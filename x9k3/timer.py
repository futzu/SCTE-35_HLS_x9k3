"""
x9k3

timer.py home of the Timer class, used mostly for
throttling to simulate live hls from pre-recorded content.

"""


import time
from threefive import print2

class Timer:
    """
    Timer class instances are used for
    segment duration, and live throttling.
    """

    def __init__(self):
        self.started = time.time()
        self.begin = None
        self.end = None
        self.lap_time = None

    def start(self, begin=None):
        """
        start starts the timer
        """
        self.begin = begin
        if not self.begin:
            self.begin = time.time()
        self.end = None
        self.lap_time = None

    def stop(self, end=None):
        """
        stop stops the timer
        """
        self.end = end
        if not self.end:
            self.end = time.time()
        self.lap_time = self.end - self.begin

    def elapsed(self, now=None):
        """
        elapsed returns the elapsed time
        """
        if not now:
            now = time.time()
        return now - self.started

    def throttle(self, seg_time, begin=None, end=None):
        """
        throttle is called to slow segment creation
        to simulate live streaming.
        """
        self.stop(end)
        diff = round((seg_time - self.lap_time), 2)
        if diff > 0:
            print2(f"throttling {diff}")
            time.sleep(diff)
        self.start(begin)
