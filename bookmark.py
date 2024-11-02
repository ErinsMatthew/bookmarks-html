"""Create bookmarks.html from a list of URLs."""

import logging
import sys

from utils import Utils

logger = logging.getLogger(__name__)


def main() -> int:
    """Create bookmarks.html from a list of URLs."""

    try:
        utils = Utils("config.yml")

        # read list of URLs in Folder,Subfolder...|URL format
        lines = utils.get_urls()

        utils.write_bookmarks([utils.get_bookmark_info(line) for line in lines])
    except Exception as ex:
        logger.error("Error Somewhere: %s", ex)

        sys.stderr.write(f"Error Somewhere: {ex}\n")

        return -1

    return 0


if __name__ == "__main__":
    sys.exit(main())
