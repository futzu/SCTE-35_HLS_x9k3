## Classes for the x9k3 remix


### SCTE35

```js
    class SCTE35(builtins.object)
     |  A SCTE35 instance is used to hold
     |  SCTE35 cue data by X9K3.
     |  
     |  Methods defined here:
     |  
     |  __init__(self)
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
     |  mk_cue_tag(self)
     |      mk_cue_tag routes  hls tag creation
     |      to the appropriate method.
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
     |  ----------------------------------
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
