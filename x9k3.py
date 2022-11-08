#!/usr/bin/env python3

"""
X9K3 is an HLS Segmenter.
"""

import argparse
import datetime
import io
import os
import sys
import time
from collections import deque
from functools import partial
from operator import itemgetter
from new_reader import reader
from threefive import Stream, Cue
from iframes import IFramer

MAJOR = "0"
MINOR = "1"
MAINTAINENCE = "63"


def version():
    """
    version prints x9k3's version as a string

    Odd number versions are releases.
    Even number versions are testing builds between releases.

    Used to set version in setup.py
    and as an easy way to check which
    version you have installed.

    """
    return f"{MAJOR}.{MINOR}.{MAINTAINENCE}"


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
        self.cue_time = None
        self.tag_method = self.x_scte35
        self.break_timer = None
        self.break_duration = None
        self.break_auto_return = False
        self.event_id = 1

    def mk_cue_tag(self):
        """
        mk_cue_tag
        """
        if self.cue:
            return self.tag_method()
        return False

    def x_cue(self):
        """
        #EXT-X-CUE-( OUT | IN | CONT )
        """
        if self.cue_out == "OUT":
            self.break_timer = 0
            return f"#EXT-X-CUE-OUT:{self.break_duration}"
        if self.cue_out == "IN":
            return "#EXT-X-CUE-IN"
        if self.cue_out == "CONT":
            return f"#EXT-X-CUE-OUT-CONT:{self.break_timer:.3f}/{self.break_duration}"
        return False

    def x_splicepoint(self):
        """
        #EXT-X-SPLICEPOINT-SCTE35
        """
        base = f"#EXT-X-SPLICEPOINT-SCTE35:{self.cue.encode()}"
        if self.cue_out == "OUT":
            return f"{base}"
        if self.cue_out == "IN":
            return f"{base}"
        return False

    def x_scte35(self):
        """
        #EXT-X-SCTE35
        """
        base = f'#EXT-X-SCTE35:CUE="{self.cue.encode()}" '
        if self.cue_out == "OUT":
            return f"{base},CUE-OUT=YES "
        if self.cue_out == "IN":
            return f"{base},CUE-IN=YES "
        if self.cue_out == "CONT":
            return f"{base},CUE-OUT=CONT"
        return False

    def x_daterange(self):
        """
        #EXT-X-DATERANGE
        """
        fbase = f'#EXT-X-DATERANGE:ID="{self.event_id}"'
        iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
        fdur = ""
        if self.break_duration:
            fdur = f",PLANNED-DURATION={self.break_duration}"

        if self.cue_out == "OUT":
            self.break_timer = 0
            fstart = f',START-DATE="{iso8601}"'
            tag = f"{fbase}{fstart}{fdur},SCTE35-OUT={self.cue.encode_as_hex()}"
            self.event_id += 1
            return tag

        if self.cue_out == "IN":
            fstop = f',END-DATE="{iso8601}"'
            tag = f"{fbase}{fstop},SCTE35-IN={self.cue.encode_as_hex()}"
            self.event_id += 1
            return tag

        return False

    def is_cue_out(self, cue):
        """
        is_cue_out checks a Cue instance
        to see if it is a cue_out event.
        Returns True for a cue_out event.
        """
        cmd = cue.command
        if cmd.command_type == 5:
            if cmd.out_of_network_indicator:
                if cmd.break_duration:
                    self.break_duration = cmd.break_duration
                    self.break_timer = 0
                    return True

        upid_starts = [
            0x10,
            0x20,
            0x22,
            0x30,
            0x32,
            0x34,
            0x36,
            0x38,
            0x3A,
            0x3C,
            0x3E,
            0x44,
            0x46,
        ]
        if cmd.command_type == 6:
            for dsptr in cue.descriptors:
                if dsptr.tag == 2:
                    if dsptr.segmentation_type_id in upid_starts:
                        if dsptr.segmentation_duration:
                            self.break_duration = dsptr.segmentation_duration
                            self.break_timer = 0
                            return True

        return False

    def is_cue_in(self, cue):
        """
        is_cue_in checks a Cue instance
        to see if it is a cue_in event.
        Returns True for a cue_in event.
        """
        cmd = cue.command
        if cmd.command_type == 5:
            if not cmd.out_of_network_indicator:
                if self.break_timer >= self.break_duration:
                    return True

        upid_stops = [
            0x11,
            0x21,
            0x21,
            0x23,
            0x33,
            0x35,
            0x37,
            0x39,
            0x3B,
            0x3D,
            0x3F,
            0x45,
            0x47,
        ]
        if cmd.command_type == 6:
            for dsptr in cue.descriptors:
                if dsptr.tag == 2:
                    if dsptr.segmentation_type_id in upid_stops:
                        if self.break_timer >= self.break_duration:
                            return True

        return False


class X9K3(Stream):
    """
    X9K3 class
    """

    def __init__(self, tsdata=None, show_null=False):
        """
        __init__ for X9K3
        tsdata is an file or http/https url or multicast url
        set show_null=False to exclude Splice Nulls
        """
        self.in_stream = None

        super().__init__(tsdata, show_null)
        self._tsdata = tsdata
        self.in_stream = tsdata
        self.active_segment = io.BytesIO()
        self.active_data = io.StringIO()
        self.scte35 = SCTE35()
        self.seg = SegData()
        self.iframer = IFramer(shush=True)
        self.window = []
        self.window_size = 5
        self.window_slot = 0
        self.seconds = 2
        self.discontinuity_sequence = 0
        self.header = None
        self.sidecar_file = None
        self.sidecar = None
        self.output_dir = "."
        self.start = False
        self.live = False
        self.replay = False
        self.program_date_time_flag = False
        self.delete = False

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

        args = parser.parse_args()
        self._apply_args(args)

    @staticmethod
    def _args_version(args):
        if args.version:
            print(version())
            sys.exit()

    def _args_input(self, args):
        if args.input:
            self._tsdata = args.input
            self.in_stream = args.input
        else:
            self._tsdata = sys.stdin.buffer

    def _args_hls_tag(self, args):
        tag_map = {
            "x_scte35": self.scte35.x_scte35,
            "x_cue": self.scte35.x_cue,
            "x_daterange": self.scte35.x_daterange,
            "x_splicepoint": self.scte35.x_splicepoint,
        }
        if args.hls_tag not in tag_map:
            raise ValueError(f"hls tag  must be in {tag_map.keys()}")
        self.scte35.tag_method = tag_map[args.hls_tag]

    def _args_output_dir(self, args):
        self.output_dir = args.output_dir
        if not os.path.isdir(args.output_dir):
            os.mkdir(args.output_dir)

    def _args_flags(self, args):
        if args.live or args.delete or args.replay:
            self.live = True
            if args.delete or args.replay:
                self.delete = True
                if args.replay:
                    self.replay = True

    def _args_sidecar(self, args):
        if args.sidecar:
            self.sidecar = deque()
            self.sidecar_file = args.sidecar

    def _args_time(self, args):
        self.seconds = args.time

    def _args_window_size(self, args):
        self.window_size = args.window_size

    def _args_program_date_time(self, args):
        self.program_date_time_flag = args.program_date_time
        if self.program_date_time_flag:
            self.live = True

    def _apply_args(self, args):
        """
        _apply_args  uses command line args
        to set X9K3 instance vars
        """
        self._args_version(args)
        self._args_program_date_time(args)
        self._args_input(args)
        self._args_hls_tag(args)
        self._args_output_dir(args)
        self._args_sidecar(args)
        self._args_time(args)
        self._args_window_size(args)
        self._args_flags(args)
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
        target = f"#EXT-X-TARGETDURATION:{int(self.seconds+1)}"
        seq = f"#EXT-X-MEDIA-SEQUENCE:{self.seg.start_seg_num}"
        dseq = f"#EXT-X-DISCONTINUITY-SEQUENCE:{self.discontinuity_sequence}"
        x9k3v = f"#EXT-X-X9K3-VERSION:{version()}"
        bumper = ""
        self.header = "\n".join(
            [
                m3u,
                m3u_version,
                target,
                seq,
                dseq,
                x9k3v,
                bumper,
            ]
        )

    def load_sidecar(self, file, pid):
        """
        load_sidecar reads (pts, cue) pairs from
        the sidecar file and loads them into X9K3.sidecar
        if live, blank out the sidecar file after cues are loaded.
        """
        if self.sidecar_file:
            with reader(file) as sidefile:
                for line in sidefile:
                    line = line.decode().strip().split("#", 1)[0]
                    if len(line):
                        pts, cue = line.split(",", 1)
                        pts = float(pts)
                        if pts >= self.pid2pts(pid):
                            if [pts, cue] not in self.sidecar:
                                print("loading", pts, cue)
                                self.sidecar.append([pts, cue])
                                self.sidecar = deque(
                                    sorted(self.sidecar, key=itemgetter(0))
                                )
                sidefile.close()
            if self.live:
                with open(self.sidecar_file, "w") as scf:
                    scf.close()

    def chk_sidecar_cues(self, pid):
        """
        chk_sidecar_cues checks the insert pts time
        for the next sidecar cue and inserts the cue if needed.
        """
        if self.sidecar:
            if self.sidecar[0][0] <= self.pid2pts(pid):
                raw = self.sidecar.popleft()[1]
                self.scte35.cue = Cue(raw)
                self.scte35.cue.decode()
                self._chk_cue(pid)

    def chk_stream_cues(self, pkt, pid):
        """
        chk_stream_cues checks scte35 packets
        and inserts the cue.
        """
        cue = self._parse_scte35(pkt, pid)
        if cue:
            self.scte35.cue = cue
            self._chk_cue(pid)

    def _add_discontinuity(self):
        self.active_data.write("#EXT-X-DISCONTINUITY\n")

    def _chk_cue(self, pid):
        """
        _chk_cue checks for SCTE-35 cues
        and inserts a tag at the time
        the cue is received.
        """
        self.scte35.cue.show()
        print(f"{self.scte35.cue.command.name}")
        if "pts_time" in self.scte35.cue.command.get():
            self.scte35.cue_time = self.scte35.cue.command.pts_time
            print(
                f"Preroll: {round(self.scte35.cue.command.pts_time- self.pid2pts(pid), 6)} "
            )
            # self.scte35.cue_out = None

        else:
            self.scte35.cue_time = self.pid2pts(pid)
            self.active_data.write("# Splice Immediate\n")
        # self._mk_cue_splice_point(pid)

    def _mk_cue_splice_point(self, pid):
        """
        _mk_cue_splice_point inserts a tag
        at the time specified in the cue.
        """
        if self.scte35.cue:
            if self.scte35.cue_time == self.pid2pts(pid):
                if self.scte35.is_cue_out(self.scte35.cue):
                    print(
                        f"Splice Point {self.scte35.cue.command.name}@{self.scte35.cue_time}"
                    )
                    self.active_data.write(f"# Splice Point @ {self.scte35.cue_time}\n")
                    self.scte35.cue_out = "OUT"
                    self._add_discontinuity()
            if self.scte35.break_timer >= self.scte35.break_duration:
                self.active_data.write(f"# Splice Point @ {self.scte35.cue_time}\n")
                self._add_discontinuity()
                self.scte35.cue_out = "IN"

            if self.scte35.cue_out is None:
                self.scte35.cue_time = None

    def cue_out_continue(self):
        """
        cue_out_continue ensures that
        if there is an active SCTE35 cue,
        the live sliding window of segments
        has a tag with CUE-OUT=CONT
        """
        self.window_slot += 1
        self.window_slot = self.window_slot % (self.window_size + 1)

    def _mk_segment(self, pid):
        """
        _mk_segment cuts hls segments
        """
        now = self.pid2pts(pid)
        # if now - self.seg.seg_start >= self.seconds:
        if now >= self.seg.seg_stop:
            self.seg.seg_stop = now
        if self.scte35.cue_time:
            if self.seg.seg_start < self.scte35.cue_time < self.seg.seg_stop:
                self.scte35.cue_time = self.seg.seg_stop
            if self.scte35.cue_time == now:
                if self.scte35.is_cue_out(self.scte35.cue):
                    self._mk_cue_splice_point(pid)
                    self.scte35.cue_time = None
                if self.scte35.is_cue_in(self.scte35.cue):
                    if self.scte35.break_timer > self.scte35.break_duration:
                        self.scte35.cue_out = "IN"
                        self._mk_cue_splice_point(pid)
        if self.seg.seg_stop:
            if self.seg.seg_stop <= now:
                self.seg.seg_stop = now
                if self.program_date_time_flag:
                    iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
                    self.active_data.write(f"#Iframe @ {self.pid2pts(pid)} \n")
                    self.active_data.write(f"#EXT-X-PROGRAM-DATE-TIME:{iso8601}\n")
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

            cue_tag = self.scte35.mk_cue_tag()
            if cue_tag:
                print(cue_tag)
                self.active_data.write(cue_tag + "\n")
            if self.scte35.break_duration:
                self.scte35.break_timer += self.seg.seg_time

            with open(self.seg.seg_uri, "wb+") as a_seg:
                a_seg.write(self.active_segment.getbuffer())
                a_seg.flush()
            del self.active_segment
            self.active_data.write(f"#EXTINF:{self.seg.seg_time:.3f},\n")
            self.active_data.write(seg_file + "\n")
            self.seg.seg_start = self.seg.seg_stop
            self.seg.seg_stop += self.seconds
            self.window.append(
                (self.seg.seg_num, self.seg.seg_uri, self.active_data.getvalue())
            )
            self.seg.seg_num += 1
            if self.scte35.cue_out == "OUT":
                self.scte35.cue_out = "CONT"
            self.active_data = io.StringIO()
            self.active_segment = io.BytesIO()
            self.stream_diff()

            if self.live:
                self.cue_out_continue()

    def _auto_return(self):
        if self.scte35.cue_out == "CONT":
            if self.scte35.break_timer >= self.scte35.break_duration:
                self.scte35.cue_out = "IN"
                self.scte35.break_timer = None
                self.active_data.write("#auto")
                self._add_discontinuity()
            # self.scte35.cue_out_cue_in()

    def _pop_segment(self):
        if len(self.window) > self.window_size:
            if self.delete:
                drop = self.window[0][1]
                print(f"deleting {drop}")
                os.unlink(drop)
            self.window = self.window[1:]

    def _discontinuity_seq_plus_one(self):
        if "DISCONTINUITY" in self.window[0][2]:
            self.discontinuity_sequence += 1
        if "DISCONTINUITY" in self.window[-1][2]:
            self._reset_stream()

    def _reset_stream(self):
        self.seg.seg_start = None
        self.seg.seg_stop = None

    def _open_m3u8(self):
        m3u8_uri = self.mk_uri(self.output_dir, "index.m3u8")
        return open(m3u8_uri, "w+", encoding="utf-8")

    def _write_manifest(self):
        """
        _write_manifest writes segment meta data from
        self.window to an m3u8 file
        """
        if self.live:
            self._discontinuity_seq_plus_one()
            self._pop_segment()
            if self.window:
                self.seg.start_seg_num = self.window[0][0]
            else:
                return
        with self._open_m3u8() as m3u8:
            self._mk_header()
            m3u8.write(self.header)
            for i in self.window:
                m3u8.write(i[2])
            if self.scte35.cue_out == "IN":
                self.scte35.cue_out = None
            if not self.live:
                m3u8.write("#EXT-X-ENDLIST")

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
        rev = res = ""
        now = time.time()
        gen_time = now - self.seg.init_time
        if not self.seg.seg_time:
            self.seg.seg_time = self.seconds
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
            self.maps.prgm_pts[prgm] = pts
            if not self.seg.seg_start:
                self.seg.seg_start = self.as_90k(pts)
                self.seg.seg_stop = self.seg.seg_start + self.seconds

    def _parse(self, pkt):
        """
        _parse parses mpegts and
        writes the packet to self.active_segment.
        """

        pid = self._parse_info(pkt)
        self.chk_sidecar_cues(pid)
        if pid in self.pids.scte35:
            self.chk_stream_cues(pkt, pid)
        if self._pusi_flag(pkt):
            if self.iframer.parse(pkt):
                self._parse_pts(pkt, pid)
                self.load_sidecar(self.sidecar_file, pid)
                self._mk_segment(pid)
                if not self.start:
                    self.start = True
        self.active_segment.write(pkt)

    def loop(self):
        """
        loop  loops a video in the hls manifest.
        sliding window and throttled to simulate live playback,
        segments are deleted when they fall out the sliding window.
        """

        self.decode()
        self._reset_stream()
        self._add_discontinuity()
        self._tsdata = reader(self.in_stream)

        return True

    def run(self):
        """
        run calls replay() if replay is set
        or else it calls decode()
        """
        if self.replay:
            while True:
                self.loop()
        else:
            self.decode()


def cli():
    """
    cli provides one function call
    for running X9K3  with command line args
    Two lines of code gives you a full X9K3 command line tool.

     from X9K3 import cli
     cli()

    """
    stuff = X9K3()
    stuff.run()


if __name__ == "__main__":
    x9k = X9K3()
    x9k.run()
