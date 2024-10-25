"""Create bookmarks.html from a list of URLs."""

import logging
import sys

from utils import Utils


logger = logging.getLogger(__name__)


def main() -> int:
    """Create bookmarks.html from a list of URLs."""

    utils = Utils("config.yml")

    logging.basicConfig(
        filename=utils.get_config("log_file", "bookmark.log"),
        level=utils.get_config("log_level", logging.DEBUG),
    )

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

    urls = utils.get_urls()

    logging.debug("urls = %s", urls)

    for url in urls:
        logger.debug("Retrieving title for '%s'.", url)

        encoded = utils.get_title(url)

        logger.debug("encoded = %s", encoded)

        html.append(f"<li><a href='{encoded.url}'>{encoded.title}</a></li>")

        utils.sleep()

    html.append(
        """
    </ul>
    </body>
    </html>
    """
    )

    utils.write_bookmarks("\n".join(html))

    return 0


if __name__ == "__main__":
    sys.exit(main())
