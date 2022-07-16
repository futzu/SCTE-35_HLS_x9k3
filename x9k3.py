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
from functools import partial
from threefive import Stream

MAJOR = "0"
MINOR = "0"
MAINTAINENCE = "99"


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
    def __init__(self):
        self.start_seg_num = 0
        self.seg_num = 0
        self.seg_start = 0
        self.seg_stop = 0
        self.cue = None
        self.cue_out = None
        self.cue_tag = None
        self.cue_time = None


class X9K3(Stream):
    """
    X9K3 class
    """

    # sliding window size
    MEDIA_SLOTS = 25
    # target segment time.
    SECONDS = 2

    def __init__(self, tsdata, show_null=False):
        """
        __init__ for X9K3
        tsdata is an file or http/https url or multicast url
        set show_null=False to exclude Splice Nulls
        """
        super().__init__(tsdata, show_null)
        self.active_segment = io.BytesIO()
        self.active_data = io.StringIO()
        self.start = False
        self.scte35 = None
        self.media_slots = []
        self.media_slot = 0
        self.header = None
        self.live = False
        self.output_dir = "."
        self.delete_segs = False
        self.seg = SegData()

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

    def _mk_header(self):
        """
        header generates the m3u8 header lines
        """
        m3u = "#EXTM3U"
        m3u_version = "#EXT-X-VERSION:3"
        m3u_cache = "#EXT-X-ALLOW-CACHE:YES"
        plt = "VOD"
        if self.live:
            plt = "EVENT"
        play_type = f"#EXT-X-PLAYLIST-TYPE:{plt}"
        target = f"#EXT-X-TARGETDURATION:{self.SECONDS+self.SECONDS}"
        seq = f"#EXT-X-MEDIA-SEQUENCE:{self.seg.start_seg_num}"
        self.header = "\n".join(
            (m3u, m3u_version, m3u_cache, play_type, target, seq, "")
        )

    def _chk_cue(self, pkt, pid):
        """
        _chk_cue checks for SCTE-35 cues
        and inserts a tag at the time
        the cue is received.
        """
        if pid in self._pids["scte35"]:
            self.seg.cue = self._parse_scte35(pkt, pid)
            if self.seg.cue:
                self.seg.cue.show()
                print(f"{self.seg.cue.command.name}")
                self.active_data.write(f"# {self.seg.cue.command.name}\n")
                if self.seg.cue.command.pts_time:
                    self.seg.cue_time = self.seg.cue.command.pts_time
                    print(
                        f"Preroll: {round(self.seg.cue.command.pts_time- self.pid2pts(pid), 6)} "
                    )
                else:
                    self.seg.cue_time = self.pid2pts(pid)
                    self.active_data.write("# Splice Immediate\n")
                self.seg.cue_tag = self.mk_cue_tag(self.seg.cue)
                self.seg.cue_out = None

    def cue_out_cue_in(self):
        """
        cue_out_cue_in adds CUE-OUT
        and CUE-IN attributes to hls scte35 tags
        """
        if self.is_cue_out(self.seg.cue):
            self.seg.cue_tag += ",CUE-OUT=YES"
            self.seg.cue_out = "CONT"
        if self.is_cue_in(self.seg.cue):
            self.seg.cue_tag += ",CUE-IN=YES"
            self.seg.cue_out = None

    def _mk_cue_splice_point(self):
        """
        _mk_cue_splice_point inserts a tag
        at the time specified in the cue.

        """
        self.seg.cue_tag = self.mk_cue_tag(self.seg.cue)
        print(f"Splice Point {self.seg.cue.command.name}@{self.seg.cue_time}")
        self.active_data.write(f"# Splice Point @ {self.seg.cue_time}\n")
        self.cue_out_cue_in()
        if self.seg.cue_out is None:
            self.seg.cue_time = None
        self.active_data.write(self.seg.cue_tag + "\n")
        self.seg.cue_tag = None

    def cue_out_continue(self):
        """
        cue_out_continue ensures that
        if there is an active SCTE35 cue,
        the live sliding window of segments
        has a tag with CUE-OUT=CONT

        """
        if self.media_slot > self.MEDIA_SLOTS:
            self.media_slot = 0
        if self.seg.cue_out == "CONT" and self.media_slot == 0:
            self.seg.cue_tag = self.mk_cue_tag(self.seg.cue)
            self.seg.cue_tag += ",CUE-OUT=CONT"
        self.media_slot += 1

    def _write_segment(self):
        if not self.start:
            return
        if self.seg.seg_stop:
            seg_file = f"seg{self.seg.seg_num}.ts"
            seg_uri = self.mk_uri(self.output_dir, seg_file)
            seg_time = round(self.seg.seg_stop - self.seg.seg_start, 3)
            if self.live:
                self.cue_out_continue()
            if self.seg.cue_tag:
                self.active_data.write(self.seg.cue_tag + "\n")
                self.seg.cue_tag = None
            with open(seg_uri, "wb+") as seg:
                seg.write(self.active_segment.getbuffer())
                seg.flush()
            del self.active_segment
            self.active_data.write(f"#EXTINF:{seg_time},\n")
            self.active_data.write(seg_file + "\n")
            print(
                f"{time.ctime()} -> {seg_file}  \tstart: {self.seg.seg_start:.6f}\tduration: {seg_time:.3f}"
            )
            self.seg.seg_start = self.seg.seg_stop
            self.seg.seg_stop += self.SECONDS
            self.media_slots.append((self.seg.seg_num, self.active_data.getvalue()))
            self.seg.seg_num += 1

    def _open_m3u8(self):
        m3u8_uri = self.mk_uri(self.output_dir, "index.m3u8")
        return open(m3u8_uri, "w+", encoding="utf-8")

    def _write_manifest(self):
        if self.live:
            if len(self.media_slots) > self.MEDIA_SLOTS:
                if self.delete_segs:
                    drop = self.mk_uri(
                        self.output_dir, self.media_slots[0][1].rsplit(",")[1].strip()
                    )
                    os.unlink(drop)
                    print(f"deleting {drop}")
                self.media_slots = self.media_slots[1:]
            self.seg.start_seg_num = self.media_slots[0][0]
        with self._open_m3u8() as m3u8:
            self._mk_header()
            m3u8.write(self.header)
            for i in self.media_slots:
                m3u8.write(i[1])
            if not self.live:
                m3u8.write("#EXT-X-ENDLIST")
        self.active_data = io.StringIO()
        self.active_segment = io.BytesIO()

    def _mk_segment(self, pid):
        """
        _mk_segment cuts hls segments
        """
        if self.seg.cue_time:
            if self.seg.seg_start < self.seg.cue_time < self.seg.seg_stop:
                self.seg.seg_stop = self.seg.cue_time
                self._mk_cue_splice_point()
                self.seg.cue_time = None
        now = self.pid2pts(pid)
        if now >= self.seg.seg_stop:
            self.seg.seg_stop = now
            self._write_segment()
            self._write_manifest()

    @staticmethod
    def _rai_flag(pkt):
        return pkt[5] & 0x40

    @staticmethod
    def _abc_flags(pkt):
        """
        0x80, 0x20, 0x8
        """
        return pkt[5] & 0xA8

    @staticmethod
    def _is_sps(pkt):
        sps_start = b"\x00\x00\x01\x67"
        if sps_start in pkt:
            sps_idx = pkt.index(sps_start)
            profile = pkt[sps_idx + 4]
            level = pkt[sps_idx + 6]
            print(f"Profile {profile} Level {level}")

    def _is_key(self, pkt):
        """
        _is_key is key frame detection.

        """
        if b"\x00\x00\x01\x65" in pkt:
            return True
        if not self._afc_flag(pkt):
            return False
        if self._rai_flag(pkt):
            return True
        if self._abc_flags(pkt):
            return True
        return False

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
        self._chk_cue(pkt, pid)
        # self._is_sps(pkt)
        if self._pusi_flag(pkt):
            self._parse_pts(pkt, pid)
            if self._is_key(pkt):
                self._mk_segment(pid)
                if not self.start:
                    self.start = True
        self.active_segment.write(pkt)


def _parse_args():
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
                Directory is created if it does not exist""",
    )

    parser.add_argument(
        "-l",
        "--live",
        action="store_const",
        default=False,
        const=True,
        help="Flag for a live event.(enables sliding window m3u8)",
    )

    parser.add_argument(
        "-d",
        "--delete",
        action="store_const",
        default=False,
        const=True,
        help="delete segments (implies live mode)",
    )

    return parser.parse_args()


if __name__ == "__main__":

    args = _parse_args()
    if args.input:
        x9k3 = X9K3(args.input)
    else:
        # for piping in video
        x9k3 = X9K3(sys.stdin.buffer)
    if args.delete:
        args.live = True
    x9k3.live = args.live
    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)
    x9k3.output_dir = args.output_dir
    x9k3.delete_segs = args.delete
    x9k3.decode()
