"""
X9K3
"""
from base64 import b64encode

import io
import sys
from functools import partial
from threefive import Stream


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
        self.seconds = 2
        self.seg_num = 0
        self.seg_start = 0
        self.seg_stop = 0
        self.start = False
        self.cue_out = None
        self.cue = None
        self.cue_tag = None
        self.cue_time = None
        self.b64 = None
        self.m3u8 = open("index.m3u8", "w+")
        self.m3u8.write(self.header() + "\n")

    def header(self):
        """
        header generates the m3u8 header lines
        """
        m3u = "#EXTM3U"
        version = "#EXT-X-VERSION:3"
        target = f"#EXT-X-TARGETDURATION:{self.seconds+1}"
        seq = f"#EXT-X-MEDIA-SEQUENCE:{self.seg_num}"
        return "\n".join((m3u, version, target, seq))

    def decode(self, func=None):
        """
        decode reads self.tsdata to cut hls segments.
        """
        if self._find_start():
            for chunk in iter(partial(self._tsdata.read, self._PACKET_SIZE), b""):
                self._parse(chunk)
        self.m3u8.write("#EXT-X-ENDLIST")
        self.m3u8.close()

    def _mk_tag(self):
        print(self.b64)
        self.cue_tag = f'#EXT-X-SCTE35:CUE="{self.b64}" '

    def _chk_cue(self, pkt, pid):
        """
        _chk_cue checks for SCTE-35 cues
        and inserts a tag at the time
        the cue is received.
        """
        if pid in self._pids["scte35"]:
            self.cue = self._parse_scte35(pkt, pid)
            if self.cue:
                self.b64 = b64encode(self.cue.bites).decode()
                self.m3u8.write(f"# {self.cue.command.name}\n")
                if self.cue.command.pts_time:
                    self.cue_time = self.cue.command.pts_time
                    print(f"preroll: {self.cue.command.pts_time- self.pid2pts(pid)} ")
                else:
                    self.cue_time = self.pid2pts(pid)
                    self.m3u8.write("# Splice Immediate\n")
                self._mk_tag()
                self.cue_out = None

    def _cue_out_cue_in(self):
        if self.cue.command.command_type == 5:
            if self.cue.command.out_of_network_indicator:
                self.cue_tag += ",CUE-OUT=YES"
            else:
                self.cue_tag += ",CUE-IN=YES"

    def _mk_cue_splice_point(self):
        """
        _mk_cue_splice_point inserts a tag
        at the time specified in the cue.

        """
        if self.cue_time <= self.seg_stop:
            self._mk_tag()
            print(f"# Splice Point @ {self.cue_time}\n")
            self.m3u8.write(f"# Splice Point @ {self.cue_time}\n")
            self._cue_out_cue_in()
            self.cue = None
            self.cue_time = None
            self.cue_out = None
            self.m3u8.write(self.cue_tag + "\n")
            self.cue_tag = None

    def _mk_segment(self, pid):
        """
        _mk_segment cuts hls segments
        """
        now = self.pid2pts(pid)
        if self.cue_time:
            print("self.cue_time: ", self.cue_time)
            if self.seg_start < self.cue_time < self.seg_stop:
                self.seg_stop = self.cue_time
                print("self.seg_stop: ", self.seg_stop)
                self._mk_cue_splice_point()
                self.cue_time = None
        if now >= self.seg_stop:
            self.seg_stop = now
            print(self.seg_start, self.seg_stop)
            seg_file = f"seg{self.seg_num}.ts"
            seg_time = round(self.seg_stop - self.seg_start, 6)
            if self.cue_tag:
                self.m3u8.write(self.cue_tag + "\n")
                self.cue_tag = None
            with open(seg_file, "wb+") as seg:
                seg.write(self.active_segment.getbuffer())
            self.m3u8.write(f"#EXTINF:{seg_time},\n")
            # self.m3u8.write(f"# Segment Ends @  {self.seg_stop}\n")
            self.m3u8.write(seg_file + "\n")
            print(f"{seg_file}: {seg_time }")
            self.seg_start = now
            self.seg_stop = self.seg_start + self.seconds
            self.seg_num += 1
            self.active_segment = io.BytesIO()

    @staticmethod
    def _is_key(pkt):
        """
        _is_key is fast and loose keyframe detection
        """
        if not pkt[3] & 0x20:
            return False
        if pkt[5] & 0x10:
            if pkt[5] & 0x40:
                return True
        if pkt[5] & 0xA8:
            return True
        return False

    @staticmethod
    def _is_idr(pkt):
        """
        _is_idr is fast and loose idr detection
        """
        if b"\x00\x00\x01\x65" in pkt:
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
        parse pts and store by program key
        in the dict Stream._pid_pts
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
            if not self.start:
                self.start = True
                self.seg_start = self.as_90k(pts)
                self.seg_stop = self.seg_start + self.seconds
                self.m3u8.write(f"# STARTED @ {self.seg_start}\n")

    def pid2prgm(self, pid):
        prgm = 1
        if pid in self._pid_prgm:
            prgm = self._pid_prgm[pid]
        return prgm

    def pid2pts(self, pid):
        """
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
        pid = self._parse_info(pkt)
        self._chk_cue(pkt, pid)
        if self._pusi_flag(pkt):
            self._parse_pts(pkt, pid)
        if self._is_key(pkt):
            self._mk_segment(pid)
        if self._is_idr(pkt):
            self._mk_segment(pid)
        if self.start:
            self.active_segment.write(pkt)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            print(f"video stream: {arg}\n")
            X9K3(arg).decode()

    else:
        # for piping in video
        X9K3(sys.stdin.buffer).decode()
