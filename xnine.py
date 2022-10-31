import io
import sys
import time
from functools import partial
from new_reader import reader
from iframes import IFramer
from collections import deque


class Timer:
    def __init__(self):
        self.begin = None
        self.end = None
        self.lap_time = None

    def start(self):
        self.begin = time.time()
        self.end = None
        self.lap_time = None

    def stop(self):
        self.end = time.time()
        self.lap_time = self.end - self.begin

    def elapsed(self):
        return time.time() - self.begin

    def throttle(self, seg_time):
        self.stop()
        diff = round(seg_time - self.lap_time, 2)
        if diff > 0:
            print(f"throttling {diff}")
            time.sleep(diff)
        self.start()


class Chunk:
    def __init__(self, name, num):
        self.tags = {}
        self.name = name
        self.num = num

    def get(self):
        me = [f"{k}:{v}" for k, v in self.tags.items()]
        me.append(self.name)
        me.append("")
        me = "\n".join(me)
        return me

    def add_tag(self, quay, val):
        self.tags[quay] = val


class SlidingWindow:
    def __init__(self, size):
        self.size = size
        self.queue = deque()

    def pop(self):
        if len(self.queue) >= self.size:
            self.queue.popleft()

    def plus(self, chunk):
        self.queue.append(chunk)
        print([chunk.name for chunk in list(self.queue)])

    def get(self):
        return "".join([chunk.get() for chunk in self.queue])


class XNine:
    def __init__(self):
        self.active_segment = io.BytesIO()
        self.iframer = IFramer()
        self.window = SlidingWindow(5)
        self.packet_size = 188
        self.seconds = 2
        self.segnum = 0
        self.start_time = None
        self.end_time = None
        self.m3u8 = "index.m3u8"
        self.live = True
        self.media_seq = 0

    def _header(self):
        self.media_seq = self.window.queue[0].num
        head = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            f"#EXT-X-TARGETDURATION:{int(self.seconds+1)}",
            f"#EXT-X-MEDIA-SEQUENCE:{self.media_seq}",
            "",
        ]
        if not self.live:
            head.append("#EXT-X-PLAYLIST-TYPE:VOD")
        return "\n".join(head)

    def _mk_start_end(self, i_pts):
        self.start_time = i_pts
        self.end_time = i_pts + self.seconds

    def _write_segment(self, seg_time):
        seg_name = f"seg{self.segnum}.ts"
        with open(seg_name, "wb") as seg:
            seg.write(self.active_segment.getbuffer())
        chunk = Chunk(seg_name, self.segnum)
        chunk.add_tag("#EXTINF", f"{seg_time:.6f},")
        print(chunk.get())
        self.window.plus(chunk)
        self._write_m3u8()

    def _write_m3u8(self):
        with open(self.m3u8, "w+") as m3u8:
            m3u8.write(self._header())
            m3u8.write(self.window.get())
            self.segnum += 1
            if self.live:
                self.window.pop()
            else:
                m3u8.write("#EXT-X-ENDLIST")
        self.active_segment = io.BytesIO()

    def _parse(self, i_pts, timer):
        if not self.start_time:
            self.start_time = i_pts
            timer.start()
            self._mk_start_end(i_pts)
        if i_pts >= self.end_time:
            seg_time = i_pts - self.start_time
            self._write_segment(seg_time)
            self._mk_start_end(i_pts)
            if self.live:
                timer.throttle(seg_time)

    def slice(self, video):
        with reader(video) as video:
            timer = Timer()
            for pkt in iter(partial(video.read, self.packet_size), b""):
                i_pts = self.iframer.parse(pkt)
                if i_pts:
                    self._parse(i_pts, timer)
                self.active_segment.write(pkt)


x9 = XNine()
x9.slice(sys.argv[1])
