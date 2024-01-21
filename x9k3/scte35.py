"""
x9k3

scte35.py

the SCTE35 class used by x9k3.
"""


import datetime

class SCTE35:
    """
    A SCTE35 instance is used to hold
    SCTE35 cue data by X9K3.
    """

    def __init__(self):
        self.cue = None
        self.cue_state = None
        self.cue_time = None
        self.tag_method = self.x_cue
        self.break_timer = None
        self.break_duration = None
        self.event_id = 1
        self.seg_type = None

    def mk_cue_tag(self):
        """
        mk_cue_tag routes hls tag creation
        """
        tag = False
        if self.cue:
            tag = self.tag_method()
        return tag

    def chk_cue_state(self):
        """
        chk_cue_state changes self.cue_state
        """
        if self.cue_state == "OUT":
            self.cue_state = "CONT"
        if self.cue_state == "IN":
            self.cue_time = None
            self.cue = None
            self.cue_state = None
            self.break_timer = None

    def mk_cue_state(self):
        """
        mk_cue_state checks if the cue
        is a CUE-OUT or a CUE-IN and
        sets cue_state.
        """
        if self.is_cue_out(self.cue):
            self.cue_state = "OUT"
            self.break_timer = 0.0
            if self.cue_time and self.break_duration:
                self.cue_time += self.break_duration
        if self.is_cue_in(self.cue):
            # the next line causes splice immediate break returns to fail.
            # if self.break_timer >= self.break_duration:
            self.cue_state = "IN"

    def x_cue(self):
        """
        #EXT-X-CUE-( OUT | IN | CONT )
        """
        if self.cue_state == "OUT":
            return f"#EXT-X-CUE-OUT:{self.break_duration}"
        if self.cue_state == "IN":
            return "#EXT-X-CUE-IN"
        if self.cue_state == "CONT":
            return f"#EXT-X-CUE-OUT-CONT:{self.break_timer:.6f}/{self.break_duration}"
        return False

    def x_splicepoint(self):
        """
        #EXT-X-SPLICEPOINT-SCTE35
        """
        base = f"#EXT-X-SPLICEPOINT-SCTE35:{self.cue.encode()}"
        if self.cue_state == "OUT":
            return f"{base}"
        if self.cue_state == "IN":
            return f"{base}"
        return False

    def x_scte35(self):
        """
        #EXT-X-SCTE35
        """
        base = f'#EXT-X-SCTE35:CUE="{self.cue.encode()}" '
        if self.cue_state == "OUT":
            return f"{base},CUE-OUT=YES "
        if self.cue_state == "IN":
            return f"{base},CUE-IN=YES "
        if self.cue_state == "CONT":
            return f"{base},CUE-OUT=CONT"
        return False

    def x_daterange(self):
        """
        #EXT-X-DATERANGE
        """
        fbase = f'#EXT-X-DATERANGE:ID="{self.event_id}"'
        iso8601 = f"{datetime.datetime.utcnow().isoformat()}Z"
        fdur = ""
        if self.break_duration:
            fdur = f",PLANNED-DURATION={self.break_duration}"

        if self.cue_state == "OUT":
            fstart = f',START-DATE="{iso8601}"'
            tag = f"{fbase}{fstart}{fdur},SCTE35-OUT={self.cue.encode_as_hex()}"
            return tag

        if self.cue_state == "IN":
            fstop = f',END-DATE="{iso8601}"'
            tag = f"{fbase}{fstop},SCTE35-IN={self.cue.encode_as_hex()}"
            self.event_id += 1
            return tag
        return False

    def _splice_insert_cue_out(self, cue):
        cmd = cue.command
        if cmd.out_of_network_indicator:
            if cmd.break_duration:
                self.break_duration = cmd.break_duration
            self.cue_state = "OUT"
            return True
        return False

    def _time_signal_cue_out(self, cue):
        seg_starts = [0x22, 0x30, 0x32, 0x34, 0x36, 0x44, 0x46]
        for dsptr in cue.descriptors:
            if dsptr.tag != 2:
                return False
            if dsptr.segmentation_type_id in seg_starts:
                self.seg_type = dsptr.segmentation_type_id + 1
                if dsptr.segmentation_duration:
                    self.break_duration = dsptr.segmentation_duration
                    self.cue_state = "OUT"
                    return True
        return False

    def is_cue_out(self, cue):
        """
        is_cue_out checks a Cue instance
        Returns True for a cue_out event.
        """
        if cue is None:
            return False
        if self.cue_state not in ["IN", None]:
            return False
        cmd = cue.command
        if cmd.command_type == 5:
            return self._splice_insert_cue_out(cue)
        if cmd.command_type == 6:
            return self._time_signal_cue_out(cue)

        return False

    def is_cue_in(self, cue):
        """
        is_cue_in checks a Cue instance
        Returns True for a cue_in event.
        """
        if cue is None:
            return False
        if self.cue_state not in ["OUT", "CONT"]:
            return False
        cmd = cue.command
        if cmd.command_type == 5:
            if not cmd.out_of_network_indicator:
                return True
        if cmd.command_type == 6:
            for dsptr in cue.descriptors:
                if dsptr.tag == 2:
                    if dsptr.segmentation_type_id == self.seg_type:
                        self.seg_type = None
                        self.cue_state = "IN"
                        return True
        return False
