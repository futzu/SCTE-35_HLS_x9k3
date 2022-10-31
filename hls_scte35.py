class SCTE35:
    """
    A SCTE35 instance is used to hold
    SCTE35 cue data by X9K3.
    """

    def __init__(self):
        self.cue = None
        self.cue_out = None
        self.cue_time = None
        self.tag_method = self.x_scte35
        self.break_timer = None
        self.break_duration = None
        self.break_auto_return = False
        self.event_id = 1

    def mk_cue_tag(self):
        """
        mk_cue_tag
        """
        if self.cue:
            return self.tag_method()
        return False

    def x_cue(self):
        """
        #EXT-X-CUE-( OUT | IN | CONT )
        """
        if self.cue_out == "OUT":
            self.break_timer = 0
            return f"#EXT-X-CUE-OUT:{self.break_duration}"
        if self.cue_out == "IN":
            return "#EXT-X-CUE-IN"
        if self.cue_out == "CONT":
            return f"#EXT-X-CUE-OUT-CONT:{self.break_timer:.3f}/{self.break_duration}"
        return False

    def x_splicepoint(self):
        """
        #EXT-X-SPLICEPOINT-SCTE35
        """
        base = f"#EXT-X-SPLICEPOINT-SCTE35:{self.cue.encode()}"
        if self.cue_out == "OUT":
            return f"{base}"
        if self.cue_out == "IN":
            return f"{base}"
        return False

    def x_scte35(self):
        """
        #EXT-X-SCTE35
        """
        base = f'#EXT-X-SCTE35:CUE="{self.cue.encode()}" '
        if self.cue_out == "OUT":
            return f"{base},CUE-OUT=YES "
        if self.cue_out == "IN":
            return f"{base},CUE-IN=YES "
        if self.cue_out == "CONT":
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

        if self.cue_out == "OUT":
            self.break_timer = 0
            fstart = f',START-DATE="{iso8601}"'
            tag = f"{fbase}{fstart}{fdur},SCTE35-OUT={self.cue.encode_as_hex()}"
            self.event_id += 1
            return tag

        if self.cue_out == "IN":
            fstop = f',END-DATE="{iso8601}"'
            tag = f"{fbase}{fstop},SCTE35-IN={self.cue.encode_as_hex()}"
            self.event_id += 1
            return tag

        return False

    def is_cue_out(self, cue):
        """
        is_cue_out checks a Cue instance
        to see if it is a cue_out event.
        Returns True for a cue_out event.
        """
        cmd = cue.command
        if cmd.command_type == 5:
            if cmd.out_of_network_indicator:
                if cmd.break_duration:
                    self.break_duration = cmd.break_duration
                    self.break_timer = 0
                    return True

        upid_starts = [
            0x10,
            0x20,
            0x22,
            0x30,
            0x32,
            0x34,
            0x36,
            0x38,
            0x3A,
            0x3C,
            0x3E,
            0x44,
            0x46,
        ]
        if cmd.command_type == 6:
            for dsptr in cue.descriptors:
                if dsptr.tag == 2:
                    if dsptr.segmentation_type_id in upid_starts:
                        if dsptr.segmentation_duration:
                            self.break_duration = dsptr.segmentation_duration
                            self.break_timer = 0
                            return True

        return False

    def is_cue_in(self, cue):
        """
        is_cue_in checks a Cue instance
        to see if it is a cue_in event.
        Returns True for a cue_in event.
        """
        cmd = cue.command
        if cmd.command_type == 5:
            if not cmd.out_of_network_indicator:
                if self.break_timer >= self.break_duration:
                    return True

        upid_stops = [
            0x11,
            0x21,
            0x21,
            0x23,
            0x33,
            0x35,
            0x37,
            0x39,
            0x3B,
            0x3D,
            0x3F,
            0x45,
            0x47,
        ]
        if cmd.command_type == 6:
            for dsptr in cue.descriptors:
                if dsptr.tag == 2:
                    if dsptr.segmentation_type_id in upid_stops:
                        if self.break_timer >= self.break_duration:
                            return True

        return False
