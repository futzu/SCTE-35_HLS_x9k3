import argparse
import sys
from reader2 import reader as r2
from x9k3 import X9K3


class EXP9K3(X9K3):
    def __init__(self, tsdata, show_null=False):
        """
        __init__ for X9K3
        tsdata is an file or http/https url or multicast url
        set show_null=False to exclude Splice Nulls
        """
        super().__init__(tsdata, show_null)
        if isinstance(tsdata, str):
            self._tsdata = r2(tsdata)
        else:
            self._tsdata = tsdata


def _parse_args():
    """
    _parse_args parse command line args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        default=None,
        help=""" Input source, like "/home/a/vid.ts"
                                or "udp://@235.35.3.5:3535"
                                or "https://futzu.com/xaa.ts"
                                """,
    )

    parser.add_argument(
        "-l",
        "--live",
        action="store_const",
        default=False,
        const=True,
        help="Flag for a live event.(enables sliding window m3u8)",
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = _parse_args()
    if len(sys.argv) > 1:
        exp9k3 = EXP9K3(args.input)
        exp9k3.live = args.live
    else:
        # for piping in video
        exp9k3 = EXP9K3(sys.stdin.buffer)
    exp9k3.decode()
