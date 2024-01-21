"""
x9k3

window.py

home of the SlidingWindow class.
"""

from collections import deque
import os
from pathlib import Path
from threefive import print2


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
