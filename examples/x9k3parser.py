"""
x9k3parser
"""


import sys
import threefive


class Stanza:
    """
    The Stanza class represents a segment
    and associated data

    """

    def __init__(self, lines, segment, start):
        self.lines = lines
        self.segment = segment
        self.clean_segment()
        self.pts = None
        self.start = start
        self.end = None
        self.duration = 0
        self.cue = False
        self.stuff = {}

    def clean_segment(self):
        if self.segment.startswith("http"):
            ss = self.segment.split("/")
            while ".." in ss:
                i = ss.index("..")
                del ss[i]
                del ss[i - 1]
            self.segment = "/".join(ss)

    def _get_pts_start(self, seg):
        if not self.start:
            pts_start = 0.000001
            try:
                strm = threefive.Stream(seg)
                strm.decode(func=None)
                if len(strm.start.values()) > 0:
                    pts_start = strm.start.popitem()[1]
                self.pts = round(pts_start / 90000.0, 6)
            except:
                pass
        self.start = self.pts

    def _extinf(self):
        self.duration = round(float(self.stuff['#EXTINF']), 6)
        del self.stuff['#EXTINF']


    def _ext_x_scte35(self):
        self.cue = self.stuff["CUE"]
        self.do_cue()


    def parse_stuff(self,line):
        line = line.replace(" ", "")
        if ':' not in line:
            return
        tag, tail = line.split(":", 1)
        while tail:
            if '=' not in tail:
                key=tag
                value = tail
                tail = None
            else:
                if not tail.endswith('"'):
                    tail,value=tail.rsplit('=',1)
                else:
                    tail,value= tail[:-1].rsplit('="',1)
                splitup=tail.rsplit(',',1)
                if len(splitup) ==2:
                    tail,key =splitup
                else:
                    key=splitup[0]
                    tail=None
            if value.endswith(','):
                value=value[:-1]
            key=key.replace("#EXT-","").replace("X-","")
            self.stuff[key]=value

    def show_stuff(self):
        {print(f'{k}: {v}') for k,v in self.stuff.items()}

    def do_cue(self):
        """
        do_cue parses a SCTE-35 encoded string
        via the threefive.Cue class
        """
        if self.cue:
            print(f"\nSCTE-35 CUE Data:\n")
            print(self.cue, "\n")
            tf = threefive.Cue(self.cue)
            tf.decode()
            tf.show()

    def decode(self):
        print(f"-- {self.segment}\n")
        for line in self.lines:
            self.parse_stuff(line)
            if '#EXTINF' in self.stuff:
                self._extinf()
            if 'CUE' in self.stuff:
                self._ext_x_scte35()
            if not self.start:
                self._get_pts_start(self.segment)
                self.start = self.pts
        if not self.start:
            self.start = 0.0
        self.show_stuff()
        return self.start


class X9K3Parser:
    """
    X9K3 Parser for x9k3 generated
    Manifests.
    """

    def __init__(self, arg):
        self.m3u8 = arg
        self.hls_time = 0.0
        self.seg_list = []
        self._start = None
        self.chunk = []
        self.base_uri = ""
        if arg.startswith("http"):
            self.base_uri = arg[: arg.rindex("/") + 1]
        self.manifest = None
        self.next_expected = 0

    @staticmethod
    def _clean_line(line):
        if isinstance(line, bytes):
            line = line.decode(errors="ignore")
        line = (
            line.replace(" ", "").replace("\n", "").replace("\r", "")
        )
        return line

    def show_segment_times(self, stanza):
        print(f"\tSegment Start: {round(stanza.start,6)}")
        print(f"\tSegment Duration: {stanza.duration}")
        print(f"\tSegment End: {round(stanza.start,6)+ stanza.duration}")
        print(f"HLS Time: {round(self.hls_time,6)}")

    def do_segment(self, line):
        segment = line
        if not line.startswith("http"):
            segment = self.base_uri + line
        if segment not in self.seg_list:
            self.seg_list.append(segment)
            self.seg_list = self.seg_list[-200:]
            stanza = Stanza(self.chunk, segment, self._start)
            stanza.decode()
            if not self._start:
                self._start = stanza.start
            self._start +=stanza.duration
            self.next_expected = self._start + self.hls_time
            self.next_expected += round(stanza.duration, 6)
            self.hls_time += stanza.duration
            self.show_segment_times(stanza)

        self.chunk = []

    def decode(self):
        while True:
            with threefive.reader(self.m3u8) as self.manifest:
                while self.manifest:
                    line = self.manifest.readline()
                    if not line:
                        break
                    line = self._clean_line(line)
                    if "ENDLIST" in line:
                        return False
                    self.chunk.append(line)

                    if not line.startswith("#"):
                        if len(line):
                            self.do_segment(line)
                            print("\n")"""
x9k3parser
"""


import sys
import threefive


class Stanza:
    """
    The Stanza class represents a segment
    and associated data

    """

    def __init__(self, lines, segment, start):
        self.lines = lines
        self.segment = segment
        self.clean_segment()
        self.pts = None
        self.start = start
        self.end = None
        self.duration = 0
        self.cue = False
        self.stuff = {}

    def clean_segment(self):
        if self.segment.startswith("http"):
            ss = self.segment.split("/")
            while ".." in ss:
                i = ss.index("..")
                del ss[i]
                del ss[i - 1]
            self.segment = "/".join(ss)

    def _get_pts_start(self, seg):
        if not self.start:
            pts_start = 0.000001
            try:
                strm = threefive.Stream(seg)
                strm.decode(func=None)
                if len(strm.start.values()) > 0:
                    pts_start = strm.start.popitem()[1]
                self.pts = round(pts_start / 90000.0, 6)
            except:
                pass
        self.start = self.pts

    def _extinf(self):
        self.duration = round(float(self.stuff['#EXTINF']), 6)
        del self.stuff['#EXTINF']


    def _ext_x_scte35(self):
        self.cue = self.stuff["CUE"]
        self.do_cue()


    def parse_stuff(self,line):
        line = line.replace(" ", "")
        if ':' not in line:
            return
        tag, tail = line.split(":", 1)
        while tail:
            if '=' not in tail:
                key=tag
                value = tail
                tail = None
            else:
                if not tail.endswith('"'):
                    tail,value=tail.rsplit('=',1)
                else:
                    tail,value= tail[:-1].rsplit('="',1)
                splitup=tail.rsplit(',',1)
                if len(splitup) ==2:
                    tail,key =splitup
                else:
                    key=splitup[0]
                    tail=None
            if value.endswith(','):
                value=value[:-1]
            key=key.replace("#EXT-","").replace("X-","")
            self.stuff[key]=value

    def show_stuff(self):
        {print(f'{k}: {v}') for k,v in self.stuff.items()}

    def do_cue(self):
        """
        do_cue parses a SCTE-35 encoded string
        via the threefive.Cue class
        """
        if self.cue:
            print(f"\nSCTE-35 CUE Data:\n")
            print(self.cue, "\n")
            tf = threefive.Cue(self.cue)
            tf.decode()
            tf.show()

    def decode(self):
        print(f"-- {self.segment}\n")
        for line in self.lines:
            self.parse_stuff(line)
            if '#EXTINF' in self.stuff:
                self._extinf()
            if 'CUE' in self.stuff:
                self._ext_x_scte35()
            if not self.start:
                self._get_pts_start(self.segment)
                self.start = self.pts
        if not self.start:
            self.start = 0.0
        self.show_stuff()
        return self.start


class X9K3Parser:
    """
    X9K3 Parser for x9k3 generated
    Manifests.
    """

    def __init__(self, arg):
        self.m3u8 = arg
        self.hls_time = 0.0
        self.seg_list = []
        self._start = None
        self.chunk = []
        self.base_uri = ""
        if arg.startswith("http"):
            self.base_uri = arg[: arg.rindex("/") + 1]
        self.manifest = None
        self.next_expected = 0

    @staticmethod
    def _clean_line(line):
        if isinstance(line, bytes):
            line = line.decode(errors="ignore")
        line = (
            line.replace(" ", "").replace("\n", "").replace("\r", "")
        )
        return line

    def show_segment_times(self, stanza):
        print(f"\tSegment Start: {round(stanza.start,6)}")
        print(f"\tSegment Duration: {stanza.duration}")
        print(f"\tSegment End: {round(stanza.start,6)+ stanza.duration}")
        print(f"HLS Time: {round(self.hls_time,6)}")

    def do_segment(self, line):
        segment = line
        if not line.startswith("http"):
            segment = self.base_uri + line
        if segment not in self.seg_list:
            self.seg_list.append(segment)
            self.seg_list = self.seg_list[-200:]
            stanza = Stanza(self.chunk, segment, self._start)
            stanza.decode()
            if not self._start:
                self._start = stanza.start
            self._start +=stanza.duration
            self.next_expected = self._start + self.hls_time
            self.next_expected += round(stanza.duration, 6)
            self.hls_time += stanza.duration
            self.show_segment_times(stanza)

        self.chunk = []

    def decode(self):
        while True:
            with threefive.reader(self.m3u8) as self.manifest:
                while self.manifest:
                    line = self.manifest.readline()
                    if not line:
                        break
                    line = self._clean_line(line)
                    if "ENDLIST" in line:
                        return False
                    self.chunk.append(line)

                    if not line.startswith("#"):
                        if len(line):
                            self.do_segment(line)
                            print("\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    for arg in args:
        X9K3Parser(arg).decode()



if __name__ == "__main__":
    args = sys.argv[1:]
    for arg in args:
        X9K3Parser(arg).decode()
