"""Utility class for creating bookmarks.html from a list of URLs."""

import base64
import logging
import mimetypes
import random
import time

import requests
import yaml

from bs4 import BeautifulSoup
from dominate.tags import a, dt


logger = logging.getLogger(__name__)


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

    def html(self) -> str:
        """Return HTML representation of bookmark."""

        _dt = dt()
        _a = a(self.title, href=self.url)

        if self.favicon is not None:
            _a["icon"] = self.favicon

        _dt.add(_a)

        bookmark_html = _dt.render(pretty=False)

        logger.debug("bookmark_html = %s", bookmark_html)

        return bookmark_html


class Config:
    """Manage configuration."""

    values = None

    def __init__(self, file):
        with open(file, "r", encoding="utf-8") as f:
            self.values = yaml.safe_load(f)

            f.close()

    def get(self, key: str, default: any = "") -> any:
        """Get configuration value for key."""

        value = None

        if self.values is not None:
            value = self.values[key]

        if value is None:
            value = default

        return value


class Utils:
    """Utility methods for creating bookmarks HTML."""

    config = None

    sleep_duration = 0
    random_sleep = True
    default_headers = None
    request_timeout = 60
    rewrite_url = True
    read_favicon = False
    folder_separator = None
    subfolder_separator = None

    def __init__(self, config_file):
        self.config = Config(config_file)

        logging.basicConfig(
            filename=self.config.get("log_file", "bookmark.log"),
            level=self.config.get("log_level", logging.DEBUG),
        )

        logger.debug("config = %s", self.config)

        self.folder_separator = self.config.get("folder_separator", "|")
        self.subfolder_separator = self.config.get("subfolder_separator", ",")

        self.sleep_duration = int(self.config.get("sleep", 0))
        self.random_sleep = bool(self.config.get("random_sleep", True))

        self.default_headers = {
            header["name"]: header["value"] for header in self.config.get("headers")
        }

        self.request_timeout = int(self.config.get("timeout", 60))

        self.rewrite_url = bool(self.config.get("rewrite_url", True))

        self.read_favicon = bool(self.config.get("favicon", False))

    def get_urls(self) -> list[str]:
        """Get list of URLs from file."""

        urls_file = self.config.get("urls_file", "urls.txt")

        logging.debug("Opening '%s'", urls_file)

        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f.readlines()]

            f.close()

        logging.debug("urls = %s", urls)

        return urls

    def write_bookmarks(self, bookmarks: list[BookmarkInfo]):
        """Write list to bookmarks HTML file."""

        if self.config.get("sort", False):
            bookmarks.sort()

        bookmark_lines = []

        for bookmark in bookmarks:
            # TODO: Append folder information.

            bookmark_lines.append(bookmark.html())

        bookmarks_file = self.config.get("bookmarks_html_file", "bookmarks.html")

        logging.debug("Writing '%s'", bookmarks_file)

        with open(bookmarks_file, "w", encoding="utf-8") as f:
            f.write(self.config.get("html_front_matter"))

            f.writelines(bookmark_lines)

            f.write(self.config.get("html_end_matter"))

            f.close()

    def get_contents(self, url: str) -> requests.Response:
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

    def get_html(self, url: str) -> BookmarkInfo:
        """Get HTML for a given URL."""

        response = self.get_contents(url)

        # update response URL if redirected
        if url != response.url and self.rewrite_url:
            logger.debug("Rewriting URL from '%s' to '%s'.", url, response.url)

            url = response.url

        return BookmarkInfo(url, response.content)

    def determine_mime_type(self, favicon_url: str) -> str:
        """Determine MIME type from URL."""

        # try based on file name
        mime_type = mimetypes.guess_type(favicon_url)

        if len(mime_type) != 2:
            mime_type = None
        else:
            mime_type = str(mime_type[0])

        return mime_type

    def use_this_favicon(self, icon) -> bool:
        """Determine whether to use this favicon or not."""

        # TODO: Determine if we should use this one or not.
        # If there are multiple <link rel="icon">s, the browser uses their media, type, and sizes attributes to select the most appropriate icon. If several icons are equally appropriate, the last one is used.
        # favicon_url = icon.get("href")
        # favicon_type = icon.get("type")
        # favicon_sizes = icon.get("sizes")

        return True

    def parse_favicon_data(self, soup: BeautifulSoup) -> str:
        """Get favicon data from links in page HTML."""

        favicon_links = soup.find_all("link", rel="icon")

        logger.debug("favicon_links = %s", favicon_links)

        favicon_data = None

        if favicon_links is not None:
            for icon in favicon_links:
                if not self.use_this_favicon(icon):
                    continue

                favicon_url = icon.get("href")
                favicon_type = icon.get("type")

                if favicon_type is not None:
                    mime_type = favicon_type
                else:
                    mime_type = self.determine_mime_type(favicon_url)

                logger.debug("mime_type = %s", mime_type)

                favicon_contents = self.get_contents(favicon_url)

                if favicon_contents is not None:
                    encoded_bytes = base64.b64encode(favicon_contents.content)

                    encoded_data = encoded_bytes.decode("utf-8")

                    # data:<mime-type>;base64,<base64-encoded-data>
                    favicon_data = f"data:{mime_type};base64,{encoded_data}"

                # stop loop once we processed one; refactor this!
                break

        return favicon_data

    def parse_title(self, soup: BeautifulSoup, url: str) -> str:
        """Parse title information from HTML."""

        title = soup.select_one("title")

        if title is not None:
            title = title.string.strip()

            logger.debug("title = %s", title)
        else:
            title = url

        return str(title)

    def get_folders(self, line: str) -> tuple[list[str], str]:
        """Parse folders and URL from line."""

        folders = []
        url = line

        # split on folder_separator
        items = line.split(self.folder_separator)

        if len(items) > 1:
            # sub-split on subfolder_separator
            folders = str(items[0]).split(self.subfolder_separator)

            url = items[1]

        return folders, url

    def get_bookmark_info(self, line: str) -> BookmarkInfo:
        """Get bookmark info from HTML."""

        logger.debug("Retrieving info for '%s'.", line)

        bookmark_info = None
        favicon_data = None

        folders, url = self.get_folders(line)

        try:
            bookmark_info = self.get_html(url)

            soup = BeautifulSoup(bookmark_info.content, "html.parser")

            title = self.parse_title(soup, url)

            if self.read_favicon:
                favicon_data = self.parse_favicon_data(soup)
        except (requests.exceptions.ReadTimeout, requests.exceptions.HTTPError) as ex:
            logger.error("Error retrieving HTML: %s", ex)

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

        self.sleep()

        return bookmark_info

    def sleep(self):
        """Sleep for configured number of milliseconds."""

        if self.sleep_duration > 0:
            if self.random_sleep:
                sleep_multiplier = random.random()
            else:
                sleep_multiplier = float(1)

            time.sleep((self.sleep_duration / 1000) * sleep_multiplier)
