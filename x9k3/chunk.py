"""
The Chunk class
"""


class Chunk:
    """
    Class to hold hls segment tags
    for a segment.
    """
    def __init__(self, name, num):
        self.tags = {}
        self.name = name
        self.num = num

    def get(self):
        """
        get returns the Chunk data formated.
        """
        this = [f"{k}:{v}" for k, v in self.tags.items()]
        this.append(self.name)
        this.append("")
        this = "\n".join(this)
        return this

    def add_tag(self, quay, val):
        """
        add_tag appends key and value for a hls tag
        """
        self.tags[quay] = val
