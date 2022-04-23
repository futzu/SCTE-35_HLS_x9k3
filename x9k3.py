#!/usr/bin/env python3

"""
X9K3
"""

import argparse
import io
import sys
from base64 import b64encode
from functools import partial
from threefive import Stream

# sliding window size
MEDIA_SLOTS = 10
# target segment time.
SECONDS = 2


class X9K3(Stream):
    """
    X9K3 class
    """

    def __init__(self, tsdata, show_null=False):
        """
        tsdata is an file or http/https url or multicast url
        set show_null=False to exclude Splice Nulls
        """
        super().__init__(tsdata, show_null)
        self.active_segment = io.BytesIO()
        self.active_data = io.StringIO()
        self.seg_num = 0
        self.seg_start = 0
        self.seg_stop = 0
        self.start = False
        self.scte35 = None
        self.queue = []
        self.live = False
        self.media_slot = 0
        self.header = None
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

    def mk_header(self):
        """
        header generates the m3u8 header lines
        """
        m3u = "#EXTM3U"
        version = "#EXT-X-VERSION:3"
        target = f"#EXT-X-TARGETDURATION:{SECONDS+SECONDS}"
        #  seq = f"#EXT-X-MEDIA-SEQUENCE:{self.seg_num}"
        self.header = "\n".join((m3u, version, target, ""))

    def decode(self, func=None):
        """
        decode reads self.tsdata to cut hls segments.
        """
        if self._find_start():
            for chunk in iter(partial(self._tsdata.read, self._PACKET_SIZE), b""):
                self._parse(chunk)

    def _chk_cue(self, pkt, pid):
        """
        _chk_cue checks for SCTE-35 cues
        and inserts a tag at the time
        the cue is received.
        """
        if pid in self._pids["scte35"]:
            self.cue = self._parse_scte35(pkt, pid)
            if self.cue:
                self.active_data.write(f"# {self.cue.command.name}\n")
                if self.cue.command.pts_time:
                    self.cue_time = self.cue.command.pts_time
                    print(f"Preroll: {self.cue.command.pts_time- self.pid2pts(pid)} ")
                else:
                    self.cue_time = self.pid2pts(pid)
                    self.active_data.write("# Splice Immediate\n")
                self.cue_tag = self.mk_cue_tag(self.cue)
                self.cue_out = None

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

    def _mk_cue_splice_point(self):
        """
        _mk_cue_splice_point inserts a tag
        at the time specified in the cue.

        """
        self.cue_tag = self.mk_cue_tag(self.cue)
        print(f"# Splice Point @ {self.cue_time}\n")
        self.active_data.write(f"# Splice Point @ {self.cue_time}\n")
        self.cue_out_cue_in()
        if self.cue_out is None:
            self.cue_time = None
        self.active_data.write(self.cue_tag + "\n")
        self.cue_tag = None

    def _write_segment(self):
        if not self.start:
            return
        if self.seg_stop:
            print(self.seg_start, self.seg_stop)
            seg_file = f"seg{self.seg_num}.ts"
            seg_time = round(self.seg_stop - self.seg_start, 6)
            if self.live:
                # print("CUE in Slot", self.media_slot)
                if self.cue_out == "CONT":
                    self.media_slot += 1
                    if self.media_slot == MEDIA_SLOTS - 1:
                        self.media_slot = 0
                    if self.media_slot == 0:
                        self.cue_tag = self.mk_cue_tag(self.cue)
                        self.cue_tag += ",CUE-OUT=CONT"
            if self.cue_tag:
                self.active_data.write(self.cue_tag + "\n")
                print(self.cue_tag)
                self.cue_tag = None
            with open(seg_file, "wb+") as seg:
                seg.write(self.active_segment.getbuffer())
            self.active_data.write(f"#EXTINF:{seg_time},\n")
            self.active_data.write(seg_file + "\n")
            print(f"{seg_file}: {seg_time }")
            self.seg_start = self.seg_stop
            self.seg_stop += SECONDS
            self.seg_num += 1
            self.queue.append(self.active_data.getvalue())

    def _write_manifest(self):
        if self.live:
            self.queue = self.queue[-(MEDIA_SLOTS):]
        with open("index.m3u8", "w+", encoding="utf-8") as mufu:
            mufu.write(self.header)
            self.mk_header()
            for i in self.queue:
                mufu.write(i)
            if not self.live:
                mufu.write("#EXT-X-ENDLIST")
        self.active_data = io.StringIO()
        self.active_segment = io.BytesIO()

    def _mk_segment(self, pid):
        """
        _mk_segment cuts hls segments
        """
        if self.cue_time:
            if self.seg_start < self.cue_time < self.seg_stop:
                self.seg_stop = self.cue_time
                # print("self.seg_stop: ", self.seg_stop)
                self._mk_cue_splice_point()
                self.cue_time = None
        now = self.pid2pts(pid)
        if now >= self.seg_stop:
            self.seg_stop = now
            self._write_segment()
            self._write_manifest()

    def _is_key(self, pkt):
        """
        _is_key is fast and loose key frame detection.

        """
        # standard nal idr
        if b"\x00\x00\x01\x65" in pkt:
            return True
        if not self._afc_flag(pkt):
            return False
        if self._pcr_flag(pkt):
            if pkt[5] & 0x40:
                return True
        # ABC
        if pkt[5] & 0xA8:
            return True
        return False

    @staticmethod
    def as_90k(ticks):
        """
        as_90k returns ticks as 90k clock time
        """
        return round((ticks / 90000.0), 6)

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
            if self.start:
                if not self.seg_start:
                    self.seg_start = self.as_90k(pts)
                    self.seg_stop = self.seg_start + SECONDS

    def pid2prgm(self, pid):
        """
        pid2prgm takes a pid,
        returns the program
        """
        prgm = 1
        if pid in self._pid_prgm:
            prgm = self._pid_prgm[pid]
        return prgm

    def pid2pts(self, pid):
        """
        pid2pts takes a pid
        return current pts
        """
        prgm = self.pid2prgm(pid)
        if prgm not in self._prgm_pts:
            return False
        return self.as_90k(self._prgm_pts[prgm])

    def _parse(self, pkt):
        """
        _parse parses mpegts and
        writes the packet to self.active_segment.
        """
        self.mk_header()
        pid = self._parse_info(pkt)
        self._chk_cue(pkt, pid)
        if self._pusi_flag(pkt):
            self._parse_pts(pkt, pid)
            if self._is_key(pkt):
                self._mk_segment(pid)
                if not self.start:
                    self.start = True
        if self.start:
            self.active_segment.write(pkt)


def parse_args():
    """
    parse_args parse command line args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
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

    if len(sys.argv) > 1:
        args = parse_args()
        x9k3 = X9K3(args.input)
        x9k3.live = args.live
        x9k3.decode()

    else:
        # for piping in video
        X9K3(sys.stdin.buffer).decode()
