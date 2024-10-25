"""Utility class for creating bookmarks.html from a list of URLs."""

import logging
import random
import time

import requests
import yaml

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class HtmlResponse:
    """Response from get_title()."""

    url = None
    title = None
    content = None

    def __init__(self, url: str, content: str):
        self.url = url
        self.content = content

    def __str__(self):
        return f"url = {self.url}; title = {self.title}"

    def encode(self):
        """Encode URL and title."""

        # TODO: URL encode url
        # TODO: HTML encode title

        pass


class Utils:
    """Utility methods for creating bookmarks HTML."""

    config = None
    sleep_duration = 0
    random_sleep = True
    default_headers = None
    request_timeout = 60
    rewrite_url = True

    def __init__(self, config_file):
        logger.debug("Opening %s", config_file)

        with open(config_file, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        logger.debug("config = %s", self.config)

        self.sleep_duration = int(self.get_config("sleep", 0))
        self.random_sleep = bool(self.get_config("random_sleep", True))

        self.default_headers = {
            h["name"]: h["value"] for h in self.get_config("headers")
        }

        self.request_timeout = int(self.get_config("timeout", 60))

        self.rewrite_url = bool(self.get_config("rewrite_url", True))

    def get_config(self, key: str, default: any = "") -> any:
        """Get configuration value for key."""

        if self.config is not None:
            value = self.config[key]

        if value is None:
            value = default

        return value

    def get_urls(self) -> list[str]:
        """Get list of URLs from file."""

        urls_file = self.get_config("urls_file", "urls.txt")

        logging.debug("Opening '%s'", urls_file)

        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f.readlines()]

            f.close()

        return urls

    def write_bookmarks(self, content: str):
        """Write list to bookmarks HTML file."""

        bookmarks_file = self.get_config("bookmarks_html_file", "bookmarks.html")

        logging.debug("Writing '%s'", bookmarks_file)

        with open(bookmarks_file, "w", encoding="utf-8") as f:
            f.write(content)

            f.close()

    def get_html(self, url: str) -> HtmlResponse:
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

        return HtmlResponse(url, response.content)

    def get_title(self, url: str) -> HtmlResponse:
        """Get title element from HTML."""

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
        except (requests.exceptions.ReadTimeout, requests.exceptions.HTTPError) as ex:
            logger.error("Error retrieving HTML: %s", ex)

            if html_response is None:
                html_response = HtmlResponse(url, "")

            title = url
        except ImportError as ex:
            logger.error("Error parsing HTML: %s", ex)

            if html_response is None:
                html_response = HtmlResponse(url, "")

            title = url

        html_response.title = title

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
