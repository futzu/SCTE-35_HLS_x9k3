"""
argue parses command line args
"""


import argparse
import sys


def argue():

    """
    argue parse command line args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        default=sys.stdin.buffer,
        help=""" Input source, like "/home/a/vid.ts"
                                or "udp://@235.35.3.5:3535"
                                or "https://futzu.com/xaa.ts"
                                """,
    )

    parser.add_argument(
        "-o",
        "--output_dir",
        default=".",
        help="""Directory for segments and index.m3u8
                ( created if it does not exist ) """,
    )

    parser.add_argument(
        "-s",
        "--sidecar_file",
        default=None,
        help="""Sidecar file of scte35 cues. each line contains  PTS, Cue""",
    )

    parser.add_argument(
        "-t",
        "--time",
        default=2,
        type=float,
        help="Segment time in seconds ( default is 2)",
    )

    parser.add_argument(
        "-T",
        "--hls_tag",
        default="x_cue",
        help="x_scte35, x_cue, x_daterange, or x_splicepoint  (default x_cue)",
    )

    parser.add_argument(
        "-w",
        "--window_size",
        default=5,
        type=int,
        help="sliding window size(default:5)",
    )

    parser.add_argument(
        "-d",
        "--delete",
        action="store_const",
        default=False,
        const=True,
        help="delete segments ( enables --live )",
    )

    parser.add_argument(
        "-l",
        "--live",
        action="store_const",
        default=False,
        const=True,
        help="Flag for a live event ( enables sliding window m3u8 )",
    )

    parser.add_argument(
        "-r",
        "--replay",
        action="store_const",
        default=False,
        const=True,
        help="Flag for replay (looping) ( enables --live and --delete )",
    )

    parser.add_argument(
        "-S",
        "--shulga",
        action="store_const",
        default=False,
        const=True,
        help="Flag to enable Shulga iframe detection mode",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_const",
        default=False,
        const=True,
        help="Show version",
    )

    parser.add_argument(
        "-p",
        "--program_date_time",
        action="store_const",
        default=False,
        const=True,
        help="Flag to add Program Date Time tags to index.m3u8 ( enables --live)",
    )

    return parser.parse_args()
