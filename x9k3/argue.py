
def argue():
    """
    argue parse command line args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        default=sys.stdin.buffer,
        help=""" The Input video  can be mpegts or m3u8 with mpegts segments,
                        or a playlist with mpegts files and/or mpegts m3u8 files.
                    The input can be a local video, http(s), udp, multicast or stdin.
            """,
    )
    parser.add_argument(
        "-s",
        "--sidecar_file",
        default=None,
        help=f"Sidecar file of SCTE-35 (pts,cue) pairs   [default:{ON}None{OFF}]",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        default=".",
        help=f" output directory f(created if needed)   [default:{ON}'.'{OFF}]",
    )
    parser.add_argument(
        "-t",
        "--time",
        default=2,
        type=float,
        help=f"segment time in seconds   [default:{ON}2{OFF}]",
    )
    parser.add_argument(
        "-T",
        "--hls_tag",
        default="x_cue",
        help=f"x_scte35, x_cue, x_daterange, or x_splicepoint   [default:{ON}x_cue{OFF}]",
    )
    parser.add_argument(
        "-w",
        "--window_size",
        default=5,
        type=int,
        help=f"sliding window size   [default:{ON}5{OFF}]",
    )
    parser.add_argument(
        "-l",
        "--live",
        action="store_const",
        default=False,
        const=True,
        help=f"enable sliding window   [default:{ON}False{OFF}]",
    )
    parser.add_argument(
        "-I",
        "--iframe",
        action="store_const",
        default=False,
        const=True,
        help=f" iframe only hls   [default:{ON}False{OFF}]",
    )
    parser.add_argument(
        "-b",
        "--byterange",
        action="store_const",
        default=False,
        const=True,
        help=f"byterange hls   [default:{ON}False{OFF}]",
    )
    parser.add_argument(
        "-c",
        "--continue_m3u8",
        action="store_const",
        default=False,
        const=True,
        help=f"resume an index.m3u8   [default:{ON}False{OFF}]",
    )
    parser.add_argument(
        "-d",
        "--delete",
        action="store_const",
        default=False,
        const=True,
        help=f"delete segments  [default:{ON}False{OFF}]",
    )
    parser.add_argument(
        "-N",
        "--no-throttle",
        action="store_const",
        default=False,
        const=True,
        help=f"disable live throttling   [default:{ON}False{OFF}]",
    )

    parser.add_argument(
        "-p",
        "--program_date_time",
        action="store_const",
        default=False,
        const=True,
        help=f"Date Time tags    [default:{ON}False{OFF}]",
    )
    parser.add_argument(
        "-r",
        "--replay",
        action="store_const",
        default=False,
        const=True,
        help=f"replay aka looping   [default:{ON}False]{OFF}",
    )

    parser.add_argument(
        "-S",
        "--shulga",
        action="store_const",
        default=False,
        const=True,
        help=f"Shulga iframe detection    [default:{ON}False{OFF}]",
    )
    parser.add_argument(
        "-n",
        "--no_discontinuity",
        action="store_const",
        default=False,
        const=True,
        help=f"disable #EXT-X-DISCONTINUITY tags on ad breaks   [default:{ON}False{OFF}]",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_const",
        default=False,
        const=True,
        help="Show version",
    )
    return parser.parse_args()

