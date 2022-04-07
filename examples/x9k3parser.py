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
                # self.end = round(strm._prgm_pts.values()[0] / 90000.0, 6)
                if len(strm.start.values()) > 0:
                    pts_start = strm.start.popitem()[1]
                self.pts = round(pts_start / 90000.0, 6)
            except:
                pass
        self.start = self.pts

    def _extinf(self, line):
        if line.startswith("#EXTINF"):
            t = line.split(":")[1].split(",")[0]
            t = float(t)
            self.duration = round(t, 6)

    def _ext_x_scte35(self, line):
        if line.startswith("#EXT-X-SCTE35"):
            line = line.replace(" ", "")
            tag, tail = line.split(":", 1)
            attributes = {
                a[0]: a[1] for a in [p.split("=", 1) for p in tail.split(",")]
            }
            self.cue = attributes["CUE"]
            self.do_cue()

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
            self._ext_x_scte35(line)
            self._extinf(line)
            if not self.pts:
                self._get_pts_start(self.segment)
                self.start = self.pts
        if not self.start:
            self.start = 0.0
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
            line.replace(" ", "").replace('"', "").replace("\n", "").replace("\r", "")
        )
        return line

    def show_segment_times(self, stanza):
        print(f"\tStart: {round(stanza.start,6)}")
        print(f"\tEnd: {round(stanza.start,6) + stanza.duration}")
        print(f"\tDuration: {stanza.duration}")
        print(f"\tHLS Time: {round(self.hls_time,6)}")

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
    arg = sys.argv[1]
    X9K3Parser(arg).decode()
