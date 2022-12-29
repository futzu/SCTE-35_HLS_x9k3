#!/usr/bin/env python3

"""
X9K3
"""


import argparse
import datetime
import io
import os
import sys
import time
from collections import deque
from operator import itemgetter
from iframes import IFramer
from new_reader import reader
from threefive import Cue
import threefive.stream as strm


MAJOR = "0"
MINOR = "1"
MAINTAINENCE = "79"


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


class X9K3(strm.Stream):
    def __init__(self, tsdata=None, show_null=False):
        super().__init__(tsdata, show_null)
        self._tsdata = tsdata
        self.in_stream = tsdata
        self.active_segment = io.BytesIO()
        self.iframer = IFramer(shush=True)
        self.window = SlidingWindow(500)
        self.scte35 = SCTE35()
        self.sidecar = deque()
        self.timer = Timer()
        self.m3u8 = "index.m3u8"
        self.started = None
        self.next_start = None
        self.segnum = 0
        self.media_seq = 0
        self.discontinuity_sequence = 0
        self.args = argue()
        self._apply_args()

    def _args_version(self):
        if self.args.version:
            print(version())
            sys.exit()

    def _args_input(self):
        self._tsdata = self.args.input
        self.in_stream = self.args.input

    def _args_hls_tag(self):
        tag_map = {
            "x_scte35": self.scte35.x_scte35,
            "x_cue": self.scte35.x_cue,
            "x_daterange": self.scte35.x_daterange,
            "x_splicepoint": self.scte35.x_splicepoint,
        }
        if self.args.hls_tag not in tag_map:
            raise ValueError(f"hls tag  must be in {tag_map.keys()}")
        self.scte35.tag_method = tag_map[self.args.hls_tag]

    def _args_output_dir(self):
        if not os.path.isdir(self.args.output_dir):
            os.mkdir(self.args.output_dir)

    def _args_flags(self):
        if self.args.program_date_time or self.args.delete or self.args.replay:
            self.args.live = True
            if self.args.delete or self.args.replay:
                self.window.delete = True

    def _args_window_size(self):
        if self.args.live:
            self.window.size = self.args.window_size

    def _apply_args(self):
        """
        _apply_args  uses command line args
        to set X9K3 instance vars
        """
        self._args_version()
        self._args_input()
        self._args_hls_tag()
        self._args_output_dir()
        self._args_flags()
        self._args_window_size()

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

    def _header(self):
        """
        header generates the m3u8 header lines
        """
        m3u = "#EXTM3U"
        m3u_version = "#EXT-X-VERSION:3"
        target = f"#EXT-X-TARGETDURATION:{int(self.args.time+1)}"
        seq = f"#EXT-X-MEDIA-SEQUENCE:{self.media_seq}"
        dseq = f"#EXT-X-DISCONTINUITY-SEQUENCE:{self.discontinuity_sequence}"
        x9k3v = f"#EXT-X-X9K3-VERSION:{version()}"
        bumper = ""
        return "\n".join(
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

    def _add_cue_tag(self, chunk, seg_time):
        """
        _add_cue_tag adds SCTE-35 tags,
        handles break auto returns,
        and adds discontinuity tags as needed.
        """
        if self.scte35.break_timer is not None:
            if self.scte35.break_timer >= self.scte35.break_duration:
                self.scte35.break_timer = None
                self.scte35.cue_state = "IN"
        tag = self.scte35.mk_cue_tag()
        if tag:
            if self.scte35.cue_state in ["OUT", "IN"]:
                chunk.add_tag("#EXT-X-DISCONTINUITY", None)
            kay = tag
            vee = None
            if ":" in tag:
                kay, vee = tag.split(":", 1)
            chunk.add_tag(kay, vee)
            print(kay, vee, file=sys.stderr)

    def _chk_pdt_flag(self, chunk):
        if self.args.program_date_time:
            iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
            chunk.add_tag("#Iframe", f"{self.started}")
            chunk.add_tag("#EXT-X-PROGRAM-DATE-TIME", f"{iso8601}")

    def _write_segment(self):
        seg_file = f"seg{self.segnum}.ts"
        seg_name = self.mk_uri(self.args.output_dir, seg_file)
        seg_time = round(self.next_start - self.started, 6)

        with open(seg_name, "wb") as seg:
            seg.write(self.active_segment.getbuffer())
        chunk = Chunk(seg_name, self.segnum)
        self._add_cue_tag(chunk, seg_time)
        self._chk_pdt_flag(chunk)
        chunk.add_tag("#EXTINF", f"{seg_time:.6f},")
        self.window.push_pane(chunk)
        self._write_m3u8()
        self._start_next_start()
        if self.scte35.break_timer is not None:
            self.scte35.break_timer += seg_time
        self.scte35.chk_cue_state()
        # print(seg_name, self.started,self.next_start, seg_time, file=sys.stderr, end='\r')
        print(
            f"{seg_name}:\tstart:{self.started}\tend:{self.next_start}\tduration:{seg_time}",
            file=sys.stderr,
        )
        if self.args.live:
            self.window.pop_pane()
            self.timer.throttle(seg_time)
            self._discontinuity_seq_plus_one()

    def _write_m3u8(self):
        self.media_seq = self.window.panes[0].num
        with open(self.m3u8, "w+") as m3u8:
            m3u8.write(self._header())
            m3u8.write(self.window.all_panes())
            self.segnum += 1
            if not self.args.live:
                m3u8.write("#EXT-X-ENDLIST")
        self.active_segment = io.BytesIO()

    def _load_sidecar(self, pid):
        """
        _load_sidecar reads (pts, cue) pairs from
        the sidecar file and loads them into X9K3.sidecar
        if live, blank out the sidecar file after cues are loaded.
        """
        if self.args.sidecar_file:
            with reader(self.args.sidecar_file) as sidefile:
                for line in sidefile:
                    line = line.decode().strip().split("#", 1)[0]
                    if len(line):
                        pts, cue = line.split(",", 1)
                        pts = float(pts)
                        if pts >= self.pid2pts(pid):
                            if [pts, cue] not in self.sidecar:
                                self.sidecar.append([pts, cue])
                                self.sidecar = deque(
                                    sorted(self.sidecar, key=itemgetter(0))
                                )
                sidefile.close()
            if self.args.live:
                with open(self.args.sidecar_file, "w") as scf:
                    scf.close()

    def _chk_sidecar_cues(self, pid):
        """
        _chk_sidecar_cues checks the insert pts time
        for the next sidecar cue and inserts the cue if needed.
        """
        if self.sidecar:
            if float(self.sidecar[0][0]) <= self.pid2pts(pid):
                raw = self.sidecar.popleft()
                self.scte35.cue_time = float(raw[0])
                self.scte35.cue = Cue(raw[1])
                self.scte35.cue.decode()
                self._chk_cue_time(pid)

    def _discontinuity_seq_plus_one(self):
        if "DISCONTINUITY" in self.window.panes[0].tags:
            self.discontinuity_sequence += 1
        if "DISCONTINUITY" in self.window.panes[-1].tags:
            self._reset_stream()

    def _reset_stream(self):
        self.started = None
        self.next_start = None

    def _start_next_start(self, pts=None):
        if pts is not None:
            self.started = pts
        else:
            self.started = self.next_start
        self.next_start = self.started + self.args.time

    def _chk_slice_point(self, now):
        """
        chk_slice_time checks for the slice point
        of a segment eoither buy self.args.time
        or by self.scte35.cue_time
        """
        if self.scte35.cue_time:
            if now >= self.scte35.cue_time:
                self.next_start = self.scte35.cue_time
                self._write_segment()
                self.scte35.cue_time = None
                self.scte35.mk_cue_state()
                return
        if now >= self.started + self.args.time:
            self.next_start = now
            self._write_segment()

    def _chk_cue_time(self, pid):
        """
        _chk_cue checks for SCTE-35 cues
        and inserts a tag at the time
        the cue is received.
        """
        if self.scte35.cue:
            pts_adjust = self.scte35.cue.info_section.pts_adjustment
            if "pts_time" in self.scte35.cue.command.get():
                self.scte35.cue_time = self.scte35.cue.command.pts_time + pts_adjust
            else:
                self.scte35.cue_time = self.pid2pts(pid) + pts_adjust

    @staticmethod
    def _rai_flag(pkt):
        return pkt[5] & 0x40

    def _shulga_mode(self, pkt, now):
        """
        _shulga_mode iframe detection
        """
        if self._rai_flag(pkt):
            self._chk_slice_point(now)

    def _parse_scte35(self, pkt, pid):
        cue = super()._parse_scte35(pkt, pid)
        if cue:
            cue.decode()
            cue.show()
            self.scte35.cue = cue
            self._chk_cue_time(pid)
        return cue

    def _parse(self, pkt):
        super()._parse(pkt)

        pkt_pid = self._parse_pid(pkt[1], pkt[2])
        now = self.pid2pts(pkt_pid)
        if not self.started:
            self._start_next_start(pts=now)
        if self._pusi_flag(pkt) and self.started:
            self._load_sidecar(pkt_pid)
            self._chk_sidecar_cues(pkt_pid)
            if self.args.shulga:
                self._shulga_mode(pkt, now)
            else:
                i_pts = self.iframer.parse(pkt)
                if i_pts:
                    self._chk_slice_point(i_pts)
        self.active_segment.write(pkt)

    def decode(self, func=False):
        """
        decode iterates mpegts packets
        and passes them to _parse.

        """
        self.timer.start()
        super().decode()

    def loop(self):
        """
        loop  loops a video in the hls manifest.
        sliding window and throttled to simulate live playback,
        segments are deleted when they fall out the sliding window.
        """
        self.decode()
        self._reset_stream()
        with open(self.m3u8, "w+") as m3u8:
            m3u8.write("#EXT-X-DISCONTINUITY")
        self._tsdata = reader(self.in_stream)
        return True

    def run(self):
        """
        run calls replay() if replay is set
        or else it calls decode()
        """
        if self.args.replay:
            while True:
                self.loop()
        else:
            self.decode()


class SCTE35:
    """
    A SCTE35 instance is used to hold
    SCTE35 cue data by X9K5.
    """

    def __init__(self):
        self.cue = None
        self.cue_state = None
        self.cue_time = None
        self.tag_method = self.x_cue
        self.break_timer = None
        self.break_duration = None
        self.event_id = 1

    def mk_cue_tag(self):
        """
        mk_cue_tag routes  hls tag creation
        to the appropriate method.
        """
        tag = False
        if self.cue:
            tag = self.tag_method()
        return tag

    def chk_cue_state(self):
        """
        chk_cue_state changes
        OUT to CONT
        and IN to None
        when the cue is expired.
        """
        if self.cue_state == "OUT":
            self.cue_state = "CONT"
        if self.cue_state == "IN":
            self.cue_time = None
            self.cue = None
            self.cue_state = None
            self.break_timer = None

    def mk_cue_state(self):
        """
        mk_cue_state checks if the cue
        is a CUE-OUT or a CUE-IN and
        sets cue_state.
        """
        if self.is_cue_out(self.cue):
            self.cue_state = "OUT"
            self.break_timer = 0.0
        if self.is_cue_in(self.cue):
            self.cue_state = "IN"

    def x_cue(self):
        """
        #EXT-X-CUE-( OUT | IN | CONT )
        """
        if self.cue_state == "OUT":
            return f"#EXT-X-CUE-OUT:{self.break_duration}"
        if self.cue_state == "IN":
            return "#EXT-X-CUE-IN"
        if self.cue_state == "CONT":
            return f"#EXT-X-CUE-OUT-CONT:{self.break_timer:.6f}/{self.break_duration}"
        return False

    def x_splicepoint(self):
        """
        #EXT-X-SPLICEPOINT-SCTE35
        """
        base = f"#EXT-X-SPLICEPOINT-SCTE35:{self.cue.encode()}"
        if self.cue_state == "OUT":
            return f"{base}"
        if self.cue_state == "IN":
            return f"{base}"
        return False

    def x_scte35(self):
        """
        #EXT-X-SCTE35
        """
        base = f'#EXT-X-SCTE35:CUE="{self.cue.encode()}" '
        if self.cue_state == "OUT":
            return f"{base},CUE-OUT=YES "
        if self.cue_state == "IN":
            return f"{base},CUE-IN=YES "
        if self.cue_state == "CONT":
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

        if self.cue_state == "OUT":
            fstart = f',START-DATE="{iso8601}"'
            tag = f"{fbase}{fstart}{fdur},SCTE35-OUT={self.cue.encode_as_hex()}"
            self.event_id += 1
            return tag

        if self.cue_state == "IN":
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
        if cue is None:
            return False
        cmd = cue.command
        if cmd.command_type == 5:
            if cmd.out_of_network_indicator:
                if cmd.break_duration:
                    self.break_duration = cmd.break_duration
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
                            return True
        return False

    def is_cue_in(self, cue):
        """
        is_cue_in checks a Cue instance
        to see if it is a cue_in event.
        Returns True for a cue_in event.
        """
        if cue is not None:
            cmd = cue.command
            if cmd.command_type == 5:
                if not cmd.out_of_network_indicator:
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
                            return True
        return False


class SlidingWindow:
    """
    The SlidingWindow class
    """

    def __init__(self, size=10000):
        self.size = size
        self.panes = []
        self.delete = False

    def pop_pane(self):
        """
        pop_pane removes the first item in self.panes
        """
        if len(self.panes) >= self.size:
            if self.delete:
                popped = self.panes[0].name
                print(f"deleting {popped}")
                os.unlink(popped)
            self.panes = self.panes[1:]

    def push_pane(self, a_pane):
        """
        push appends a_pane to self.panes
        """
        self.panes.append(a_pane)
        # print([a_pane.name for a_pane in self.panes])

    def all_panes(self):
        """
        all_panes returns the current window panes joined.
        """
        return "".join([a_pane.get() for a_pane in self.panes])

    def slide_panes(self, a_pane):
        """
        slide calls self.push_pane with a_pane
        and then calls self.pop_pane to trim self.panes
        as needed.
        """
        self.push_pane(a_pane)
        self.pop_pane()


class Timer:
    def __init__(self):
        self.begin = None
        self.end = None
        self.lap_time = None

    def start(self, begin=None):
        self.begin = begin
        if not self.begin:
            self.begin = time.time()
        self.end = None
        self.lap_time = None

    def stop(self, end=None):
        self.end = end
        if not self.end:
            self.end = time.time()
        self.lap_time = self.end - self.begin

    def elapsed(self, now=None):
        if not now:
            now = time.time()
        return now - self.begin

    def throttle(self, seg_time, begin=None, end=None):
        self.stop(end)
        diff = round(seg_time - self.lap_time, 2)
        if diff > 0:
            # print(f"throttling {diff}")#,file=sys.stderr, end='\r')
            time.sleep(diff)
        self.start(begin)


class Chunk:
    """
    Class to hold hls segment tags
    for a segment.
    """

    def __init__(self, name, num):
        self.tags = {}
        self.name = name
        self.num = num

    def get(self):
        """
        get returns the Chunk data formated.
        """
        this = []
        for k, v in self.tags.items():
            if v is None:
                this.append(k)
            else:
                this.append(f"{k}:{v}")
        this.append(self.name)
        this.append("")
        this = "\n".join(this)
        return this

    def add_tag(self, quay, val):
        """
        add_tag appends key and value for a hls tag
        """
        self.tags[quay] = val


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
