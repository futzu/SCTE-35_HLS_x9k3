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
