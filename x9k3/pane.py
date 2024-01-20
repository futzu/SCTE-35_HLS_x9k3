
class Pane:
    """
    Class to hold hls segment tags
    for a segment.
    """

    def __init__(self, file, name, num):
        self.tags = {}
        self.file = file
        self.name = name
        self.num = num

    def get(self):
        """
        get returns the a_pane data formated.
        """
        this = []
        for kay, vee in self.tags.items():
            if vee is None:
                this.append(kay)
            else:
                this.append(f"{kay}:{vee}")
        this.append(self.file)
        this.append("")
        this = "\n".join(this)
        return this

    def add_tag(self, quay, val):
        """
        add_tag appends key and value for a hls tag
        """
        self.tags[quay] = val

