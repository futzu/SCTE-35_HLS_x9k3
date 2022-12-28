"""
X9K3
"""


import datetime
import io
import os
import sys
from collections import deque
from operator import itemgetter
from chunk import Chunk
from new_reader import reader
from iframes import IFramer
from threefive import Cue
import threefive.stream as strm
from scte35 import SCTE35
from args import argue

from timer import Timer
from window import SlidingWindow

MAJOR = "0"
MINOR = "1"
MAINTAINENCE = "76"


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
                self.args.delete = True

    def _args_window_size(self):
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
        self._args_window_size()
        self._args_flags()
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
        bump = ""
        self.media_seq = self.window.panes[0].num
        head = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            f"#EXT-X-TARGETDURATION:{int(self.args.time+1)}",
            f"#EXT-X-MEDIA-SEQUENCE:{self.media_seq}",
        ]
        if not self.args.live:
            head.append("#EXT-X-PLAYLIST-TYPE:VOD")
        head.append(bump)
        return "\n".join(head)

    def add_cue_tag(self, chunk, seg_time):
        """
        add_cue_tag adds SCTE-35 tags,
        handles break auto returns,
        and adds discontinuity tags as needed.
        """
        if self.scte35.break_timer is not None:
            if self.scte35.break_timer + seg_time > self.scte35.break_duration:
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
            print(kay, vee)

    def _chk_pdt_flag(self, chunk):
        if self.args.program_date_time:
            iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
            chunk.add_tag("#Iframe", f"{self.started}")
            chunk.add_tag("#EXT-X-PROGRAM-DATE-TIME", f"{iso8601}")

    def _write_segment(self):
        seg_file = f"seg{self.segnum}.ts"
        seg_name = self.mk_uri(self.args.output_dir, seg_file)
        seg_time = round(self.next_start - self.started,6)
        print(f"{seg_name}:\tstart:{self.started}\tend:{self.next_start}\tduration:{seg_time}", file=sys.stderr)
        with open(seg_name, "wb") as seg:
            seg.write(self.active_segment.getbuffer())
        chunk = Chunk(seg_name, self.segnum)
        self.add_cue_tag(chunk, seg_time)
        self._chk_pdt_flag(chunk)
        chunk.add_tag("#EXTINF", f"{seg_time:.6f},")
        self.window.push_pane(chunk)
        self._write_m3u8()
        self._start_next_start()
        if self.scte35.break_timer is not None:
            self.scte35.break_timer += seg_time
        self.scte35.chk_cue_state()
       # print(seg_name, self.started,self.next_start, seg_time, file=sys.stderr, end='\r')
        if self.args.live:
            self.window.pop_pane()
            self.timer.throttle(seg_time)
            self._discontinuity_seq_plus_one()


    def _write_m3u8(self):
        with open(self.m3u8, "w+") as m3u8:
            m3u8.write(self._header())
            m3u8.write(self.window.all_panes())
            self.segnum += 1
            if not self.args.live:
                m3u8.write("#EXT-X-ENDLIST")
        self.active_segment = io.BytesIO()


    def load_sidecar(self, pid):
        """
        load_sidecar reads (pts, cue) pairs from
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

    def chk_slice_point(self, now):
        """
        chk_slice_time checks for the slice point
        of a segment eoither buy self.args.time
        or by self.scte35.cue_time
        """
        if self.scte35.cue_time:
            if now >= self.scte35.cue_time >= self.next_start:
                self.next_start = self.scte35.cue_time
                self._write_segment()
                self.scte35.cue_time = None
                self.scte35.mk_cue_state()
                return
        if now >= self.started +self.args.time:
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

    def shulga_mode(self, pkt, now):
        """
        shulga_mode iframe detection
        """
        if self._rai_flag(pkt):
            self.chk_slice_point(now)

    def _parse_scte35(self, pkt, pid):
        cue = super()._parse_scte35(pkt, pid)
        if cue:
            cue.decode()
          #  cue.show()
            self.scte35.cue = cue
            self._chk_cue_time(pid)
        return cue

    def _parse(self, pkt):
        super()._parse(pkt)
        pkt_pid = self._parse_pid(pkt[1], pkt[2])
        now = self.pid2pts(pkt_pid)
        if not self.started:
            self._start_next_start(pts=now)
        if self._pusi_flag(pkt):
            self.load_sidecar(pkt_pid)
            if self.args.shulga:
                self.shulga_mode(pkt, now)
            else:
                i_pts = self.iframer.parse(pkt)
                if i_pts:
                  #  print(f"iframe: {i_pts} now: {now} ")
                    self.chk_sidecar_cues(pkt_pid)
                    self.chk_slice_point(i_pts)
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
