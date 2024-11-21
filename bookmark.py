"""Create bookmarks.html from a list of URLs."""

import logging
import sys
import traceback

from utils import Utils

logger = logging.getLogger(__name__)


def main() -> int:
    """Create bookmarks.html from a list of URLs."""

    try:
        Utils("config.yml").write_bookmarks()
    except Exception as ex:
        logger.error("Error:", exc_info=True)

        traceback.print_exception(ex, file=sys.stderr)

        return -1

    return 0


if __name__ == "__main__":
    sys.exit(main())
