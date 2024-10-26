"""Utility class for creating bookmarks.html from a list of URLs."""

import html
import logging
import random
import time
import urllib

import requests
import yaml

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class BookmarkInfo:
    """Information about a bookmark."""

    url = None
    title = None
    content = None
    favicon = None

    def __init__(self, url: str, content: str):
        self.url = url
        self.content = content

    def __str__(self):
        return f"url = {self.url}; title = {self.title}"

    def html(self) -> str:
        """Return HTML representation of bookmark."""

        # TODO: Include favicon.

        return f'<DT><A HREF="{self.url}">{self.title}</A>'

    def encode(self):
        """Encode URL and title."""

        # TODO: Encode favicon.

        self.url = urllib.parse.quote(self.url)
        self.title = html.escape(self.title)


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

    def __init__(self, config_file):
        self.config = Config(config_file)

        logging.basicConfig(
            filename=self.config.get("log_file", "bookmark.log"),
            level=self.config.get("log_level", logging.DEBUG),
        )

        logger.debug("config = %s", self.config)

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

    def write_bookmarks(self, bookmarks: list[any]):
        """Write list to bookmarks HTML file."""

        bookmarks_file = self.config.get("bookmarks_html_file", "bookmarks.html")

        logging.debug("Writing '%s'", bookmarks_file)

        with open(bookmarks_file, "w", encoding="utf-8") as f:
            f.write(self.config.get("html_front_matter"))

            f.writelines(bookmarks)

            f.write(self.config.get("html_end_matter"))

            f.close()

    def get_html(self, url: str) -> BookmarkInfo:
        """Get HTML for a given URL."""

        with requests.Session() as s:
            response = s.get(
                url,
                headers=self.default_headers,
                timeout=self.request_timeout,
            )

            logger.debug("response = %s", response.headers)

            # update response URL if redirected
            if url != response.url and self.rewrite_url:
                logger.debug("Rewriting URL from '%s' to '%s'.", url, response.url)

                url = response.url

            response.raise_for_status()

        return BookmarkInfo(url, response.content)

    def get_bookmark_info(self, url: str) -> BookmarkInfo:
        """Get bookmark details from HTML."""

        logger.debug("Retrieving title for '%s'.", url)

        html_response = None

        try:
            html_response = self.get_html(url)

            soup = BeautifulSoup(html_response.content, "html.parser")

            title = soup.select_one("title")

            if title is not None:
                title = title.string.strip()

                logger.debug("title = %s", title)
            else:
                title = url

            # TODO: Get favicon.
        except (requests.exceptions.ReadTimeout, requests.exceptions.HTTPError) as ex:
            logger.error("Error retrieving HTML: %s", ex)

            if html_response is None:
                html_response = BookmarkInfo(url, "")

            title = url
        except ImportError as ex:
            logger.error("Error parsing HTML: %s", ex)

            if html_response is None:
                html_response = BookmarkInfo(url, "")

            title = url

        html_response.title = title

        self.sleep()

        html_response.encode()

        return html_response

    def sleep(self):
        """Sleep for configured number of milliseconds."""

        if self.sleep_duration > 0:
            if self.random_sleep:
                sleep_multiplier = random.random()
            else:
                sleep_multiplier = float(1)

            time.sleep((self.sleep_duration / 1000) * sleep_multiplier)
