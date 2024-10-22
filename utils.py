"""Utility class for creating bookmarks.html from a list of URLs."""

import logging

import requests
import yaml

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class HtmlResponse:
    """Response from get_title()."""

    content = None
    url = None
    title = None

    def __init__(self, url: str, content: str):
        self.url = url
        self.content = content

    def encode(self):
        """Encode URL and title."""

        # TODO: URL encode url
        # TODO: HTML encode title

        pass


class Utils:
    """Read configuration from YAML."""

    config = None

    def __init__(self, config_file):
        logger.debug("Opening %s", config_file)

        with open(config_file, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        logger.debug("config = %s", self.config)

    def get_config(self, key: str, default: str = "") -> any:
        """Get configuration value for key."""

        if self.config is not None:
            value = self.config[key]

        if value is None:
            value = default

        return value

    def get_html(self, url: str) -> HtmlResponse:
        """Get HTML for a given URL."""

        headers = {h["name"]: h["value"] for h in self.get_config("headers")}

        response = requests.get(url, headers=headers, timeout=60)

        logger.debug("response = %s", response.headers)

        # update URL if redirected
        if url != response.url and self.get_config("rewrite_url", True):
            logger.debug("Rewriting URL from '%s' to '%s'.", url, response.url)

            url = response.url

        response.raise_for_status()

        return HtmlResponse(url, response.content)

    def get_title(self, url: str) -> HtmlResponse:
        """Get title element from HTML."""

        try:
            html_response = self.get_html(url)

            soup = BeautifulSoup(html_response.content, "html.parser")

            title = soup.select_one("title")

            if title is not None:
                title = title.string.strip()

                logger.debug("title = %s", title)
            else:
                title = url
        except Exception:
            title = url

        html_response.title = title

        html_response.encode()

        return html_response
