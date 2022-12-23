"""
The SlidingWindow Class for live M3u8 playlists

The arg named chunk is a just lines of text associated
with the segment to be written to the m3u8
like:

#EXT-X-DISCONTINUITY
#EXT-X-CUE-OUT:15.0
#EXTINF:2.152144,
seg2.ts

""

class SlidingWindow:
    """
    The SlidingWindow class
    """
    def __init__(self, size):
        self.size = size
        self.queue = []

    def popleft(self):
        """
        popleft removes the first item in self.queue
        """
        if len(self.queue) >= self.size:
            self.queue = self.queue[1:]

    def push(self, chunk):
        """
        push appends a chunk to self.queue
        """
        self.queue.append(chunk)
       # print([chunk.name for chunk in list(self.queue)])

    def all(self):
        """
        all returns the current window chunks
        """
        return "".join([chunk.get() for chunk in self.queue])

    def slide(self,chunk):
        """
        slide calls self.push with chunk
        and calls self.popleft to move the window
        """
        self.push(chunk)
        self.popleft()
