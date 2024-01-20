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
from pathlib import Path
from new_reader import reader
from iframes import IFramer
from threefive import Cue, print2, Segment
import threefive.stream as strm

from m3ufu import M3uFu


MAJOR = "0"
MINOR = "2"
MAINTAINENCE = "59"

ON = "\033[1m"
OFF = "\033[0m"


def version():
    """
    version prints x9k3's version as a string
    Odd number versions are releases.
    """
    return f"{MAJOR}.{MINOR}.{MAINTAINENCE}"


class X9K3(strm.Stream):
    """
    X9K3 class
    """

    def __init__(self, tsdata=None, show_null=False):
        super().__init__(tsdata, show_null)
        self._tsdata = tsdata
        self.in_stream = tsdata
        self.active_segment = io.BytesIO()
        self.iframer = IFramer(shush=True)
        self.scte35 = SCTE35()
        self.sidecar = deque()
        self.timer = Timer()
        self.m3u8 = "index.m3u8"
        self.window = SlidingWindow()
        self.segnum = 0
        self.args = argue()
        self.started = None
        self.next_start = None
        self.media_seq = 0
        self.discontinuity_sequence = 0
        self.first_segment = True
        self.media_list = deque()
        self.now = None
        self.last_sidelines = ""
        self.started_byte = 0
        self.now_byte = 0

    def _args_version(self):
        if self.args.version:
            print2(f"{ON}version(){OFF}")
            sys.exit()

    def _args_input(self):
        self.in_stream = self.args.input
        if self._tsdata is not None:
            self.args.input = self._tsdata
        else:
            self._tsdata = self.args.input

    def _args_hls_tag(self):
        tag_map = {
            "x_scte35": self.scte35.x_scte35,
            "x_cue": self.scte35.x_cue,
            "x_daterange": self.scte35.x_daterange,
            "x_splicepoint": self.scte35.x_splicepoint,
        }
        if self.args.hls_tag not in tag_map:
            raise ValueError(f"{ON}hls tag  must be in {tag_map.keys()}{OFF}")
        self.scte35.tag_method = tag_map[self.args.hls_tag]

    def _args_output_dir(self):
        if not os.path.isdir(self.args.output_dir):
            os.mkdir(self.args.output_dir)

    def _chk_flags(self, flags):
        if flags:
            return True in flags
        return None

    def _args_flags(self):
        """
        I really expected to do more here.
        """
        flags = deque([self.args.program_date_time, self.args.delete, self.args.replay])
        if self._chk_flags(flags):
            self.args.live = True
        flags.popleft()  # pop self.args.program_date_time
        if self._chk_flags(flags):
            self.window.delete = True
        flags.popleft()  # pop self.args.delete

        flags.popleft()  # pop self.args.replay

    def _args_window_size(self):
        if self.args.live:
            self.window.size = self.args.window_size

    def _args_continue_m3u8(self):
        if self.args.continue_m3u8:
            self.continue_m3u8()

    def apply_args(self):
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
        self._args_continue_m3u8()

        if isinstance(self._tsdata, str):
            self._tsdata = reader(self._tsdata)

    def _reload_a_pane(self, segment):
        if "#EXT-X-BYTERANGE" not in segment.tags:
            tmp_segnum = int(segment.relative_uri.split("seg")[1].split(".")[0])
            a_pane = Pane(
                segment.relative_uri,
                segment.media,
                tmp_segnum,
            )
            self.segnum = tmp_segnum
            for this in ["#EXT-X-X9K3-VERSION", "#EXT-X-ENDLIST"]:
                if this in segment.tags:
                    segment.tags.pop(this)
            a_pane.tags = segment.tags
            if "#EXTINF" in segment.tags:
                segment.tags["#EXTINF"] = f'{segment.tags["#EXTINF"] },'
            for line in segment.lines:
                if "#EXT-X-CUE-IN" in line:
                    a_pane.tags["#EXT-X-CUE-IN"] = None
                if "#EXT-X-DISCONTINUITY" in line:
                    a_pane.tags["#EXT-X-DISCONTINUITY"] = None
            self.window.slide_panes(a_pane)

    def _reload_m3u8(self):
        """
        m3u8_reload is called when the continue_m3u8 option is set.
        """
        m3 = M3uFu()
        m3.window_size = None
        tmp_name = self.mk_uri(self.args.output_dir, "tmp.m3u8")
        with open(tmp_name, "w", encoding="utf8") as tmp_m3u8:
            with open(self.m3u8uri(), "r", encoding="utf8") as m3u8:
                tmp_m3u8.write("\n".join(m3u8.readlines()))
                tmp_m3u8.write("\n#EXT-X-ENDLIST\n")
        m3.m3u8 = tmp_name
        m3.decode()
        if "#EXT-X-DISCONTINUITY-SEQUENCE" in m3.headers:
            self.discontinuity_sequence = int(
                m3.headers["#EXT-X-DISCONTINUITY-SEQUENCE"]
            )
        if "#EXT-X-MEDIA-SEQUENCE" in m3.headers:
            self.media_seq = int(m3.headers["#EXT-X-MEDIA-SEQUENCE"])
        segments = list(m3.segments)
        m3.segments[-1].tags["#EXT-X-DISCONTINUITY"] = None
        for segment in segments:
            self._reload_a_pane(segment)
        # if self.window.panes:
        if self.args.live:
            self.window.slide_panes()
        os.unlink(tmp_name)
        self.first_segment = True

    def continue_m3u8(self):
        """
        continue_m3u8 reads self.discontinuity_sequence
        and self.segnum from an existing index.m3u8.
        """
        if self.args.iframe or self.args.byterange:
            print2(
                f"{ON}Cannot continue m3u8  as 'iframe only' or 'byterange' hls.{OFF}"
            )
            return
        if os.path.isfile(self.m3u8uri()):
            self._reload_m3u8()
            self.segnum += 1
            print2(
                f"{ON}Continuing {self.m3u8uri()} @ segment number {self.segnum}{OFF}"
            )

    def m3u8uri(self):
        """
        m3u8uri return full path to the output index.m3u8
        """
        return self.mk_uri(self.args.output_dir, self.m3u8)

    @staticmethod
    def mk_uri(head, tail):
        """
        mk_uri is used to create local filepaths
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
        m3u_version = "#EXT-X-VERSION:4"
        target = f"#EXT-X-TARGETDURATION:{int(self.args.time+1)}"
        seq = f"#EXT-X-MEDIA-SEQUENCE:{self.media_seq}"
        dseq = f"#EXT-X-DISCONTINUITY-SEQUENCE:{self.discontinuity_sequence}"
        x9k3v = f"#EXT-X-X9K3-VERSION:{version()}"
        bumper = ""
        if self.args.iframe:
            bumper = "#EXT-X-I-FRAMES-ONLY\n" + bumper
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

    def _add_discontinuity(self, a_pane):
        """
        _add_discontinuity adds a discontinuity tag.
        """
        if not self.args.no_discontinuity:
            a_pane.add_tag("#EXT-X-DISCONTINUITY", None)

    def _add_cue_tag(self, a_pane):
        """
        _add_cue_tag adds SCTE-35 tags,
        auto CUE-INs, and discontinuity tags.
        """
        if self.scte35.break_timer is not None:
            if self.scte35.break_timer >= self.scte35.break_duration:
                self.scte35.break_timer = None
                self.scte35.cue_state = "IN"
        tag = self.scte35.mk_cue_tag()
        if tag:
            if self.scte35.cue_state in ["OUT", "IN"]:
                self._add_discontinuity(a_pane)
            kay = tag
            vee = None
            if ":" in tag:
                kay, vee = tag.split(":", 1)
            a_pane.add_tag(kay, vee)
            print2(f"{kay} = {vee}")

    def _chk_pdt_flag(self, a_pane):
        if self.args.program_date_time:
            a_pane.add_tag("#Iframe", f" @ {self.started}")
            iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
            a_pane.add_tag("#EXT-X-PROGRAM-DATE-TIME", f"{iso8601}")

    def _chk_live(self, seg_time):
        if self.args.live:
            self.window.slide_panes()
            if not self.args.no_throttle:
                self.timer.throttle(seg_time)
            self._discontinuity_seq_plus_one()

    def _mk_a_pane_tags(self, a_pane, seg_time):
        self._add_cue_tag(a_pane)
        self._chk_pdt_flag(a_pane)
        a_pane.add_tag("#EXTINF", f"{seg_time:.6f},")

        if self.is_byterange():
            tag = "#EXT-X-BYTERANGE"
            val = f"{self.now_byte - self.started_byte}@{self.started_byte}"
            a_pane.add_tag(tag, val)

    def _print_segment_details(self, seg_name, seg_time):
        if not self.started:
            return
        one = f"{seg_name}:   start: {self.started:.6f}   "
        two = f"end: {self.now:.6f}   duration: {seg_time:.6f}"
        print2(f"{one}{two}")

    def _mk_a_pane(self, seg_file, seg_name, seg_time):
        a_pane = Pane(seg_file, seg_name, self.segnum)
        if self.first_segment:
            if self.args.replay or self.args.continue_m3u8:
                self._add_discontinuity(a_pane)
        self._mk_a_pane_tags(a_pane, seg_time)
        self.window.slide_panes(a_pane)

    def _write_segment_file(self, seg_name):
        with open(seg_name, "wb") as seg:
            seg.write(self.active_segment.getbuffer())

    def is_byterange(self):
        """
        is byterange returns True if m3u8 is byterange.
        """
        if self.args.byterange and ".ts" in self.args.input:
            return True
        return False

    def _write_segment(self):
        if not self.segnum:
            self.segnum = 0
        seg_file = f"seg{self.segnum}.ts"
        seg_name = self.mk_uri(self.args.output_dir, seg_file)
        if self.is_byterange():
            seg_name = self.args.input
            seg_file = self.args.input
        seg_time = round((self.now - self.started), 6)
        if seg_time <= 0:
            return
        if not self.is_byterange():
            self._write_segment_file(seg_name)
            if seg_time > self.args.time + 2:
                print2(f"{ON}Verifying {seg_name} time of {seg_time}{OFF}")
                s = Segment(seg_name)
                s.decode()
                if s.duration:
                    seg_time = s.duration
                    print2(f"{ON}Setting {seg_name} time to {seg_time}{OFF}")
        self._mk_a_pane(seg_file, seg_name, seg_time)
        self._write_m3u8()
        self._print_segment_details(seg_name, seg_time)
        #   self._reset_stream()
        if self.scte35.break_timer is not None:
            self.scte35.break_timer += seg_time
        self.scte35.chk_cue_state()
        self._chk_live(seg_time)
        self._start_next_start(pts=self.now)
        self.started_byte = self.now_byte

    def _clear_endlist(self, lines):
        return [line for line in lines if not self._endlist(line)]

    @staticmethod
    def clobber_file(the_file):
        """
        clobber_file  blanks the_file
        """
        with open(the_file, "w", encoding="utf8") as clobbered:
            clobbered.close()

    @staticmethod
    def _endlist(line):
        if "ENDLIST" in line:
            return True
        return False

    def _write_m3u8(self):
        self.media_seq = self.window.panes[0].num
        self._discontinuity_seq_plus_one()
        with open(self.m3u8uri(), "w+", encoding="utf8") as m3u8:
            m3u8.write(self._header())
            m3u8.write(self.window.all_panes())
            self.segnum += 1
            self.first_segment = False
        self.active_segment = io.BytesIO()
        self.window.slide_panes()

    def load_sidecar(self):
        """
        load_sidecar reads (pts, cue) pairs from
        the sidecar file and loads them into X9K3.sidecar
        """
        if self.args.sidecar_file:
            with reader(self.args.sidecar_file) as sidefile:
                sidelines = sidefile.readlines()
                if sidelines == self.last_sidelines:
                    return
                for line in sidelines:
                    line = line.decode().strip().split("#", 1)[0]
                    if line:
                        print2(f"{ON}loading  {line}{OFF}")
                        if float(line.split(",", 1)[0]) == 0.0:
                            line = f'{self.now},{line.split(",",1)[1]}'
                        self.add2sidecar(line)
                sidefile.close()
                self.last_sidelines = sidelines
            self.clobber_file(self.args.sidecar_file)

    def add2sidecar(self, line):
        """
        add2sidecar add insert_pts,cue to the deque
        """
        insert_pts, cue = line.split(",", 1)
        insert_pts = float(insert_pts)
        if [insert_pts, cue] not in self.sidecar:
            self.sidecar.append([insert_pts, cue])
            self.sidecar = deque(sorted(self.sidecar, key=itemgetter(0)))

    def _chk_sidecar_cues(self, pid):
        """
        _chk_sidecar_cues checks the insert pts time
        for the next sidecar cue and inserts the cue if needed.
        """
        if self.sidecar:
            for s in list(self.sidecar):
                splice_pts = float(s[0])
                splice_cue = s[1]
                if self.started:
                    if self.started <= splice_pts <= self.now:
                        self.sidecar.remove(s)
                        self.scte35.cue = Cue(splice_cue)
                        self.scte35.cue.decode()
                        self.scte35.cue.show()
                        self._chk_cue_time(pid)
                        self._chk_splice_point()

    def _discontinuity_seq_plus_one(self):
        if self.window.panes:
            if "#EXT-X-DISCONTINUITY" in self.window.panes[0].tags:
                if len(self.window.panes) >= self.window.size:
                    self.discontinuity_sequence += 1
            if "#EXT-X-DISCONTINUITY" in self.window.panes[-1].tags:
                self._reset_stream()

    def _reset_stream(self):
        self.started = None
        self.next_start = None

    def _start_next_start(self, pts=None):
        """
        _start_next_start sets when the current
        segment starts and ends.
        """
        rollover = self.ROLLOVER / 90000.0
        if pts is not None:
            self.started = pts
        else:
            self.started = self.next_start
        self.next_start = self.started + self.args.time
        if self.next_start + self.args.time > rollover:
            self._reset_stream()

    def _chk_splice_point(self):
        """
        _chk_splice_point checks for the slice point
        of a segment.
        """
        if self.started:
            if self.scte35.cue_time:
                if self.started < self.scte35.cue_time < self.next_start:
                    self.next_start = self.scte35.cue_time
            if self.now >= self.next_start:
                self.next_start = self.now
                self._write_segment()
                self.scte35.mk_cue_state()

    def _chk_cue_time(self, pid):
        if self.scte35.cue:
            self.scte35.cue_time = self._adjusted_pts(self.scte35.cue, pid)

    def _adjusted_pts(self, cue, pid):
        pts = 0
        if "pts_time" in cue.command.get():
            pts = cue.command.pts_time
        else:
            pts = self.pid2pts(pid)
        pts_adjust = cue.info_section.pts_adjustment
        adj_pts = (pts + pts_adjust) % self.as_90k(self.ROLLOVER)
        return round(adj_pts, 6)

    @staticmethod
    def _rai_flag(pkt):
        """
        _rai_flag random access indicator flag
        """
        return pkt[5] & 0x40

    def _shulga_mode(self, pkt):
        """
        _shulga_mode is mpeg2 video iframe detection
        """
        if self._rai_flag(pkt):
            self._chk_splice_point()

    def _parse_scte35(self, pkt, pid):
        """
        _parse_scte35 overrides the inherited method.
        """
        cue = super()._parse_scte35(pkt, pid)
        if cue:
            cue.decode()
            self.scte35.cue = cue
            self._chk_cue_time(pid)
            self.add2sidecar(f"{self._adjusted_pts(cue, pid)}, {cue.encode()}")
        return cue

    def _chk_iframe(self, pkt, pkt_pid):
        i_pts = self.iframer.parse(pkt)
        if i_pts:
            self.now = i_pts
            if self.args.iframe:
                self.next_start = i_pts
            self.load_sidecar()
            self._chk_sidecar_cues(pkt_pid)
            self._chk_splice_point()

    def _parse(self, pkt):
        """
        _parse is run on every packet.
        """
        super()._parse(pkt)
        self.now_byte += 188
        pkt_pid = self._parse_pid(pkt[1], pkt[2])
        self.now = self.pid2pts(pkt_pid)
        if not self.started:
            self._start_next_start(pts=self.now)
        if self._pusi_flag(pkt) and self.started:
            if self.args.shulga:
                self._shulga_mode(pkt)
            else:
                self._chk_iframe(pkt, pkt_pid)
        if not self.is_byterange():
            self.active_segment.write(pkt)

    def _last_buff(self):
        """
        _last_buff writes antthing left in the
        active_segment buffer for the last segment.
        """
        buff = self.active_segment.getbuffer()
        if buff:
            self._write_segment()
            time.sleep(0.5)

    def addendum(self):
        """
        addendum post stream parsing related tasks.
        """
        self._last_buff()
        if not self.args.live:
            with open(self.m3u8uri(), "a", encoding="utf8") as m3u8:
                m3u8.write("#EXT-X-ENDLIST")

    def decode(self, func=False):
        """
        decode applies any set args,
        and starts parsing.
        """
        self.apply_args()
        _ = {print(k, "=", v) for k, v in vars(self.args).items()}
        self.timer.start()
        if isinstance(self.args.input, str) and ("m3u8" in self.args.input):
            self.decode_m3u8(self.args.input)
        else:
            super().decode()
        self.addendum()

    def _parse_m3u8_media(self, media):
        """
        _parse_m3u8_media parse a segment from
        a m3u8 input file if it has not been parsed.
        """
        max_media = 10101
        if media not in self.media_list:
            self.media_list.append(media)
            while len(self.media_list) > max_media:
                self.media_list.popleft()
            self._tsdata = reader(media)
            for pkt in self.iter_pkts():
                self._parse(pkt)
            self._tsdata.close()

    def decode_m3u8(self, manifest=None):
        """
        decode_m3u8 is called when the input file is a m3u8 playlist.
        """
        based = manifest.rsplit("/", 1)
        if len(based) > 1:
            base_uri = f"{based[0]}/"
        else:
            base_uri = ""
        while True:
            with reader(manifest) as manifesto:
                m3u8 = manifesto.readlines()
                for line in m3u8:
                    if not line:
                        break
                    line = _clean_line(line)
                    if self._endlist(line):
                        return False
                    if line.startswith("#"):
                        media = None
                    else:
                        media = line
                        if base_uri not in media:
                            media = base_uri + media
                        self._parse_m3u8_media(media)


def _clean_line(line):
    if isinstance(line, bytes):
        line = line.decode(errors="ignore")
    line = line.replace("\n", "").replace("\r", "")
    return line


def decode_playlist(playlist):
    """
    decode_playlist parses a playlist file
    and segments all the media into 1 stream.
    A playlist file is a list of media OR media,sidecar lines
    Example:

    /home/a/video.ts
    /home/a/othervideo.ts,/home/a/other_sidecar.txt
    https://futzu.com/xaa.ts

    """
    comma = ","
    octothorpe = "#"
    sidecar = None
    first = True
    with reader(playlist) as plist:
        for line in plist.readlines():
            if not line:
                break
            line = _clean_line(line)
            media = line.split(octothorpe)[0]
            if media:
                if comma in media:
                    media, sidecar = media.split(comma)
                print2(f"{ON}loading media {media}{OFF}")
                x9 = X9K3()
                if sidecar:
                    print2(f"{ON}loading sidecar file {sidecar}{OFF}")
                    x9.args.sidecar_file = sidecar
                x9.args.input = media
                if first:
                    x9.decode()
                    first = False
                else:
                    x9.continue_m3u8()
                    x9.decode()


def cli():
    """
    cli provides one function call for running X9K3.
    """
    args = argue()
    if isinstance(args.input, str) and ("playlist" in args.input):
        decode_playlist(args.input)
    else:
        x9 = X9K3()
        x9.decode()
        while args.replay:
            x9 = X9K3()
            x9.continue_m3u8()
            x9.decode()


if __name__ == "__main__":
    cli()
