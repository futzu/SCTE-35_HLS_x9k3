import time


class Timer:
    def __init__(self):
        self.begin = None
        self.end = None
        self.lap_time = None

    def start(self,begin=None):
        self.begin = begin
        if not self.begin:
            self.begin = time.time()
        self.end = None
        self.lap_time = None

    def stop(self,end=None):
        self.end = end
        if not self.end:
            self.end = time.time()
        self.lap_time = self.end - self.begin

    def elapsed(self, now =None):
        if not now:
            now = time.time()
        return now - self.begin

    def throttle(self, seg_time,begin=None, end=None):
        self.stop(end)
        diff = round(seg_time - self.lap_time, 2)
        if diff > 0:
            print(f"throttling {diff}")
            time.sleep(diff/2)
        self.start(begin)
