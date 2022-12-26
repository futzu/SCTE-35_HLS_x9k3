## Classes for the x9k3 remix

### ExpX9K3
```js
    class ExpX9K3(threefive.stream.Stream)
     |  ExpX9K3(tsdata, show_null=False)
     |  
     |  Stream class for parsing MPEG-TS data.
     |  
     |  Method resolution order:
     |      ExpX9K3
     |      threefive.stream.Stream
     |      builtins.object
     |  
     |  Methods defined here:
     |  
     |  __init__(self, tsdata, show_null=False)
     |      tsdata is an file or http/https url
     |      set show_null=False to exclude Splice Nulls
     |      
     |      Use like...
     |      
     |      from threefive import Stream
     |      strm = Stream("vid.ts",show_null=False)
     |      strm.decode()
     |  
     |  add_cue_tag(self, chunk)
     |  
     |  slice_check(self, now)
     |  
     |  slicer(self)
     |  
     |  ----------------------------------------------------------------------
     |  Methods inherited from threefive.stream.Stream:
     |  
     |  __repr__(self)
     |  
     |  decode(self, func=<function show_cue at 0x00007f0818f51e20>)
     |      Stream.decode reads self.tsdata to find SCTE35 packets.
     |      func can be set to a custom function that accepts
     |      a threefive.Cue instance as it's only argument.
     |  
     |  decode_next(self)
     |      Stream.decode_next returns the next
     |      SCTE35 cue as a threefive.Cue instance.
     |  
     |  decode_program(self, the_program, func=<function show_cue at 0x00007f0818f51e20>)
     |      Stream.decode_program limits SCTE35 parsing
     |      to a specific MPEGTS program.
     |  
     |  
     |  decode_proxy(self, func=<function show_cue_stderr at 0x00007f0818f51d80>)
     |      Stream.decode_proxy writes all ts packets are written to stdout
     |      for piping into another program like mplayer.
     |      SCTE-35 cues are printed to stderr.
     |  
     |  decode_start_time(self)
     |      displays streams that will be
     |      parsed for SCTE-35.
     |  
     |  iter_pkts(self)
     |      iter_pkts iterates a mpegts stream into packets
     |  
     |  pid2pcr(self, pid)
     |      pid2pcr takes a pid
     |      returns the current pcr
     |  
     |  pid2prgm(self, pid)
     |      pid2prgm takes a pid,
     |      returns the program
     |  
     |  pid2pts(self, pid)
     |      pid2pts takes a pid
     |      returns the current pts
     |  
     |  show(self)
     |      displays streams that will be
     |      parsed for SCTE-35.
     |  
     |  ----------------------------------------------------------------------
     |  Static methods inherited from threefive.stream.Stream:
     |  
     |  as_90k(ticks)
     |      as_90k returns ticks as 90k clock time
     |  
     |  ----------------------------------------------------------------------
```


###  Chunk

```js
    class Chunk(builtins.object)
     |  Chunk(name, num)
     |  
     |  Class to hold hls segment tags
     |  for a segment.
     |  
     |  Methods defined here:
     |  
     |  __init__(self, name, num)
     |  
     |  add_tag(self, quay, val)
     |      add_tag appends key and value for a hls tag
     |  
     |  get(self)
     |      get returns the Chunk data formated.
     |  
     |  ----------------------------------------------------------------------
```

### SCTE35

```js
    
    class SCTE35(builtins.object)
     |  A SCTE35 instance is used to hold
     |  SCTE35 cue data by X9K5.
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
     |  
     |  chk_cue_state(self)
     |      chk_cue_state changes
     |      OUT to CONT
     |      and IN to None
     |      when the cue is expired.
     |  
     |  is_cue_in(self, cue)
     |      is_cue_in checks a Cue instance
     |      to see if it is a cue_in event.
     |      Returns True for a cue_in event.
     |  
     |  is_cue_out(self, cue)
     |      is_cue_out checks a Cue instance
     |      to see if it is a cue_out event.
     |      Returns True for a cue_out event.
     |  
     |  mk_auto_return(timestamp)
     |      mk_auto_return generates a cue
     |      when a splice insert has the
     |      break_autp_return flag set.
     |  
     |  mk_cue_state(self)
     |      mk_cue_state checks if the cue
     |      is a CUE-OUT or a CUE-IN and
     |      sets cue_state.
     |  
     |  mk_cue_tag(self)
     |      mk_cue_tag routes  hls tag creation
     |      to the appropriate method.
     |  
     |  
     |  x_cue(self)
     |      #EXT-X-CUE-( OUT | IN | CONT )
     |  
     |  x_daterange(self)
     |      #EXT-X-DATERANGE
     |  
     |  x_scte35(self)
     |      #EXT-X-SCTE35
     |  
     |  x_splicepoint(self)
     |      #EXT-X-SPLICEPOINT-SCTE35
     |  
     |  ----------------------------------------------------------------------

```



###      SlidingWindow

```js
    
    class SlidingWindow(builtins.object)
     |  SlidingWindow(size)
     |  
     |  The SlidingWindow class
     |  
     |  Methods defined here:
     |  
     |  __init__(self, size)
     |  
     |  all_panes(self)
     |      all_panes returns the current window panes joined.
     |  
     |  pop_pane(self)
     |      pop_pane removes the first item in self.panes
     |  
     |  push_pane(self, a_pane)
     |      push appends a_pane to self.panes
     |  
     |  slide_panes(self, a_pane)
     |      slide calls self.push_pane with a_pane
     |      and then calls self.pop_pane to trim self.panes
     |      as needed.
     |  
     |  ----------------------------------------------------------------------
```
