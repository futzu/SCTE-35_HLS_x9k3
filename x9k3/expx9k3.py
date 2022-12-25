import io
import sys
from chunk import Chunk
from new_reader import reader
from iframes import IFramer
from scte35 import SCTE35
from timer import Timer
from window import SlidingWindow

from threefive import Stream


class ExpX9K3(Stream):
    def __init__(self, tsdata, show_null=False):
        super().__init__(tsdata, show_null)
        self.video = tsdata
        self.active_segment = io.BytesIO()
        self.iframer = IFramer()
        self.window = SlidingWindow(50)
        self.scte35 = SCTE35()
        self.packet_size = 188
        self.seconds = 2
        self.segnum = 0
        self.started = None
        self.next_start = None
        self.m3u8 = "index.m3u8"
        self.live = False
        self.media_seq = 0

    def _add_discontinuity(self):
        self.active_data.write("#EXT-X-DISCONTINUITY\n")

    def _header(self):
        bump = ""
        self.media_seq = self.window.panes[0].num
        head = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            f"#EXT-X-TARGETDURATION:{int(self.seconds+1)}",
            f"#EXT-X-MEDIA-SEQUENCE:{self.media_seq}",
        ]
        if not self.live:
            head.append("#EXT-X-PLAYLIST-TYPE:VOD")
        head.append(bump)
        return "\n".join(head)

    def add_cue_tag(self, chunk):
        tag = self.scte35.mk_cue_tag()
        print(tag)
        if tag:
            print(tag)
            kay = tag
            vee = ""
            if ":" in tag:
                kay, vee = tag.split(":", 1)
            chunk.add_tag(kay, vee)
            print(kay, vee)

    def _write_segment(self):
        seg_name = f"seg{self.segnum}.ts"
        seg_time = self.next_start - self.started

        with open(seg_name, "wb") as seg:
            seg.write(self.active_segment.getbuffer())
        chunk = Chunk(seg_name, self.segnum)
        # self.add_cue_tag(chunk)
        chunk.add_tag("#EXTINF", f"{seg_time:.6f},")
        print(chunk.get())
        self.window.slide_panes(chunk)
        self._write_m3u8()

    def _write_m3u8(self):
        with open(self.m3u8, "w+") as m3u8:
            m3u8.write(self._header())
            m3u8.write(self.window.all_panes())
            self.segnum += 1
            if not self.live:
                m3u8.write("#EXT-X-ENDLIST")
        self.active_segment = io.BytesIO()

    def _parse(self, pkt):
        super()._parse(pkt)
        pkt_pid = self._parse_pid(pkt[1], pkt[2])
        pkt_pts = self.pid2pts(pkt_pid)
        # print(pkt_pts)
        if not self.started:
            self.started = pkt_pts
        if not self.next_start:
            self.next_start = self.started + self.seconds
        i_pts = self.iframer.parse(pkt)
        if i_pts:
            if pkt_pts >= self.next_start or self.scte35.cue_time:
                self.next_start = pkt_pts
                self._write_segment()
                self.started = self.next_start
                self.next_start = self.started + self.seconds
        self.active_segment.write(pkt)

    def slicer(self):
        for pkt in self._find_start():
            self._parse(pkt)
        pid = self._parse_pid(pkt[1], pkt[2])
        self.next_start = self.pid2pts(pid)
        self._write_segment()


x9 = ExpX9K3(sys.argv[1])
x9.slicer()
