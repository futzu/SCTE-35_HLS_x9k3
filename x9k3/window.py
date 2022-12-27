"""
The SlidingWindow Class for live M3u8 playlists

The arg named a_pane  is just lines of text associated
with the segment to be written to the m3u8
like:

#EXT-X-DISCONTINUITY
#EXT-X-CUE-OUT:15.0
#EXTINF:2.152144,
seg2.ts

"""


class SlidingWindow:
    """
    The SlidingWindow class
    """

    def __init__(self, size):
        self.size = size
        self.panes = []
        self.delete = False

    def pop_pane(self):
        """
        pop_pane removes the first item in self.panes
        """
        if len(self.panes) >= self.size:
            popped = self.panes[0]
            if self.delete
            self.panes = self.panes[1:]

    def push_pane(self, a_pane):
        """
        push appends a_pane to self.panes
        """
        self.panes.append(a_pane)
        # print([a_pane.name for a_pane in self.panes])

    def all_panes(self):
        """
        all_panes returns the current window panes joined.
        """
        return "".join([a_pane.get() for a_pane in self.panes])

    def slide_panes(self, a_pane):
        """
        slide calls self.push_pane with a_pane
        and then calls self.pop_pane to trim self.panes
        as needed.
        """
        self.push_pane(a_pane)
        self.pop_pane()
