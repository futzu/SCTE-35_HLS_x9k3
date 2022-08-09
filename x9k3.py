#!/usr/bin/env python3

"""
X9K3
"""

import argparse
import io
import os
import sys
import time
from base64 import b64encode
from collections import deque
from new_reader import reader
from threefive import Stream, Cue

MAJOR = "0"
MINOR = "1"
MAINTAINENCE = "15"


def version():
    """
    version prints threefives version as a string

    Odd number versions are releases.
    Even number versions are testing builds between releases.

    Used to set version in setup.py
    and as an easy way to check which
    version you have installed.

    """
    return f"{MAJOR}.{MINOR}.{MAINTAINENCE}"


def version_number():
    """
    version_number returns version as an int.
    if version() returns 2.3.01
    version_number will return 2301
    """
    return int(f"{MAJOR}{MINOR}{MAINTAINENCE}")


class SegData:
    """
    A SegData instance is used to keep hold
    segment data by X9K3.
    """

    def __init__(self):
        self.start_seg_num = 0
        self.seg_num = 0
        self.seg_start = None
        self.seg_stop = None
        self.seg_time = None
        self.init_time = time.time()
        self.seg_uri = None
        self.diff_total = 0


class SCTE35:
    """
    A SCTE35 instance is used to hold
    SCTE35 cue data by X9K3.
    """

    def __init__(self):
        self.cue = None
        self.cue_out = None
        self.cue_tag = None
        self.cue_time = None

    @staticmethod
    def mk_cue_tag(cue):
        """
        mk_cue_tag
        """
        return f'#EXT-X-SCTE35:CUE="{b64encode(cue.bites).decode()}"'

    @staticmethod
    def is_cue_out(cue):
        """
        is_cue_out checks a Cue instance
        to see if it is a cue_out event.
        Returns True for a cue_out event.
        """
        if cue.command.command_type == 5:
            if cue.command.out_of_network_indicator:
                return True
        return False

    @staticmethod
    def is_cue_in(cue):
        """
        is_cue_in checks a Cue instance
        to see if it is a cue_in event.
        Returns True for a cue_in event.
        """
        if cue.command.command_type == 5:
            if not cue.command.out_of_network_indicator:
                return True
        return False

    def cue_out_cue_in(self):
        """
        cue_out_cue_in adds CUE-OUT
        and CUE-IN attributes to hls scte35 tags
        """
        if self.is_cue_out(self.cue):
            self.cue_tag += ",CUE-OUT=YES"
            self.cue_out = "CONT"
        if self.is_cue_in(self.cue):
            self.cue_tag += ",CUE-IN=YES"
            self.cue_out = None


class X9K3(Stream):
    """
    X9K3 class
    """

    # sliding window size
    WINDOW_SLOTS = 5
    # target segment time.
    SECONDS = 2

    def __init__(self, tsdata=None, show_null=False):
        """
        __init__ for X9K3
        tsdata is an file or http/https url or multicast url
        set show_null=False to exclude Splice Nulls
        """
        super().__init__(tsdata, show_null)
        self.active_segment = io.BytesIO()
        self.active_data = io.StringIO()
        self.start = False
        self.scte35 = SCTE35()
        self.window = []
        self.window_slot = 0
        self.header = None
        self.live = False
        self.output_dir = "."
        self.delete = False
        self.seg = SegData()
        self.sidecar = None
        self._parse_args()

    def _parse_args(self):
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
            "-o",
            "--output_dir",
            default=".",
            help="""Directory for segments and index.m3u8
                    ( created if it does not exist ) """,
        )

        parser.add_argument(
            "-s",
            "--sidecar",
            default=None,
            help="""sidecar file of scte35 cues. each line contains  (PTS, CueString)
                        Example:  89718.451333, /DARAAAAAAAAAP/wAAAAAHpPv/8=""",
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
            "-d",
            "--delete",
            action="store_const",
            default=False,
            const=True,
            help="delete segments ( enables live mode )",
        )

        args = parser.parse_args()
        self._apply_args(args)


    def _apply_args(self,args):
        """
        _apply_args  uses command line args
        to set X9K3 instance vars
        """
        if args.input:
            self._tsdata = args.input
        else:
            self._tsdata = sys.stdin.buffer

        self.output_dir = args.output_dir
        if not os.path.isdir(args.output_dir):
            os.mkdir(args.output_dir)

        self.live = args.live

        self.delete = args.delete
        if args.delete:
            self.live = True

        if args.sidecar:
            self.load_sidecar(args.sidecar)
        if isinstance(self._tsdata, str):
            self._tsdata = reader(self._tsdata)

    @staticmethod
    def mk_uri(head, tail):
        """
        mk_uri is used to create local filepaths
        and resolve backslash or forwardslash seperators
        """
        sep = "/"
        if len(head.split("\\")) > len(head.split("/")):
            sep = "\\"
        if not head.endswith(sep):
            head = head + sep
        return f"{head}{tail}"

    def _mk_header(self):
        """
        header generates the m3u8 header lines
        """
        m3u = "#EXTM3U"
        m3u_version = "#EXT-X-VERSION:3"
        m3u_cache = "#EXT-X-ALLOW-CACHE:YES"
        headers = [m3u, m3u_version, m3u_cache]
        if not self.live:
            play_type = "#EXT-X-PLAYLIST-TYPE:VOD"
            headers.append(play_type)
        target = f"#EXT-X-TARGETDURATION:{self.SECONDS+self.SECONDS}"
        headers.append(target)
        seq = f"#EXT-X-MEDIA-SEQUENCE:{self.seg.start_seg_num}"
        headers.append(seq)
        bumper = ""
        headers.append(bumper)
        self.header = "\n".join(headers)

    def load_sidecar(self, file):
        """
        load_sidecar reads (pts, cue) pairs from
        the sidecar file and loads them into X9K3.sidecar
        """
        self.sidecar = deque()
        with reader(file) as sidefile:
            for line in sidefile:
                line = line.decode().strip().split("#",1)[0]
                if len(line):
                    pts, cue = line.split(",", 1)
                    self.sidecar.append([float(pts), cue])

    def chk_sidecar_cues(self, pid):
        """
        chk_sidecar_cues checks the insert pts time
        for the next sidecar cue and inserts the cue if needed.
        """
        if self.sidecar:
            if self.sidecar[0][0] < self.pid2pts(pid):
                raw = self.sidecar.popleft()[1]
                self.scte35.cue = Cue(raw)
                self.scte35.cue.decode()
                self._chk_cue(pid)

    def chk_stream_cues(self, pkt, pid):
        """
        chk_stream_cues checks scte35 packets
        and inserts the cue.
        """
        self.scte35.cue = self._parse_scte35(pkt, pid)
        if self.scte35.cue:
            self._chk_cue(pid)

    def _chk_cue(self, pid):
        """
        _chk_cue checks for SCTE-35 cues
        and inserts a tag at the time
        the cue is received.
        """
        self.scte35.cue.show()
        print(f"{self.scte35.cue.command.name}")
        self.active_data.write(f"# {self.scte35.cue.command.name} @ {self.scte35.cue.command.pts_time}\n")
        if "pts_time" in self.scte35.cue.command.get():
            self.scte35.cue_time = self.scte35.cue.command.pts_time
            print(
                f"Preroll: {round(self.scte35.cue.command.pts_time- self.pid2pts(pid), 6)} "
            )
        else:
            self.scte35.cue_time = self.pid2pts(pid)
            self.active_data.write("# Splice Immediate\n")
        self.scte35.cue_tag = self.scte35.mk_cue_tag(self.scte35.cue)
        self.scte35.cue_out = None

    def _mk_cue_splice_point(self):
        """
        _mk_cue_splice_point inserts a tag
        at the time specified in the cue.
        """
        self.scte35.cue_tag = self.scte35.mk_cue_tag(self.scte35.cue)
        print(f"Splice Point {self.scte35.cue.command.name}@{self.scte35.cue_time}")
        self.active_data.write(f"# Splice Point @ {self.scte35.cue_time}\n")
        self.scte35.cue_out_cue_in()
        if self.scte35.cue_out is None:
            self.scte35.cue_time = None
        self.active_data.write(self.scte35.cue_tag + "\n")
        self.scte35.cue_tag = None

    def cue_out_continue(self):
        """
        cue_out_continue ensures that
        if there is an active SCTE35 cue,
        the live sliding window of segments
        has a tag with CUE-OUT=CONT

        """
        if self.window_slot > self.WINDOW_SLOTS:
            self.window_slot = 0
        if self.scte35.cue_out == "CONT" and self.window_slot == 0:
            self.scte35.cue_tag = self.scte35.mk_cue_tag(self.scte35.cue)
            self.scte35.cue_tag += ",CUE-OUT=CONT"
        self.window_slot += 1

    def _mk_segment(self, pid):
        """
        _mk_segment cuts hls segments
        """
        if self.scte35.cue_time:
            if self.seg.seg_start < self.scte35.cue_time < self.seg.seg_stop:
                self.seg.seg_stop = self.scte35.cue_time
                self._mk_cue_splice_point()
                self.scte35.cue_time = None
        now = self.pid2pts(pid)
        if now >= self.seg.seg_stop:
            self.seg.seg_stop = now
            self._write_segment()
            self._write_manifest()

    def _write_segment(self):
        """
        _write_segment creates segment file,
        writes segment meta data to self.active_data
        """
        if not self.start:
            return
        seg_file = f"seg{self.seg.seg_num}.ts"
        self.seg.seg_uri = self.mk_uri(self.output_dir, seg_file)
        if self.seg.seg_stop:
            self.seg.seg_time = round(self.seg.seg_stop - self.seg.seg_start, 6)
            if self.live:
                self.cue_out_continue()
            if self.scte35.cue_tag:
                self.active_data.write(self.scte35.cue_tag + "\n")
                self.scte35.cue_tag = None
            with open(self.seg.seg_uri, "wb+") as a_seg:
                a_seg.write(self.active_segment.getbuffer())
                a_seg.flush()
            del self.active_segment
            self.active_data.write(f"#EXTINF:{self.seg.seg_time},\n")
            self.active_data.write(seg_file + "\n")
            self.seg.seg_start = self.seg.seg_stop
            self.seg.seg_stop += self.SECONDS
            self.window.append(
                (self.seg.seg_num, self.seg.seg_uri, self.active_data.getvalue())
            )
            self.seg.seg_num += 1

    def _pop_segment(self):
        if len(self.window) > self.WINDOW_SLOTS:
            if self.delete:
                drop = self.window[0][1]
                print(f"deleting {drop}")
                os.unlink(drop)
            self.window = self.window[1:]

    def _open_m3u8(self):
        m3u8_uri = self.mk_uri(self.output_dir, "index.m3u8")
        return open(m3u8_uri, "w+", encoding="utf-8")

    def _write_manifest(self):
        """
        _write_manifest writes segment meta data from
        self.window to an m3u8 file
        """
        self.stream_diff()
        if self.live:
            self._pop_segment()
            self.seg.start_seg_num = self.window[0][0]
        with self._open_m3u8() as m3u8:
            self._mk_header()
            m3u8.write(self.header)
            for i in self.window:
                m3u8.write(i[2])
            if not self.live:
                m3u8.write("#EXT-X-ENDLIST")
        self.active_data = io.StringIO()
        self.active_segment = io.BytesIO()

    def stream_diff(self):
        """
        stream diff is the difference
        between the playback time of the stream
        and generation of segments by x9k3.

        a segment with a 2 second duration that takes
        0.5 seconds to generate would have a stream diff of 1.5.

        a negative stream_diff when the stream source is read over a netowork,
        is a good indication that your network is too slow
        for the bitrate of the stream.

        In live mode, the stream_diff is used to throttle non-live
        streams so they stay in sync with the sliding window of the m3u8.
        """
        rev = "\033[7m \033[1m"
        res = "\033[00m"
        now = time.time()
        gen_time = now - self.seg.init_time
        if not self.seg.seg_time:
            self.seg.seg_time = self.SECONDS
        diff = self.seg.seg_time - gen_time
        self.seg.diff_total += diff
        furi = f"{rev}{self.seg.seg_uri}{res}"
        fstart = f"\tstart: {rev}{self.seg.seg_start- self.seg.seg_time:.6f}{res}"
        fdur = f"\tduration: {rev}{self.seg.seg_time:.6f}{res}"
        fdiff = f"\tstream diff: {rev}{round(self.seg.diff_total,6)}{res}"
        print(f"{furi}{fstart}{fdur}{fdiff}")
        self.seg.init_time = now
        if self.live:
            if self.seg.diff_total > 0:
                time.sleep(self.seg.seg_time)

    def _is_key(self, pkt):
        """
        _is_key is key frame detection.
        """

        def _rai_flag(pkt):
            """
            random access indicator
            """
            return pkt[5] & 0x40

        def _abc_flags(pkt):
            """
            0x80, 0x20, 0x8
            """
            return pkt[5] & 0xA8

        def _nal(pkt):
            """
            \x65
            """
            return b"\x00\x00\x01\x65" in pkt

        if _nal(pkt):
            return True
        if self._afc_flag(pkt):
            if _rai_flag(pkt):
                return True
            if _abc_flags(pkt):
                return True

        return False

    @staticmethod
    def _is_sps(pkt):
        """
        _is_sps parses h264 for profile and level
        """
        sps_start = b"\x00\x00\x01\x67"
        if sps_start in pkt:
            sps_idx = pkt.index(sps_start)
            profile = pkt[sps_idx + 4]
            level = pkt[sps_idx + 6]
            print(f"Profile {profile} Level {level}")

    def _parse_pts(self, pkt, pid):
        """
        parse pts from pkt and store it
        in the dict Stream._pid_pts.
        """
        payload = self._parse_payload(pkt)
        if len(payload) < 14:
            return
        if self._pts_flag(payload):
            pts = ((payload[9] >> 1) & 7) << 30
            pts |= payload[10] << 22
            pts |= (payload[11] >> 1) << 15
            pts |= payload[12] << 7
            pts |= payload[13] >> 1
            prgm = self.pid2prgm(pid)
            self._prgm_pts[prgm] = pts
            if not self.seg.seg_start:
                self.seg.seg_start = self.as_90k(pts)
                self.seg.seg_stop = self.seg.seg_start + self.SECONDS

    def _parse(self, pkt):
        """
        _parse parses mpegts and
        writes the packet to self.active_segment.
        """
        pid = self._parse_info(pkt)
        self.chk_sidecar_cues(pid)
        if pid in self._pids["scte35"]:
            self.chk_stream_cues(pkt, pid)
        # self._is_sps(pkt)
        if self._pusi_flag(pkt):
            self._parse_pts(pkt, pid)
            if self._is_key(pkt):
                self._mk_segment(pid)
                if not self.start:
                    self.start = True
        if self.start:
            self.active_segment.write(pkt)


def cli():
    """
    cli provides one function call
    for running X9K3  with command line args

      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                        Input source, like "/home/a/vid.ts" or
                        "udp://@235.35.3.5:3535" or "https://futzu.com/xaa.ts"
      -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory for segments and index.m3u8 ( created if it
                        does not exist )
      -s SIDECAR, --sidecar SIDECAR
                        sidecar file of scte35 cues. each line contains (PTS,
                        CueString) Example: 89718.451333,
                        /DARAAAAAAAAAP/wAAAAAHpPv/8=
      -l, --live            Flag for a live event ( enables sliding window m3u8 )
      -d, --delete          delete segments ( enables live mode )

    Two lines of code gives you a full X9K3 command line tool.

     from X9K3 import cli
     cli()

    """
    x9k3 = X9K3()
    x9k3.decode()



if __name__ == "__main__":
    cli()
