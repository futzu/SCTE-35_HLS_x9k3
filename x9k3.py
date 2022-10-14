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
from base64 import b64encode
from collections import deque
from functools import partial
from operator import itemgetter
from new_reader import reader
from threefive import Stream, Cue
from iframes import IFramer

MAJOR = "0"
MINOR = "1"
MAINTAINENCE = "45"


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
        self.cue_tag = None
        self.cue_time = None
        self.tag_method = self.x_cue
        self.break_timer = None
        self.break_duration = None
        self.event_id =1

    def mk_cue_tag(self):
        """
        mk_cue_tag
        """
        if self.cue:
            return self.tag_method()
        return False


    def x_cue(self):
        if self.cue_out == "OUT":
            self.break_timer = 0
            return f'#EXT-X-CUE-OUT:{self.break_duration}'
        if self.cue_out == "IN":
            self.break_timer= None
            return f"#EXT-X-CUE-IN"
        if self.cue_out == "CONT":
            return (
                f"#EXT-X-CUE-OUT-CONT:{self.break_timer:.6f}/{self.break_duration}"
            )
        return False

    def x_splicepoint(self):
        base = f"#EXT-X-SPLICEPOINT-SCTE35:{self.cue.encode()}"
        if self.cue_out == "OUT":
            return f"{base}"
        if self.cue_out == "IN":
            return f"{base}"
        return False

    def x_scte35(self):
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
        #EXT-X-DATERANGE:ID="187",START-DATE="2018-09-11T21:44:00Z"
        ,PLANNED-DURATION=24,
        SCTE35-OUT=0xFC302100000000000000FFF010050
        """
        fbase = f'#EXT-X-DATERANGE:ID="{self.event_id}"'
        iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
        fdur=""
        if self.break_duration:
            fdur=f',PLANNED-DURATION={self.break_duration}'
        
        if self.cue_out == "OUT":
                    self.break_timer = 0
                    fstart = f',START-DATE="{iso8601}"'
                    tag = f'{fbase}{fstart}{fdur},SCTE35-OUT={self.cue.encode_as_hex()}'
                    self.event_id +=1
                    return tag
                    
        if self.cue_out == "IN":
                    self.break_timer = None
                    fstop = f',END-DATE="{iso8601}"'
                    tag =  f'{fbase}{fstop},SCTE35-IN={self.cue.encode_as_hex()}'
                    self.event_id +=1
                    return tag

        return False


        
    def is_cue_out(self,cue):
        """
        is_cue_out checks a Cue instance
        to see if it is a cue_out event.
        Returns True for a cue_out event.
        """
        cmd =cue.command
        if cmd.command_type == 5:
            if cmd.out_of_network_indicator:
                if cmd.break_duration:
                    self.break_duration= cmd.break_duration
                    self.break_timer= 0
                    return True

        upid_starts=[0x10,0x20,0x22,0x30,0x32,0x34,0x36,0x38,0x3a,0x3c,0x3e,0x44,0x46]               
        if cmd.command_type ==6:
            for d in cue.descriptors:
                if d.tag ==2:
                    if d.segmentation_type_id in upid_starts:
                        if d.segmentation_duration:
                            self.break_duration= d.segmentation_duration
                            self.break_timer =0
                            return True
                
        return False

    def is_cue_in(self,cue):
        """
        is_cue_in checks a Cue instance
        to see if it is a cue_in event.
        Returns True for a cue_in event.
        """
        cmd = cue.command
        if cmd.command_type == 5:
            if not cmd.out_of_network_indicator:
                self.break_duration = None
                self.break_timer =None
                return True
            
        upid_stops = [0x11,0x21,0x21,0x23,0x33,0x35,0x37,0x39,0x3b,0x3d,0x3f,0x45,0x47]
        if cmd.command_type ==6:
            for d in cue.descriptors:
                if d.tag ==2:
                    if d.segmentation_type_id in upid_stops:
                        self.break_duration = None
                        self.break_timer =None
                        return True                

        return False

    def cue_out_cue_in(self):
        """
        cue_out_cue_in adds CUE-OUT
        and CUE-IN attributes to hls scte35 tags
        """
        if self.cue:
            if self.is_cue_out(self.cue):
                self.cue_out = "CONT"
            if self.is_cue_in(self.cue):
                self.cue_out = None


class X9K3(Stream):
    """
    X9K3 class
    """

    # sliding window size
    WINDOW_SLOTS = 5
    __slots__ = [
        "_tsdata",
        "start",
        "window_slot",
        "header",
        "live",
        "output_dir",
        "delete",
        "sidecar",
        "seconds",
        "replay",
    ]

    def __init__(self, tsdata=None, show_null=False):
        """
        __init__ for X9K3
        tsdata is an file or http/https url or multicast url
        set show_null=False to exclude Splice Nulls
        """
        super().__init__(tsdata, show_null)
        self._tsdata = tsdata
        self.in_stream = tsdata
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
        self.sidecar_file = None
        self.sidecar = None
        self.seconds = 2
        self.replay = False
        self._parse_args()
        self.iframer = IFramer(shush=True)

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
            
            "--hls_tag",
            default="x_cue",
            help="""hls tag  can be x_scte35, x_cue, x_daterange, or x_splicepoint """,
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
            help="delete segments ( enables --live )",
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
        else:
            self._tsdata = sys.stdin.buffer

    def _args_hls_tag(self,args):
        tag_map ={"x_scte35": self.scte35.x_scte35,
                              "x_cue":self.scte35.x_cue,
                              "x_daterange":self.scte35.x_daterange,
                              "x_splicepoint":self.scte35.x_splicepoint}
        if args.hls_tag not in  tag_map:
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

    def _apply_args(self, args):
        """
        _apply_args  uses command line args
        to set X9K3 instance vars
        """
        self._args_version(args)
        self._args_input(args)
        self._args_hls_tag(args)
        self._args_output_dir(args)
        self._args_sidecar(args)
        self._args_time(args)
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
        headers = [m3u, m3u_version]
        if not self.live:
            play_type = "#EXT-X-PLAYLIST-TYPE:VOD"
            headers.append(play_type)
        target = f"#EXT-X-TARGETDURATION:{int(self.seconds+1)}"
        headers.append(target)
        seq = f"#EXT-X-MEDIA-SEQUENCE:{self.seg.start_seg_num}"
        headers.append(seq)
        bumper = ""
        headers.append(bumper)
        self.header = "\n".join(headers)

    def load_sidecar(self, file, pid):
        """
        load_sidecar reads (pts, cue) pairs from
        the sidecar file and loads them into X9K3.sidecar
        """
        if self.sidecar_file:
            with reader(file) as sidefile:
                for line in sidefile:
                    line = line.decode().strip().split("#", 1)[0]
                    if len(line):
                        pts, cue = line.split(",", 1)
                        if float(pts) >= self.pid2pts(pid):
                            if [float(pts), cue] not in self.sidecar:
                                self.sidecar.append([float(pts), cue])
                                self.sidecar = deque(
                                    sorted(self.sidecar, key=itemgetter(0))
                                )

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
                # self.scte35.cue_tag = self.scte35.mk_cue_tag(self.scte35.cue)
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
        self.seg.seg_start = None
        self.seg.seg_stop = None

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
            self.scte35.cue_out = None

        else:
            self.scte35.cue_time = self.pid2pts(pid)
            self.active_data.write("# Splice Immediate\n")
            self._mk_cue_splice_point()

    def _mk_cue_splice_point(self):
        """
        _mk_cue_splice_point inserts a tag
        at the time specified in the cue.
        """
        if self.scte35.cue:
            self._add_discontinuity()
            print(f"Splice Point {self.scte35.cue.command.name}@{self.scte35.cue_time}")
            self.active_data.write(f"# Splice Point @ {self.scte35.cue_time}\n")
            if self.scte35.is_cue_in(self.scte35.cue):
                self.scte35.cue_out = "IN"
            if self.scte35.is_cue_out(self.scte35.cue):
                self.scte35.cue_out = "OUT"

            #    self.scte35.cue_out_cue_in()
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
        self.window_slot = self.window_slot % (self.WINDOW_SLOTS + 1)
        print(self.window_slot)

    def _mk_segment(self, pid):
        """
        _mk_segment cuts hls segments
        """
        now = self.pid2pts(pid)
        if self.scte35.cue_time:
            if self.seg.seg_start < self.scte35.cue_time < now:
                self.seg.seg_stop = self.scte35.cue_time
                self._mk_cue_splice_point()
                self.scte35.cue_time = None
        if self.seg.seg_stop:
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

            cue_tag = self.scte35.mk_cue_tag()
            if cue_tag:
                self.active_data.write(cue_tag + "\n")
            if self.scte35.break_duration:     
                self.scte35.break_timer +=self.seg.seg_time
            self.active_data.write(f'#PTS {round(self.seg.seg_start, 6)}\n')

            with open(self.seg.seg_uri, "wb+") as a_seg:
                a_seg.write(self.active_segment.getbuffer())
                a_seg.flush()
            del self.active_segment
            self.active_data.write(f"#EXTINF:{self.seg.seg_time},\n")
            self.active_data.write(seg_file + "\n")
            self.seg.seg_start = self.seg.seg_stop
            self.seg.seg_stop += self.seconds
            self.window.append(
                (self.seg.seg_num, self.seg.seg_uri, self.active_data.getvalue())
            )
            self.seg.seg_num += 1
            if self.scte35.cue_out == "OUT":
                self.scte35.cue_out = "CONT"
            if self.scte35.cue_out == "IN":
                self.scte35.cue_out = None
                self.scte35.cue = None
                self.scte35.cue_time = None
            # self.scte35.cue_out_cue_in()
            if self.live:
                self.cue_out_continue()

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
            self._parse_pts(pkt, pid)
            if self.iframer.parse(pkt):
                #      self.sps.is_sps(pkt)
                self.load_sidecar(self.sidecar_file, pid)
                self._mk_segment(pid)
                if not self.start:
                    self.start = True
        if self.start:
            self.active_segment.write(pkt)

    def loop(self):
        """
        loop  loops a video in the hls manifest.
        sliding window and throttled to simulate live playback,
        segments are deleted when they fall out the sliding window.
        """
        if not self._find_start():
            return False
        _ = [
            self._parse(pkt)
            for pkt in iter(partial(self._tsdata.read, self._PACKET_SIZE), b"")
        ]
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
    usage: x9k3.py [-h] [-i INPUT] [--hls_tag HLS_TAG] [-o OUTPUT_DIR] [-s SIDECAR] [-t TIME] [-l] [-d] [-r] [-v]

    Two lines of code gives you a full X9K3 command line tool.

     from X9K3 import cli
     cli()

    """
    stuff = X9K3()
    stuff.run()


if __name__ == "__main__":
    x9k = X9K3()
    x9k.run()
