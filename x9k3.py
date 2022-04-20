"""
x9k3parser
"""

import json
import sys
import threefive


class Segment:
    """
    The Segment class represents a segment
    and associated data

    """

    def __init__(self, lines, media_uri, start):
        self._lines = lines
        self.media = media_uri
        self.pts = None
        self.start = start
        self.end = None
        self.duration = 0
        self.cue = False
        self.cue_data = None
        self.tags = {}

    def __repr__(self):
        return str(self.__dict__)

    @staticmethod
    def dot_dot(media_uri):
        """
        dot dot resolves '..' in  urls
        """
        ssu = media_uri.split("/")
        while ".." in ssu:
            i = ssu.index("..")
            del ssu[i]
            del ssu[i - 1]
        media_uri = "/".join(ssu)
        return media_uri

    def kv_clean(self):
        """
        kv_clean removes items from a dict if the value is None
        """

        def b2l(val):
            if isinstance(val, (list)):
                val = [b2l(v) for v in val]
            if isinstance(val, (dict)):
                val = {k: b2l(v) for k, v in val.items()}
            return val

        return {k: b2l(v) for k, v in vars(self).items() if v not in [None, 0, 0.0]}

    def _get_pts_start(self, seg):
        if not self.start:
            pts_start = 0.000001
            try:
                strm = threefive.Stream(seg)
                strm.decode(func=None)
                if len(strm.start.values()) > 0:
                    pts_start = strm.start.popitem()[1]
                self.start = self.pts = round(pts_start / 90000.0, 6)
            except:
                pass
        self.start = self.pts

    def _extinf(self):
        self.duration = round(float(self.tags["#EXTINF"]), 6)

    def _ext_x_scte35(self):
        self.cue = self.tags["#EXT-X-SCTE35"]["CUE"]
        self.do_cue()

    def parse_tags(self, line):
        """
        parse_tags parses tags and
        associated attributes
        """
        line = line.replace(" ", "")
        if ":" not in line:
            return
        tag, tail = line.split(":", 1)
        if tail.endswith(","):
            tail = tail[:-1]
        self.tags[tag] = {}
        while tail:
            if "=" not in tail:
                self.tags[tag] = tail
                return
            if not tail.endswith('"'):
                tail, value = tail.rsplit("=", 1)
            else:
                tail, value = tail[:-1].rsplit('="', 1)
            splitup = tail.rsplit(",", 1)
            if len(splitup) == 2:
                tail, key = splitup
            else:
                key = splitup[0]
                tail = None
            self.tags[tag][key] = value

    def show(self):
        print(json.dumps(self.kv_clean(), indent=4))

    def do_cue(self):
        """
        do_cue parses a SCTE-35 encoded string
        via the threefive.Cue class
        """
        if self.cue:
            tf = threefive.Cue(self.cue)
            tf.decode()
            self.cue_data = tf.get()
            # tf.show()

    def decode(self):
        self.media = self.dot_dot(self.media)
        for line in self._lines:
            self.parse_tags(line)
            if "#EXTINF" in self.tags:
                self._extinf()
            if "#EXT-X-SCTE35" in self.tags:
                self._ext_x_scte35()
            if not self.start:
                self._get_pts_start(self.media)
                self.start = self.pts
        if not self.start:
            self.start = 0.0
        self.start = round(self.start, 6)
        self.end = round(self.start + self.duration, 6)
        del self._lines
        self.show()
        return self.start


class X9K3Parser:
    """
    X9K3 Parser for x9k3 generated
    Manifests.
    """

    def __init__(self, arg):
        self.m3u8 = arg
        self.hls_time = 0.0
        self.media_list = []
        self._start = None
        self.chunk = []
        self.base_uri = ""
        if arg.startswith("http"):
            self.base_uri = arg[: arg.rindex("/") + 1]
        self.manifest = None
        self.segments = []
        self.next_expected = 0
        self.master = False
        self.reload = True

    @staticmethod
    def _clean_line(line):
        if isinstance(line, bytes):
            line = line.decode(errors="ignore")
            line = line.replace("\n", "").replace("\r", "")
        return line

    def is_master(self, line):
        if "STREAM-INF" in line:
            self.master = True
            self.reload = False

    def do_media(self, line):
        media = line
        if self.master and "URI" in line:
            media = line.split('URI="')[1].split('"')[0]
        if not line.startswith("http"):
            media = self.base_uri + media
        if media not in self.media_list:
            self.media_list.append(media)
            self.media_list = self.media_list[-200:]

            segment = Segment(self.chunk, media, self._start)
            self.segments.append(segment)
            segment.decode()
            if not self._start:
                self._start = segment.start
            self._start += segment.duration
            self.next_expected = self._start + self.hls_time
            self.next_expected += round(segment.duration, 6)
            self.hls_time += segment.duration
        self.chunk = []

    def decode(self):
        while self.reload:
            with threefive.reader(self.m3u8) as self.manifest:
                while self.manifest:
                    line = self.manifest.readline()
                    if not line:
                        break
                    line = self._clean_line(line)
                    if not (line.startswith("#EXT-X-VERSION") or line.startswith(
                        "#EXT-X-TARGETDURATION")
                    ):
                        if "ENDLIST" in line:
                            return False
                        self.is_master(line)
                        self.chunk.append(line)
                        if not line.startswith("#") or line.startswith(
                            "#EXT-X-I-FRAME-STREAM-INF"
                        ):
                            if len(line):
                                self.do_media(line)


if __name__ == "__main__":
    args = sys.argv[1:]
    for arg in args:
        x9k3p = X9K3Parser(arg)
        x9k3p.decode()
