"""Create bookmarks.html from a list of URLs."""

import sys

from utils import Utils


def main() -> int:
    """Create bookmarks.html from a list of URLs."""

    utils = Utils("config.yml")

    urls = utils.get_urls()

    utils.write_bookmarks([utils.get_bookmark_info(url).html() for url in urls])

    return 0


if __name__ == "__main__":
    sys.exit(main())
