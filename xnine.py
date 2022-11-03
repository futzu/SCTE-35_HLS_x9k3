import io
import sys
import time
from functools import partial
from new_reader import reader
from iframes import IFramer
from collections import deque


class SCTE35:
    """
    A SCTE35 instance is used to hold
    SCTE35 cue data by X9K3.
    """

    def __init__(self):
        self.cue = None
        self.cue_out = None
        self.cue_time = None
        self.tag_method = self.x_scte35
        self.break_timer = None
        self.break_duration = None
        self.break_auto_return = False
        self.event_id = 1

    def mk_cue_tag(self):
        """
        mk_cue_tag
        """
        if self.cue:
            return self.tag_method()
        return False

    def x_cue(self):
        """
        #EXT-X-CUE-( OUT | IN | CONT )
        """
        if self.cue_out == "OUT":
            self.break_timer = 0
            return f"#EXT-X-CUE-OUT:{self.break_duration}"
        if self.cue_out == "IN":
            return "#EXT-X-CUE-IN"
        if self.cue_out == "CONT":
            return f"#EXT-X-CUE-OUT-CONT:{self.break_timer:.3f}/{self.break_duration}"
        return False

    def x_splicepoint(self):
        """
        #EXT-X-SPLICEPOINT-SCTE35
        """
        base = f"#EXT-X-SPLICEPOINT-SCTE35:{self.cue.encode()}"
        if self.cue_out == "OUT":
            return f"{base}"
        if self.cue_out == "IN":
            return f"{base}"
        return False

    def x_scte35(self):
        """
        #EXT-X-SCTE35
        """
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
        #EXT-X-DATERANGE
        """
        fbase = f'#EXT-X-DATERANGE:ID="{self.event_id}"'
        iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
        fdur = ""
        if self.break_duration:
            fdur = f",PLANNED-DURATION={self.break_duration}"

        if self.cue_out == "OUT":
            self.break_timer = 0
            fstart = f',START-DATE="{iso8601}"'
            tag = f"{fbase}{fstart}{fdur},SCTE35-OUT={self.cue.encode_as_hex()}"
            self.event_id += 1
            return tag

        if self.cue_out == "IN":
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
        cmd = cue.command
        if cmd.command_type == 5:
            if cmd.out_of_network_indicator:
                if cmd.break_duration:
                    self.break_duration = cmd.break_duration
                    self.break_timer = 0
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
                            self.break_timer = 0
                            return True

        return False

    def is_cue_in(self, cue):
        """
        is_cue_in checks a Cue instance
        to see if it is a cue_in event.
        Returns True for a cue_in event.
        """
        cmd = cue.command
        if cmd.command_type == 5:
            if not cmd.out_of_network_indicator:
                if self.break_timer >= self.break_duration:
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
                        if self.break_timer >= self.break_duration:
                            return True

        return False

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
        self.scte35 = SCTE35()
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

    def add_cue_tag(self,chunk):
        tag = self.scte35.mk_cue_tag()
        if tag:
            k,v = tag.split(":",1)
            chunk.add_tag(k,v)
            
    def _write_segment(self, seg_time):
        seg_name = f"seg{self.segnum}.ts"
        with open(seg_name, "wb") as seg:
            seg.write(self.active_segment.getbuffer())
        chunk = Chunk(seg_name, self.segnum)
        self.add_cue_tag(chunk)
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

    def chk_scte35_cue_time(self):       
        if self.scte35.cue_time:
            if self.start_time < self.scte35.cue_time < self.end_time:
                self.end_time = self.scte35.cue_time
            if self.scte35.cue_time == self.start_time:
                if self.scte35.is_cue_out(self.scte35.cue):
                    self.scte35.cue_out="OUT"
                if self.scte35.is_cue_in(self.scte35.cue):
                    self.scte35.cue_out="IN"
            else:
                if self.scte35.cue_out =="OUT":
                    self.scte35.cue_out ="CONT"
                   
    def _parse(self, i_pts, timer):
        if not self.start_time:
            self.start_time = i_pts
            timer.start()
            self.chk_scte35_cue_time()
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
