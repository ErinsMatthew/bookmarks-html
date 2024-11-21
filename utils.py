"""Utility class for creating bookmarks.html from a list of URLs."""

import base64
import logging
import mimetypes
import random
import time

import requests
import yaml

from bs4 import BeautifulSoup

from dominate import document
from dominate.util import raw
from dominate.tags import a, dt, dl, p, h1, h3, meta


logger = logging.getLogger(__name__)

current_time_seconds = int(time.time())

BOOKMARKS_KEY = "bookmarks"
FOLDERS_KEY = "folders"


class BookmarkInfo:
    """Information about a bookmark."""

    url = None
    title = None
    content = None
    favicon = None
    folders = None

    def __init__(self, url: str, content: str):
        self.url = url
        self.content = content

    def __str__(self):
        return f"url = {self.url}; title = {self.title}"

    def __lt__(self, other):
        return self.folders < other.folders and self.url < other.url

    def __le__(self, other):
        return self.folders <= other.folders and self.url <= other.url

    def __eq__(self, other):
        return self.folders == other.folders and self.url == other.url

    def __ne__(self, other):
        return self.folders != other.folders and self.url != other.url

    def __gt__(self, other):
        return self.folders > other.folders and self.url > other.url

    def __ge__(self, other):
        return self.folders >= other.folders and self.url >= other.url

    def html(self):
        """Return HTML representation of bookmark."""

        _dt = dt()
        _a = a(
            self.title,
            href=self.url,
            ADD_DATE=current_time_seconds,
            LAST_MODIFIED=current_time_seconds,
        )

        if self.favicon is not None:
            _a["icon"] = self.favicon

        _dt.add(_a)

        return _dt


class Config:
    """Manage configuration."""

    _values = None

    def __init__(self, file):
        with open(file, "r", encoding="utf-8") as f:
            self._values = yaml.safe_load(f)

            f.close()

    def get(self, key: str, default: any = "") -> any:
        """Get configuration value for key."""

        value = None

        if self._values is not None:
            value = self._values[key]

        if value is None:
            value = default

        return value


class Utils:
    """Utility methods for creating bookmarks HTML."""

    _config = None

    _sleep_duration = 0
    random_sleep = True
    default_headers = None
    request_timeout = 60
    rewrite_url = True
    read_favicon = False
    folder_separator = None
    subfolder_separator = None

    def __init__(self, config_file):
        self._config = Config(config_file)

        logging.basicConfig(
            filename=self._config.get("log_file", "bookmark.log"),
            encoding="utf-8",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=self._config.get("log_level", logging.DEBUG),
        )

        logger.debug("config = %s", self._config)

        self.folder_separator = self._config.get("folder_separator", "|")
        self.subfolder_separator = self._config.get("subfolder_separator", ",")

        self._sleep_duration = int(self._config.get("sleep", 0))
        self.random_sleep = bool(self._config.get("random_sleep", True))

        self.default_headers = {
            header["name"]: header["value"] for header in self._config.get("headers")
        }

        self.request_timeout = int(self._config.get("timeout", 60))

        self.rewrite_url = bool(self._config.get("rewrite_url", True))

        self.read_favicon = bool(self._config.get("favicon", False))

    def _get_urls(self) -> list[str]:
        """Get list of URLs from file."""

        urls_file = self._config.get("urls_file", "urls.txt")

        logger.debug("Opening '%s'", urls_file)

        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f.readlines()]

            f.close()

        logger.debug("urls = %s", urls)

        return urls

    def _build_bookmarks_dict(self) -> dict:
        """Create nested dictionary of bookmarks by folder.

        {
          "bookmarks": [],
          "folders": {
            "Folder1": {
              "bookmarks": [],
              "folders": {
                ...
              }
            }
          }
        }
        """

        bookmarks_dict = {BOOKMARKS_KEY: [], FOLDERS_KEY: {}}

        bookmarks = self._get_bookmarks_list()

        for bookmark_info in bookmarks:
            folders = bookmark_info.folders

            logger.debug("folders = %s", folders)

            bookmarks_list = bookmarks_dict[BOOKMARKS_KEY]

            d = bookmarks_dict[FOLDERS_KEY]

            for folder in folders:
                logger.debug("folder = %s", folder)

                if folder not in d:
                    logger.debug("Creating object for folder %s", folder)

                    d[folder] = {BOOKMARKS_KEY: [], FOLDERS_KEY: {}}

                bookmarks_list = d[folder][BOOKMARKS_KEY]

                logger.debug("bookmarks_list = %s", bookmarks_list)

                d = d[folder][FOLDERS_KEY]

            bookmarks_list.append(bookmark_info)

        logger.debug("bookmarks_dict = %s", bookmarks_dict)

        return bookmarks_dict

    def _build_folder_bookmark_elements(self, folder: str, bookmarks_dict: dict):
        """Build list of bookmarks for a folder from bookmarks_dict."""

        folder_element = dt()

        folder_element.add(
            h3(
                folder,
                ADD_DATE=current_time_seconds,
                LAST_MODIFIED=current_time_seconds,
            )
        )

        _p = folder_element.add(dl()).add(p())

        # process sub-folders
        for subfolder in bookmarks_dict[FOLDERS_KEY][folder][FOLDERS_KEY]:
            _p.add(
                self._build_folder_bookmark_elements(
                    subfolder, bookmarks_dict[FOLDERS_KEY][folder]
                )
            )

        # write folder bookmarks
        for bookmark in bookmarks_dict[FOLDERS_KEY][folder][BOOKMARKS_KEY]:
            _p.add(bookmark.html())

        return folder_element

    def _build_bookmark_elements(self, parent):
        """Build list of bookmark lines to output."""

        bookmarks_dict = self._build_bookmarks_dict()

        for folder in bookmarks_dict[FOLDERS_KEY]:
            logger.debug("folder = %s", folder)

            parent.add(self._build_folder_bookmark_elements(folder, bookmarks_dict))

        for bookmark in bookmarks_dict[BOOKMARKS_KEY]:
            parent.add(bookmark.html())

        return parent

    def _get_bookmarks_list(self) -> list[BookmarkInfo]:
        """Get list of bookmarks."""

        # read list of URLs in Folder,Subfolder...|URL format
        urls = self._get_urls()

        logger.debug("Read %d URLs.", len(urls))

        bookmarks = [self._get_bookmark_info(url) for url in urls]

        if self._config.get("sort", False):
            bookmarks.sort()

        return bookmarks

    def _build_bookmarks_file(self):
        _document = document(
            title="Bookmarks", doctype="<!DOCTYPE NETSCAPE-Bookmark-file-1>"
        )

        with _document.head:
            # raw(
            #     """<!-- This is an automatically generated file.
            #             It will be read and overwritten.
            #             DO NOT EDIT! -->"""
            # )
            meta(http_equiv="Content-Type", content="text/html; charset=UTF-8")

        with _document:
            h1("Bookmarks")

            with dl().add(p()).add(dt()):
                h3(
                    "Bookmarks",
                    ADD_DATE=current_time_seconds,
                    LAST_MODIFIED=current_time_seconds,
                    PERSONAL_TOOLBAR_FOLDER="true",
                )

                _p = dl().add(p())

        self._build_bookmark_elements(_p)

        return _document.render(pretty=False)

    def write_bookmarks(self):
        """Write bookmarks to an HTML file.

        This method will convert URLs listed in a text file into a HTML format
        per the `documentation
        <https://learn.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/platform-apis/aa753582(v=vs.85)>`_.
        """

        bookmarks_file = self._config.get("bookmarks_html_file", "bookmarks.html")

        logger.debug("Writing '%s'", bookmarks_file)

        with open(bookmarks_file, "w", encoding="utf-8") as f:
            f.write(self._build_bookmarks_file())

            f.close()

    def _get_contents(self, url: str) -> requests.Response:
        """Get binary contents of file from URL."""

        with requests.Session() as s:
            response = s.get(
                url,
                headers=self.default_headers,
                timeout=self.request_timeout,
            )

            logger.debug("response = %s", response.headers)

            response.raise_for_status()

        return response

    def _get_html(self, url: str) -> BookmarkInfo:
        """Get HTML for a given URL."""

        response = self._get_contents(url)

        # update response URL if redirected
        if url != response.url and self.rewrite_url:
            logger.debug("Rewriting URL from '%s' to '%s'.", url, response.url)

            url = response.url

        return BookmarkInfo(url, response.content)

    def _determine_mime_type(self, favicon_url: str) -> str:
        """Determine MIME type from URL."""

        # try based on file name
        mime_type = mimetypes.guess_type(favicon_url)

        if len(mime_type) != 2:
            mime_type = None
        else:
            mime_type = str(mime_type[0])

        return mime_type

    def _use_this_favicon(self, icon) -> bool:
        """Determine whether to use this favicon or not."""

        # TODO: Determine if we should use this one or not.
        #
        # If there are multiple <link rel="icon">s, the browser uses their media, type,
        # and sizes attributes to select the most appropriate icon. If several icons are
        # equally appropriate, the last one is used.
        #
        # favicon_url = icon.get("href")
        # favicon_type = icon.get("type")
        # favicon_sizes = icon.get("sizes")

        return True

    def _parse_favicon_data(self, soup: BeautifulSoup) -> str:
        """Get favicon data from links in page HTML."""

        favicon_links = soup.find_all("link", rel="icon")

        logger.debug("favicon_links = %s", favicon_links)

        favicon_data = None

        if favicon_links is not None:
            for icon in favicon_links:
                if not self._use_this_favicon(icon):
                    continue

                favicon_url = icon.get("href")
                favicon_type = icon.get("type")

                if favicon_type is not None:
                    mime_type = favicon_type
                else:
                    mime_type = self._determine_mime_type(favicon_url)

                logger.debug("mime_type = %s", mime_type)

                favicon_contents = self._get_contents(favicon_url)

                if favicon_contents is not None:
                    encoded_bytes = base64.b64encode(favicon_contents.content)

                    encoded_data = encoded_bytes.decode("utf-8")

                    # data:<mime-type>;base64,<base64-encoded-data>
                    favicon_data = f"data:{mime_type};base64,{encoded_data}"

                # stop loop once we processed one; TODO: refactor this!
                break

        return favicon_data

    def _parse_title(self, soup: BeautifulSoup, url: str) -> str:
        """Parse title information from HTML."""

        title = soup.select_one("title")

        if title is not None and title.string is not None:
            title = title.string.strip()

            logger.debug("title = %s", title)
        else:
            title = url

        return str(title)

    def _get_folders(self, line: str) -> tuple[list[str], str]:
        """Parse folders and URL from line."""

        folders = []
        url = line

        # split on folder_separator
        items = line.split(self.folder_separator)

        if len(items) > 1:
            # sub-split on subfolder_separator
            folders = str(items[0]).split(self.subfolder_separator)

            url = items[1]

        logger.debug("folders('%s') = %s", url, folders)

        return folders, url

    def _get_bookmark_info(self, line: str) -> BookmarkInfo:
        """Get bookmark info from HTML."""

        logger.debug("Retrieving info for '%s'.", line)

        bookmark_info = None
        favicon_data = None

        folders, url = self._get_folders(line)

        try:
            bookmark_info = self._get_html(url)

            soup = BeautifulSoup(bookmark_info.content, "html.parser")

            title = self._parse_title(soup, url)

            if self.read_favicon:
                favicon_data = self._parse_favicon_data(soup)
        except requests.exceptions.RequestException as ex:
            logger.error("Error retrieving HTML: %s", ex)

            # use URL as title and keep going
            if bookmark_info is None:
                bookmark_info = BookmarkInfo(url, "")

            title = url
        except ImportError as ex:
            logger.error("Error parsing HTML: %s", ex)

            if bookmark_info is None:
                bookmark_info = BookmarkInfo(url, "")

            title = url

        bookmark_info.title = title
        bookmark_info.favicon = favicon_data
        bookmark_info.folders = folders

        self._sleep()

        return bookmark_info

    def _sleep(self):
        """Sleep for configured number of milliseconds."""

        if self._sleep_duration > 0:
            if self.random_sleep:
                sleep_multiplier = random.random()
            else:
                sleep_multiplier = float(1)

            time.sleep((self._sleep_duration / 1000) * sleep_multiplier)
