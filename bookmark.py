"""Create bookmarks.html from a list of URLs."""

import logging
import random
import sys
import time

from utils import Utils


logger = logging.getLogger(__name__)


def main() -> int:
    """Create bookmarks.html from a list of URLs."""

    logging.basicConfig(filename="bookmark.log", level=logging.DEBUG)

    utils = Utils("config.yml")

    html = [
        """
    <html>
    <head>
    <title>Bookmarks</title>
    </head>

    <body>
    <h1>Bookmarks</h1>
    <ul>
    """
    ]

    urls_file = utils.get_config("urls_file", "urls.txt")

    logging.debug("Opening '%s'", urls_file)

    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f.readlines()]

        f.close()

    logging.debug("urls = %s", urls)

    for url in urls:
        logger.debug("Retrieving title for '%s'.", url)

        encoded = utils.get_title(url)

        logger.debug("encoded = %s", encoded)

        html.append(f"<li><a href='{encoded.url}'>{encoded.title}</a></li>")

        sleep_duration = int(utils.get_config("sleep", 0))

        if sleep_duration > 0:
            if utils.get_config("random_sleep", True):
                time.sleep((sleep_duration / 1000) * random.random())

    html.append(
        """
    </ul>
    </body>
    </html>
    """
    )

    bookmarks_file = utils.get_config("bookmarks_html_file", "bookmarks.html")

    logging.debug("Writing '%s'", urls_file)

    with open(bookmarks_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

        f.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
