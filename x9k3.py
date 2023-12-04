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
from new_reader import reader
from iframes import IFramer
from threefive import Cue, print2
import threefive.stream as strm
from m3ufu import M3uFu


MAJOR = "0"
MINOR = "2"
MAINTAINENCE = "19"


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
        self.segnum = None
        self.args = argue()
        self.apply_args()
        self.started = None
        self.next_start = None
        self.media_seq = 0
        self.discontinuity_sequence = 0
        self.first_segment = True
        self.media_list = deque()
        self.now = None
        self.last_sidelines = ""

    def _args_version(self):
        if self.args.version:
            print2(version())
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
            raise ValueError(f"hls tag  must be in {tag_map.keys()}")
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

    def _reload_chunk(self, segment):
        tmp_segnum = int(segment.relative_uri.split("seg")[1].split(".")[0])
        chunk = Chunk(
            self.mk_uri(self.args.output_dir, segment.relative_uri),
            segment.media,
            tmp_segnum,
        )
        for this in ["#EXT-X-X9K3-VERSION", "#EXT-X-ENDLIST"]:
            if this in segment.tags:
                segment.tags.pop(this)
        chunk.tags = segment.tags
        self.window.slide_panes(chunk)

    def reload_m3u8(self):
        """
        m3u8_reload is called when the continue_m3u8 option is set.
        The index.m3u8 file is copied to tmp.m3u8 and a "#EXT-X-ENDLIST" tag
        is appended so that m3ufu doesn't keep trying to reload it as a live stream.
        An M3uFu instance parses tmp.m3u8 and loads the data into
        the SlidingWindow, X9K3.window.
        """
        m3 = M3uFu()
        tmp_name = self.mk_uri(self.args.output_dir, "tmp.m3u8")
        with open(tmp_name, "w", encoding="utf8") as tmp_m3u8:
            with open(self.m3u8uri(), "r", encoding="utf8") as m3u8:
                tmp_m3u8.write("\n".join(m3u8.readlines()))
                tmp_m3u8.write("\n#EXT-X-ENDLIST\n")
        m3.m3u8 = tmp_name
        m3.decode()
        self.discontinuity_sequence = m3.headers["#EXT-X-DISCONTINUITY-SEQUENCE"]
        segments = list(m3.segments)
        for segment in segments:
            self._reload_chunk(segment)
        if self.args.live or self.args.continue_m3u8:
            self.window.slide_panes()
        os.unlink(tmp_name)

    def continue_m3u8(self):
        """
        continue_m3u8 reads self.discontinuity_sequence
        and self.segnum from an existing index.m3u8
        when the self.args.continue_m3u8 flag is set.
        """
        with open(self.m3u8uri(), "r", encoding="utf8") as manifest:
            lines = manifest.readlines()
            segment_list = [line for line in lines if not line.startswith("#")]
            self.segnum = int(segment_list[-1].split("seg")[1].split(".")[0]) + 1
        self.reload_m3u8()
        print2(f"Continuing {self.m3u8uri()} @ segment number {self.segnum}")

    def m3u8uri(self):
        """
        m3u8uri return full path to the output index.m3u8
        """
        return self.mk_uri(self.args.output_dir, self.m3u8)

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

    def add_discontinuity(self, chunk):
        """
        add_discontinuity adds a discontinuity tag.
        """
        if not self.args.no_discontinuity:
            chunk.add_tag("#EXT-X-DISCONTINUITY", None)

    def _add_cue_tag(self, chunk):
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
                self.add_discontinuity(chunk)
            kay = tag
            vee = None
            if ":" in tag:
                kay, vee = tag.split(":", 1)
            chunk.add_tag(kay, vee)
            print2(f"{kay} = {vee}")

    def _chk_pdt_flag(self, chunk):
        if self.args.program_date_time:
            iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
            chunk.add_tag("#Iframe", f" @ {self.started}")
            chunk.add_tag("#EXT-X-PROGRAM-DATE-TIME", f"{iso8601}")

    def _chk_live(self, seg_time):
        """
        _chk_live

            * slides the sliding window
            * throttles to simulate live stream
            * increments discontinuity sequence
        """
        if self.args.live:
            self.window.slide_panes()
            self.timer.throttle(seg_time)
            self._discontinuity_seq_plus_one()

    def _mk_chunk_tags(self, chunk, seg_time):
        self._add_cue_tag(chunk)
        self._chk_pdt_flag(chunk)
        chunk.add_tag("#EXTINF", f"{seg_time:.6f},")

    def _print_segment_details(self, seg_name, seg_time):
        one = f"{seg_name}:   start: {self.started:.6f}   "
        two = f"end: {self.next_start:.6f}   duration: {seg_time:.6f}"
        print2(f"{one}{two}")

    def _write_segment(self):
        if self.segnum is None:
            self.segnum = 0
        seg_file = f"seg{self.segnum}.ts"
        seg_name = self.mk_uri(self.args.output_dir, seg_file)
        seg_time = round(self.now - self.started, 6)
        with open(seg_name, "wb") as seg:
            seg.write(self.active_segment.getbuffer())
        if seg_time <= 0:
            return
        chunk = Chunk(seg_file, seg_name, self.segnum)
        if self.first_segment:
            if self.args.replay or self.args.continue_m3u8:
                self.add_discontinuity(chunk)
        self._mk_chunk_tags(chunk, seg_time)
        self.window.slide_panes(chunk)
        self._write_m3u8()
        self._print_segment_details(seg_name, seg_time)
        self._start_next_start()
        if self.scte35.break_timer is not None:
            self.scte35.break_timer += seg_time
        self.scte35.chk_cue_state()
        self._chk_live(seg_time)

    def _clear_endlist(self, lines):
        return [line for line in lines if not self._endlist(line)]

    @staticmethod
    def _endlist(line):
        if "ENDLIST" in line:
            return True
        return False

    def _write_m3u8(self):
        """
        _write_m3u8 writes the index.m3u8
        """
        self.media_seq = self.window.panes[0].num
        with open(self.m3u8uri(), "w+", encoding="utf8") as m3u8:
            m3u8.write(self._header())
            m3u8.write(self.window.all_panes())
            self.segnum += 1
            self.first_segment = False
        self.active_segment = io.BytesIO()
        self.window.slide_panes()

    def _load_sidecar(self, pid):
        """
        _load_sidecar reads (pts, cue) pairs from
        the sidecar file and loads them into X9K3.sidecar
        if live, blank out the sidecar file after cues are loaded.
        """
        if self.args.sidecar_file:
            with reader(self.args.sidecar_file) as sidefile:
                sidelines = sidefile.readlines()
                if sidelines == self.last_sidelines:
                    return
                for line in sidelines:
                    line = line.decode().strip().split("#", 1)[0]
                    if len(line):
                        if line.split(",", 1)[0] in ["0", "0.0", 0, 0.0]:
                            if self.args.live:
                                line = f'{self.next_start},{line.split(",",1)[1]}'
                        self.add2sidecar(line)
                sidefile.close()
                self.last_sidelines = sidelines
                self._clear_sidecar_file()

    def _clear_sidecar_file(self):
        if self.args.live and not self.args.replay:
            with open(self.args.sidecar_file, "w", encoding="utf8") as scf:
                scf.close()

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
            if float(self.sidecar[0][0]) <= self.pid2pts(pid):
                raw = self.sidecar.popleft()
                self.scte35.cue_time = float(raw[0])
                self.scte35.cue = Cue(raw[1])
                self.scte35.cue.decode()
                self.scte35.cue.show()
                self._chk_cue_time(pid)

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
        if pts is not None:
            self.started = pts
        else:
            self.started = self.next_start
        self.next_start = self.started + self.args.time

    def _chk_slice_point(self):
        """
        chk_slice_time checks for the slice point
        of a segment eoither buy self.args.time
        self.maps.prgm_pts.items()or by self.scte35.cue_time
        """
        if self.scte35.cue_time:
            if self.now >= self.scte35.cue_time:
                self.next_start = self.now
                self._write_segment()
                self.scte35.cue_time = None
                self.scte35.mk_cue_state()
                return
        if self.now >= self.started + self.args.time:
            self.next_start = self.now
            self._write_segment()

    def _chk_cue_time(self, pid):
        """
        _chk_cue checks for SCTE-35 cues
        and inserts a tag at the time
        the cue is received.
        """
        if self.scte35.cue:
            self.scte35.cue_time = self.adjusted_pts(self.scte35.cue, pid)

    def adjusted_pts(self, cue, pid):
        """
        adjusted_pts = (pts_time + pts_adjustment) % self.ROLLOVER
        """
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
            self._chk_slice_point()

    def _parse_scte35(self, pkt, pid):
        """
        _parse_scte35 overrides the inherited
        Stream._parse_scte35 method
        """
        cue = super()._parse_scte35(pkt, pid)
        if cue:
            cue.decode()
            self.scte35.cue = cue
            self._chk_cue_time(pid)
            self.add2sidecar(f"{self.adjusted_pts(cue, pid)}, {cue.encode()}")
        return cue

    def _parse(self, pkt):
        """
        _parse is run on every packet.
        """
        super()._parse(pkt)
        pkt_pid = self._parse_pid(pkt[1], pkt[2])
        self.now = self.pid2pts(pkt_pid)
        if not self.started:
            self._start_next_start(pts=self.now)
        if self._pusi_flag(pkt) and self.started:
            if self.args.shulga:
                self._shulga_mode(pkt)
            else:
                i_pts = self.iframer.parse(pkt)
                if i_pts:
                    self.now = i_pts
                    self._chk_slice_point()
            self._load_sidecar(pkt_pid)
            self._chk_sidecar_cues(pkt_pid)
            # Split on non-Iframes for CUE-IN or CUE-OUT
            if self.scte35.cue_time:
                self._chk_slice_point()
        self.active_segment.write(pkt)

    def addendum(self):
        """
        addendum post stream parsing related tasks.
            * writing the last segment
            * sleeping to ensure last segment gets playing
            when the replay flag or continue_m3u8 flag is set.
            * adding endlist tag
        """
        buff = self.active_segment.getbuffer()
        if buff:
            self._write_segment()
            time.sleep(0.5)
        if not self.args.live:
            with open(self.m3u8uri(), "a", encoding="utf8") as m3u8:
                m3u8.write("#EXT-X-ENDLIST")

    def decode(self, func=False):
        """
        decode iterates mpegts packets
        and passes them to _parse.
        """
        self.timer.start()
        if (isinstance(self.args.input, str) and ("m3u8" in self.args.input)):
            self.decode_m3u8(self.args.input)
        else:
            super().decode()
        self.addendum()

    @staticmethod
    def _clean_line(line):
        if isinstance(line, bytes):
            line = line.decode(errors="ignore")
        line = line.replace("\n", "").replace("\r", "")
        return line

    def parse_m3u8_media(self, media):
        """
        parse_m3u8_media parse a segment from
        a m3u8 input file if it has not been parsed.
        """
        max_media = 200
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
                    line = self._clean_line(line)
                    if self._endlist(line):
                        return False
                    if line.startswith("#"):
                        media = None
                    else:
                        media = line
                    if media:
                        if base_uri not in media:
                            media = base_uri + media
                        self.parse_m3u8_media(media)


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
        self.seg_type = None

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
            return tag

        if self.cue_state == "IN":
            fstop = f',END-DATE="{iso8601}"'
            tag = f"{fbase}{fstop},SCTE35-IN={self.cue.encode_as_hex()}"
            self.event_id += 1
            return tag
        return False

    def _splice_insert_cue_out(self,cue):
        cmd = cue.command
        if cmd.out_of_network_indicator:
            if cmd.break_duration:
                self.break_duration = cmd.break_duration
            self.cue_state = "OUT"
            return True
        return False

    def _time_signal_cue_out(self,cue):
        seg_starts = [0x22, 0x30, 0x32, 0x34, 0x36, 0x44, 0x46]
        for dsptr in cue.descriptors:
            if dsptr.tag != 2:
                return
            if dsptr.segmentation_type_id in seg_starts:
                self.seg_type = dsptr.segmentation_type_id + 1
                if dsptr.segmentation_duration:
                    self.break_duration = dsptr.segmentation_duration
                    self.cue_state = "OUT"
                    return True
        return False

    def is_cue_out(self, cue):
        """
        is_cue_out checks a Cue instance
        to see if it is a cue_out event.
        Returns True for a cue_out event.
        """
        if cue is None:
            return False
        if self.cue_state not in ["IN", None]:
            return False
        cmd = cue.command
        if cmd.command_type == 5:
            return self._splice_insert_cue_out(cue)
        if cmd.command_type == 6:
            return self._time_signal_cue_out(cue)

        return False

    def is_cue_in(self, cue):
        """
        is_cue_in checks a Cue instance
        to see if it is a cue_in event.
        Returns True for a cue_in event.
        """
        if cue is None:
            return False
        if self.cue_state not in ["OUT", "CONT"]:
            return False
        cmd = cue.command
        if cmd.command_type == 5:
            if not cmd.out_of_network_indicator:
                return True
        if cmd.command_type == 6:
            for dsptr in cue.descriptors:
                if dsptr.tag == 2:
                    if dsptr.segmentation_type_id == self.seg_type:
                        self.seg_type = None
                        self.cue_state = "IN"
                        return True
        return False


class SlidingWindow:
    """
    The SlidingWindow class
    """
    def __init__(self, size=10000):
        self.size = size
        self.panes = deque()
        self.delete = False

    def popleft_pane(self):
        """
        popleft_pane removes the first item in self.panes
        """
        popped = self.panes.popleft()
        if self.delete:
            try:
                os.unlink(popped.name)
            except:
                pass

    def push_pane(self, a_pane):
        """
        push appends a_pane to self.panes
        """
        self.panes.append(a_pane)

    def all_panes(self):
        """
        all_panes returns the current window panes joined.
        """
        return "".join([a_pane.get() for a_pane in self.panes])

    def slide_panes(self, a_pane=None):
        """
        slide calls self.push_pane with a_pane
        and then calls self.popleft_pane to trim self.panes
        as needed.
        """
        if a_pane:
            self.push_pane(a_pane)
        if len(self.panes) > self.size:
            self.popleft_pane()



class Timer:
    """
    Timer class instances are used for
    segment duration, and live throttling.
    """
    def __init__(self):
        self.begin = None
        self.end = None
        self.lap_time = None

    def start(self, begin=None):
        """
        start starts the timer
        """
        self.begin = begin
        if not self.begin:
            self.begin = time.time()
        self.end = None
        self.lap_time = None

    def stop(self, end=None):
        """
        stop stops the timer
        """
        self.end = end
        if not self.end:
            self.end = time.time()
        self.lap_time = self.end - self.begin

    def elapsed(self, now=None):
        """
        elapsed returns the elapsed time
        """
        if not now:
            now = time.time()
        return now - self.begin

    def throttle(self, seg_time, begin=None, end=None):
        """
        throttle is called to slow segment creation
        to simulate live streaming.
        """
        self.stop(end)
        diff = round(seg_time - self.lap_time, 2)
        if diff > 0:
            print2(f"throttling {diff}")
            time.sleep(diff)
        self.start(begin)


class Chunk:
    """
    Class to hold hls segment tags
    for a segment.
    """
    def __init__(self, file, name, num):
        self.tags = {}
        self.file = file
        self.name = name
        self.num = num

    def get(self):
        """
        get returns the Chunk data formated.
        """
        this = []
        for kay, vee in self.tags.items():
            if vee is None:
                this.append(kay)
            else:
                this.append(f"{kay}:{vee}")
        this.append(self.file)
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
        help=""" Input source, like /home/a/vid.ts
                                or udp://@235.35.3.5:3535
                                or https://futzu.com/xaa.ts
                                or https://example.com/not_a_master.m3u8
                                [default: stdin]
                                """,
    )
    parser.add_argument(
        "-c",
        "--continue_m3u8",
        action="store_const",
        default=False,
        const=True,
        help="Resume writing index.m3u8 [default:False]",
    )
    parser.add_argument(
        "-d",
        "--delete",
        action="store_const",
        default=False,
        const=True,
        help="delete segments (enables --live) [default:False]",
    )
    parser.add_argument(
        "-l",
        "--live",
        action="store_const",
        default=False,
        const=True,
        help="Flag for a live event (enables sliding window m3u8) [default:False]",
    )
    parser.add_argument(
        "-n",
        "--no_discontinuity",
        action="store_const",
        default=False,
        const=True,
        help="Flag to disable adding #EXT-X-DISCONTINUITY tags at splice points [default:False]",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        default=".",
        help="""Directory for segments and index.m3u8
                (created if needed) [default:'.'] """,
    )
    parser.add_argument(
        "-p",
        "--program_date_time",
        action="store_const",
        default=False,
        const=True,
        help="Flag to add Program Date Time tags to index.m3u8 ( enables --live) [default:False]",
    )
    parser.add_argument(
        "-r",
        "--replay",
        action="store_const",
        default=False,
        const=True,
        help="""Flag for replay aka looping
        (enables --live,--delete) [default:False]
        """,
    )
    parser.add_argument(
        "-s",
        "--sidecar_file",
        default=None,
        help="""Sidecar file of SCTE-35 (pts,cue) pairs.[default:None]""",
    )
    parser.add_argument(
        "-S",
        "--shulga",
        action="store_const",
        default=False,
        const=True,
        help="Flag to enable Shulga iframe detection mode [default:False]",
    )
    parser.add_argument(
        "-t",
        "--time",
        default=2,
        type=float,
        help="Segment time in seconds [default:2]",
    )
    parser.add_argument(
        "-T",
        "--hls_tag",
        default="x_cue",
        help="x_scte35, x_cue, x_daterange, or x_splicepoint [default:x_cue]",
    )

    parser.add_argument(
        "-w",
        "--window_size",
        default=5,
        type=int,
        help="sliding window size (enables --live) [default:5]",
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


def cli():
    """
    cli provides one function call for running X9K3.

     from X9K3 import cli
     cli()
    """
    args = argue()
    x9 = X9K3()
    x9.decode()
    while args.replay:
        x9 = X9K3()
        x9.continue_m3u8()
        x9.decode()


if __name__ == "__main__":
    cli()
