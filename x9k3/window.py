
class SlidingWindow:
    """
    The SlidingWindow class
    """

    def __init__(self, size=50000):
        self.size = size
        self.panes = deque()
        self.delete = False

    def popleft_pane(self):
        """
        popleft_pane removes the first item in self.panes
        """
        popped = self.panes.popleft()
        if self.delete:
            Path(popped.name).touch()
            os.unlink(popped.name)
            print2(f"deleted {popped.name}")

    def push_pane(self, a_pane):
        """
        push appends a_pane to self.panes
        """
        self.panes.append(a_pane)

    def all_panes(self):
        """
        all_panes returns the current window panes joined.
        """
        return "".join([a_pane.get() for a_pane in self.panes])

    def slide_panes(self, a_pane=None):
        """
        slide calls self.push_pane with a_pane and then
        calls self.popleft_pane to trim self.panes as needed.
        """
        if a_pane:
            self.push_pane(a_pane)
        if len(self.panes) > self.size:
            self.popleft_pane()


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

