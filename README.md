 [Install](https://github.com/futzu/scte35-hls-segmenter-x9k3/README.md#install) |
 [Use](#how-to-use) |
 [CUE-OUT](#cue-out) |
 [CUE-IN](#cue-in)   |
 [SCTE-35 Tags](#hls--tags) |
 [Sidecar SCTE35](#sidecar-files) |
 [Live](#live)  |
 [Bugs](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues)

___

### HLS + SCTE35 = x9k3
### `x9k3` is a HLS segmenter with SCTE-35 injection and parsing, powered by threefive.

---
# `Heads Up`
### x9k3 is not finished, there are bugs. I am trying to fix them.
### I keep getting sidetrack by people running unit tests for every possible combination of options.
### This is not the time for fanatical testing of edge cases, that comes later.
### Sorry, but If you're not sleeping with me or paying my bills, you're not a priority.

---


<details><summary><b> Segment duration is open to interpretation... wait, let me explain.</b></summary>

 
<div>
 <br>
        threefive and ffmpeg may report different durations for segments.<br>
threefive use absolute PTS values and always start on an iframe.
 <br>
In the tables below, four segments are compared.<br> 
Reported start and reported duration are values returned from the tool.<br>
Calculate duration is (next segment start - this segment start)
 <br><br>

</div>
<br>
<br>

* <b>threefive</b> (what x9k3 uses)

| segment| reported start|  reported duration|calculated duration|
|--------|---------------|-------------------|-------------------|
| seg0.ts|  3164.376089  |     2.0           |     2.0           |
| seg1.ts|  3166.376089  |     2.0           |     2.0           |
| seg2.ts|  3168.376089  |     2.0           |     2.0           |
| seg3.ts|  3170.376089  |     2.0           |     2.0           |


* <b>ffmpeg</b>

| segment| reported start|  reported duration|calculated duration|
|--------|---------------|-------------------|-------------------|
| seg0.ts|   3164.376089 |   2.0             |    0.361333       |
| seg1.ts|   3164.737422 |   3.64            |    2.047999       |
| seg2.ts|   3166.785422 |   3.59            |    3.59           |
| seg3.ts|   3170.376089 |   2.0             |    0.356000       |


#### What does it all mean? 
> I don't know.
>  
___


</details>

---
#### `Current Version`: 
# v.0.2.37

|  test               | command                | score                  |previous     |
|---------------------|------------------------|------------------------|-------------|
|cyclomatic complexity| radon cc -s -a  x9k3.py|  __A (2.807692)__          | A (2.769230)|
| pylint              |  pylint  x9k3.py       |                 __9.97 / 10__| __9.97 / 10__ |



* __Some of the new stuff__:
   * m3u8 files as input. Resegment and add SCTE-35 to an existing m3u8. `-i INPUT`, `--input INPUT`
   * segments may be added to an existing m3u8, VOD or live. ` -c`, `--continue_m3u8 `
   * discontinuity tags may now be omitted. `-n`, `--no_discontinuity`
   * auto `CUE-IN`
   *  live throttling can be disabled with the `-N`, `--no_throttle` flag 


## `Features`

   * __SCTE-35 Cues__ in __Mpegts Streams__ are Translated into __HLS tags__.
   * __SCTE-35 Cues can be added from a [Sidecar File](#sidecar-files)__.
   * Segments are __Split on SCTE-35 Cues__ as needed.
   * Segments __Start on iframes__.
   * Supports __h264__ and __h265__ .
   * __Multi-protocol.__ Input sources may be __Files, Http(s), Multicast, and Unicast UDP streams__.
   * Supports [__Live__](https://github.com/futzu/scte35-hls-x9k3#live) __Streaming__.
   * [__amt-play__ ](https://github.com/vivoh-inc/amt-play)uses x9k3.
---


## `Requires` 
* python 3.6+ or pypy3
* [threefive](https://github.com/futzu/scte35-threefive)  
* [new_reader](https://github.com/futzu/new_reader)
* [iframes](https://github.com/futzu/iframes)



## `Install`
* Use pip to install the the x9k3 lib and  executable script x9k3 (_will install threefive, new_reader and iframes too_)
```lua
# python3

python3 -mpip install x9k3

# pypy3 

pypy3 -mpip install x9k3
```

[⇪ top](https://github.com/futzu/x9k3/blob/main/README.md#hls--scte35--x9k3)
## `Details` 

*  __X-SCTE35__, __X-CUE__, __X-DATERANGE__, or __X-SPLICEPOINT__ HLS tags can be generated. set with the `--hls_tag` switch.

* reading from stdin now available
* Segments are cut on iframes.
* Segment time is 2 seconds or more, determined by GOP size. Can be set with the `-t` switch or by setting `X9K3.args.time` 
* Segments are named seg1.ts seg2.ts etc...
*  For SCTE-35, Video segments are cut at the the first iframe >=  the splice point pts.
*  If no pts time is present in the SCTE-35 cue, the segment is cut at the next iframe. 
* SCTE-35 cues with a preroll are inserted at the splice point.

## `How to Use`

---
* Cli Information Flags
---

<br>

| switch| description|
|-------|------------------------------------------------------|
| `-h`, `--help`        | show this help message and exit         |
| `-v`, `--version`| Show version                              |




* help `-h`
```smalltalk
a@fu:~$ x9k3 -h

```

* version `-v`

```smalltalk
a@fu:~$ x9k3 -v
0.2.35
a@fu:~$ 
```
---
* Cli Base Options
---
| switch| description|
|-------|------------|
|` -i INPUT`, `--input INPUT`| Input source, like /home/a/vid.ts or udp://@235.35.3.5:3535 or https://futzu.com/xaa.ts or https://example.com/not_a_master.m3u8 [default: stdin] |
| `-o OUTPUT_DIR`, `--output_dir OUTPUT_DIR`  |  Directory for segments and index.m3u8(created if needed) [default:'.'] |
| `-s SIDECAR_FILE`, `--sidecar_file SIDECAR_FILE`| Sidecar file of SCTE-35 (pts,cue) pairs. [default:None]  |
 | `-t TIME`, `--time TIME`|  Segment time in seconds [default:2]   |

---
* cli base options examples
---


```smalltalk
x9k3 -input  /home/a/vid.ts  
```
* input file and output directory
```smalltalk
x9k3 -i https://example.com/fu.ts   --output_dir /home/a/hls
```
* input from https , with an output directory
```smalltalk
x9k3 -i https://example.com/not_a_master.m3u8 -o /home/a/hls
```
* input from udp multicast, local sidecar file  
```smalltalk
x9k 3 --input udp://@235.35.3.5:3535  --sidecar_file sidecar.txt
```
* input from stdin, output directory, sidecar file 
```smalltalk
cat fu.ts | x9k3 -o /home/a/hls -s sidecar.t
```


---
* Writing Code with options. Up and Running in Six Lines.
---


1. import argue and X9K3
2. Call argue() to get a namespace of all available options.
   * All the above options are available
3. Set the options you want
4.  Create an X9K3 instance
5. Set  X9K3.args to your args
6.     6. Call X9K3.decode()



```smalltalk
        from x9k3 import argue, X9K3     # 1
        
        args = argue()                   # 2

        args.input='/home/a/cool.ts'     # 3

        x9 = X9K3()                      # 4

        x9.args = args                   # 5 

        x9.decode()                      # 6 
```


---
* Fine Tuning
---


| switch| description|
|-------|------------|
| `-T HLS_TAG`, `--hls_tag HLS_TAG`| x_scte35, x_cue, x_daterange, or x_splicepoint [default:x_cue] |
|`-w WINDOW_SIZE`, `--window_size WINDOW_SIZE`| sliding window size (enables --live) [default:5]    |
| `-l`, ` --live `      |   Flag for a live event (enables sliding window m3u8) [default:False] |


### Additional Flags
| switch| description|
|-------|------------|
 | `-c`, `--continue_m3u8` | Resume writing index.m3u8 [default:False]  |
 |` -d`, `--delete`   |   delete segments (enables --live) [default:False] |
 | `-n`, `--no_discontinuity`  | Flag to disable adding #EXT-X-DISCONTINUITY tags at splice points [default:False] |
 | `-N`, `--no-throttle`|   disable live throttling [default:False]   |
 | `-p`, `--program_date_time` | Flag to add Program Date Time tags to index.m3u8 (enables --live) [default:False]  |
 | `-r`, `--replay`   | Flag for replay aka looping (enables --live,--delete) [default:False]|
 | `-S`, `--shulga`|         Flag to enable Shulga iframe detection mode [default:False] |

| switch| description|
|-------|------------|
 | `-h`, `--help` |          show this help message and exit |
 | `-v`, `--version`|       Show version|

 
```smalltalk
a@fu:~/x9k3-repo$ x9k3 -h

usage: x9k3 [-h] [-i INPUT] [-c] [-d] [-l] [-n] [-o OUTPUT_DIR] [-p] [-r]
            [-s SIDECAR_FILE] [-S] [-t TIME] [-T HLS_TAG] [-w WINDOW_SIZE]
            [-v]


options:

  -h, --help            show this help message and exit

  -i INPUT, --input INPUT
                        Input source, like /home/a/vid.ts or
                        udp://@235.35.3.5:3535 or https://futzu.com/xaa.ts or
                        https://example.com/not_a_master.m3u8 [default: stdin]

  -c, --continue_m3u8   Resume writing index.m3u8 [default:False]

  -d, --delete          delete segments (enables --live) [default:False]

  -l, --live            Flag for a live event (enables sliding window m3u8)
                        [default:False]

  -n, --no_discontinuity
                        Flag to disable adding #EXT-X-DISCONTINUITY tags at
                        splice points [default:False]

  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory for segments and index.m3u8 (created if
                        needed) [default:'.']

  -p, --program_date_time
                        Flag to add Program Date Time tags to index.m3u8 (
                        enables --live) [default:False]

  -r, --replay          Flag for replay aka looping (enables --live,--delete)
                        [default:False]

  -s SIDECAR_FILE, --sidecar_file SIDECAR_FILE
                        Sidecar file of SCTE-35 (pts,cue) pairs.[default:None]

  -S, --shulga          Flag to enable Shulga iframe detection mode
                        [default:False]

  -t TIME, --time TIME  Segment time in seconds [default:2]

  -T HLS_TAG, --hls_tag HLS_TAG
                        x_scte35, x_cue, x_daterange, or x_splicepoint
                        [default:x_cue]

  -w WINDOW_SIZE, --window_size WINDOW_SIZE
                        sliding window size (enables --live) [default:5]

  -v, --version         Show version
```








</details>


### Example Usage

 #### `local file as input`
 ```smalltalk
    x9k3 -i video.mpegts
 ```
 #### `multicast stream as input with a live sliding window`   
   ```smalltalk
   x9k3 --live -i udp://@235.35.3.5:3535
   ```
  #### Live mode works with a live source or static files.
  *  x9k3 will throttle segment creation to mimic a live stream.
   ```js
   x9k3 --live -i /some/video.ts
   ```
 #### `live sliding window and deleting expired segments`
   ```smalltalk
   x9k3  -i udp://@235.35.3.5:3535 --delete
   ```
#### `https stream for input, and writing segments to an output directory`
   *  directory will be created if it does not exist.
 ```smalltalk
   x9k3 -i https://so.slo.me/longb.ts --output_dir /home/a/variant0
 ```
#### `https hls m3u8 for input, and inserting SCTE-35 from a sidecar file, and continuing from a previously create index.m3u8 in the output dir`
 ```smalltalk
   x9k3 -i https://slow.golf/longb.m3u8 --output_dir /home/a/variant0 -continue_m3u8 -s sidecar.txt
 ```  
#### `using stdin as input`
   ```smalltalk
   cat video.ts | x9k3
   ```
#### `live m3u8 file as input, add SCTE-35 from a sidecar file, change segment duration to 3 and output as live stream`
```smalltalk
x9k3 -i https://example.com/rendition.m3u8 -s sidecar.txt -t 3 -l
```
[⇪ top](https://github.com/futzu/x9k3/blob/main/README.md#hls--scte35--x9k3)

# `Cli tool`

#### New Option, `-c` or  `--continue_m3u8` Continue an existing index.m3u8. _(Only works with x9k3 generated m3u8 files)_

```smalltalk
a@fu:~/x9k3-repo$ x9k3 -h

usage: x9k3 [-h] [-i INPUT] [-c] [-d] [-l] [-n] [-o OUTPUT_DIR] [-p] [-r]
            [-s SIDECAR_FILE] [-S] [-t TIME] [-T HLS_TAG] [-w WINDOW_SIZE]
            [-v]


options:

  -h, --help            show this help message and exit

  -i INPUT, --input INPUT
                        Input source, like /home/a/vid.ts or
                        udp://@235.35.3.5:3535 or https://futzu.com/xaa.ts or
                        https://example.com/not_a_master.m3u8 [default: stdin]

  -c, --continue_m3u8   Resume writing index.m3u8 [default:False]

  -d, --delete          delete segments (enables --live) [default:False]

  -l, --live            Flag for a live event (enables sliding window m3u8)
                        [default:False]

  -n, --no_discontinuity
                        Flag to disable adding #EXT-X-DISCONTINUITY tags at
                        splice points [default:False]

  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory for segments and index.m3u8 (created if
                        needed) [default:'.']

  -p, --program_date_time
                        Flag to add Program Date Time tags to index.m3u8 (
                        enables --live) [default:False]

  -r, --replay          Flag for replay aka looping (enables --live,--delete)
                        [default:False]

  -s SIDECAR_FILE, --sidecar_file SIDECAR_FILE
                        Sidecar file of SCTE-35 (pts,cue) pairs.[default:None]

  -S, --shulga          Flag to enable Shulga iframe detection mode
                        [default:False]

  -t TIME, --time TIME  Segment time in seconds [default:2]

  -T HLS_TAG, --hls_tag HLS_TAG
                        x_scte35, x_cue, x_daterange, or x_splicepoint
                        [default:x_cue]

  -w WINDOW_SIZE, --window_size WINDOW_SIZE
                        sliding window size (enables --live) [default:5]

  -v, --version         Show version
```


#### Programmatically (writing code with x9k3) 
```js
x9 = X9K3("https://iodisco.com/fu.ts")
x9.decode()
```
Setting  parameters
* create an instance.
```js
x9 = X9K3()
```
*  input source

```js
x9.args.input = "https://futzu.com/xaa.ts"   
```
* hls_tag can be x_scte35, x_cue, x_daterange, or x_splicepoint

```js
x9.args.hls tag = x_cue 
```
* output directory default is "."
```js
x9.args.output_dir="/home/a/stuff"
```
* live
```js 
x9.args.live = True
```
* replay (loop video) ( also sets live )
```js
x9.args.replay = True
```
* delete segments when they expire ( also sets live )
```js
x9.args.delete = True
```

* add program date time tags ( also sets live )
```js
self.args.program_date_time= True
```
* set window size for live mode ( requires live ) 
```js
x9.args.window_size = 5 
```
* run 
```js
x9.run()
```
* you can get a complete set of args and the defaults like this
```js
from x9k3 import X9K3
x9 = X9K3()
print(x9.args)

Namespace(input=<_io.BufferedReader name='<stdin>'>, continue_m3u8=False, delete=False, live=False, no_discontinuity=False, output_dir='.', program_date_time=False, replay=False, sidecar_file=None, shulga=False, time=2, hls_tag='x_cue', window_size=5, version=False)


```
* argue can also be called to get the defaults
```js
>>>> from x9k3 import X9K3, argue
>>>> args = argue()

>>>> args
Namespace(input=<_io.BufferedReader name='<stdin>'>, continue_m3u8=False, delete=False, live=False, no_discontinuity=False, output_dir='.', program_date_time=False, replay=False, sidecar_file=None, shulga=False, time=2, hls_tag='x_cue', window_size=5, version=False)

>>>> args.replay =True
>>>> args.live = True
>>>> args.time = 6
>>>> args.window_size = 10

>>>> args
Namespace(input=<_io.BufferedReader name='<stdin>'>, continue_m3u8=False, delete=False, live=True, no_discontinuity=False, output_dir='.', program_date_time=False, replay=True, sidecar_file=None, shulga=False, time=6, hls_tag='x_cue', window_size=10, version=False)

>>>> x9 = X9K3()
>>>> x9.args = args

>>>> x9.args
Namespace(input=<_io.BufferedReader name='<stdin>'>, continue_m3u8=False, delete=False, live=True, no_discontinuity=False, output_dir='.', program_date_time=False, replay=True, sidecar_file=None, shulga=False, time=6, hls_tag='x_cue', window_size=10, version=False)

```
[⇪ top](https://github.com/futzu/x9k3/blob/main/README.md#hls--scte35--x9k3)
 

### `Sidecar Files`   
#### load scte35 cues from a Sidecar file

    
Sidecar Cues will be handled the same as SCTE35 cues from a video stream.   
line format for text file  `insert_pts, cue`
    
    
pts is the insert time for the cue, A four second preroll is standard. 
cue can be base64,hex, int, or bytes
     
  ```smalltalk
  a@debian:~/x9k3$ cat sidecar.txt
  
  38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ== 
  38199.918911, /DAsAAAAAAAAAP/wDwUAAABef0/+zPACTQAAAAAADAEKQ1VFSbGfMTIxIxGolm0= 

      
```
  ```smalltalk
  x9k3 -i  noscte35.ts  -s sidecar.txt 
  ```
####   In Live Mode you can do dynamic cue injection with a `Sidecar file`
   ```js
   touch sidecar.txt
   
   x9k3 -i vid.ts -s sidecar.txt -l 
   
   # Open another terminal and printf cues into sidecar.txt
   
   printf '38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==\n' > sidecar.txt
   
   ```
#### `Sidecar files` can now accept 0 as the PTS insert time for Splice Immediate. 
 
 

 Specify 0 as the insert time,  the cue will be insert at the start of the next segment.
 __Using 0 only works in live mode__

 ```js
 printf '0,/DAhAAAAAAAAAP/wEAUAAAAJf78A/gASZvAACQAAAACokv3z\n' > sidecar.txt

 ```
 [⇪ top](https://github.com/futzu/x9k3/blob/main/README.md#hls--scte35--x9k3)

 ####  A CUE-OUT can be terminated early using a `sidecar file`.

 
 In the middle of a CUE-OUT send a splice insert with the out_of_network_indicator flag not set and the splice immediate flag set.
 Do the steps above ,
 and then do this
 ```js
 printf '0,/DAcAAAAAAAAAP/wCwUAAAABfx8AAAEAAAAA3r8DiQ==\n' > sidecar.txt
```
 It will cause the CUE-OUT to end at the next segment start.
 ```js
#EXT-X-CUE-OUT 13.4
./seg5.ts:	start:112.966667	end:114.966667	duration:2.233334
#EXT-X-CUE-OUT-CONT 2.233334/13.4
./seg6.ts:	start:114.966667	end:116.966667	duration:2.1
#EXT-X-CUE-OUT-CONT 4.333334/13.4
./seg7.ts:	start:116.966667	end:118.966667	duration:2.0
#EXT-X-CUE-OUT-CONT 6.333334/13.4
./seg8.ts:	start:117.0	        end:119.0	duration:0.033333
#EXT-X-CUE-IN None
./seg9.ts:	start:119.3	        end:121.3	duration:2.3

``` 
 __Using 0 only works in live mode__

   ---
## CUES   
   
##   `CUE-OUT`
#### A CUE-OUT is defined as:

* `A Splice Insert Command` with:
   *  the `out_of_network_indicator` set to `True` 
   *  a `break_duration`.
        
* `A Time Signal Command` and a Segmentation Descriptor with:
   *  a `segmentation_duration` 
   *  a `segmentation_type_id` of:
      * 0x22: "Break Start",
      * 0x30: "Provider Advertisement Start",
      * 0x32: "Distributor Advertisement Start",
      * 0x34: "Provider Placement Opportunity Start",
      * 0x36: "Distributor Placement Opportunity Start",
      * 0x44: "Provider Ad Block Start",
      * 0x46: "Distributor Ad Block Start",

[⇪ top](https://github.com/futzu/x9k3/blob/main/README.md#hls--scte35--x9k3)

## `CUE-IN`
#### A CUE-IN is defined as:
* `A Splice Insert Command`
  *  with the `out_of_network_indicator` set to `False`

* `A Time Signal Command` and a Segmentation Descriptor with:
   *  a `segmentation_type_id` of:

      * 0x23: "Break End",
      * 0x31: "Provider Advertisement End",
      * 0x33: "Distributor Advertisement End",
      * 0x35: "Provider Placement Opportunity End",
      * 0x37: "Distributor Placement Opportunity End",
      * 0x45: "Provider Ad Block End",
      * 0x47: "Distributor Ad Block End",

* For CUE-OUT and CUE-IN, `only the first Segmentation Descriptor will be used`
---
    
## `Supported HLS  Tags`
* #EXT-X-CUE 
* #EXT-X-DATERANGE 
* #EXT-X-SCTE35 
* #EXT-X-SPLICEPOINT 

###  `x_cue`
* CUE-OUT
```lua
#EXT-X-DISCONTINUITY
#EXT-X-CUE-OUT:242.0
#EXTINF:4.796145,
seg32.ts
```
* CUE-OUT-CONT
```lua
#EXT-X-CUE-OUT-CONT:4.796145/242.0
#EXTINF:2.12,
```
* CUE-IN
```lua
#EXT-X-DISCONTINUITY
#EXT-X-CUE-IN
#EXTINF:5.020145,
seg145.ts

```
### `x_scte35`
* CUE-OUT
```lua
#EXT-X-DISCONTINUITY
#EXT-X-SCTE35:CUE="/DAvAAAAAAAAAP/wFAUAAAKWf+//4WoauH4BTFYgAAEAAAAKAAhDVUVJAAAAAOv1oqc=" ,CUE-OUT=YES 
#EXTINF:4.796145,
seg32.ts
```
* CUE-OUT-CONT
```lua
#EXT-X-SCTE35:CUE="/DAvAAAAAAAAAP/wFAUAAAKWf+//4WoauH4BTFYgAAEAAAAKAAhDVUVJAAAAAOv1oqc=" ,CUE-OUT=CONT
#EXTINF:2.12,
seg33.ts
```
* CUE-IN
```lua
#EXT-X-DISCONTINUITY
#EXT-X-SCTE35:CUE="/DAqAAAAAAAAAP/wDwUAAAKWf0//4rZw2AABAAAACgAIQ1VFSQAAAAAtegE5" ,CUE-IN=YES 
#EXTINF:5.020145,
seg145.ts
```
### `x_daterange`
* CUE-OUT
```lua
#EXT-X-DISCONTINUITY
#EXT-X-DATERANGE:ID="1",START-DATE="2022-10-14T17:36:58.321731Z",PLANNED-DURATION=242.0,SCTE35-OUT=0xfc302f00000000000000fff01405000002967fefffe16a1ab87e014c562000010000000a00084355454900000000ebf5a2a7
#EXTINF:4.796145,
seg32.ts
```
* CUE-IN
```lua
#EXT-X-DISCONTINUITY
#EXT-X-DATERANGE:ID="2",END-DATE="2022-10-14T17:36:58.666073Z",SCTE35-IN=0xfc302a00000000000000fff00f05000002967f4fffe2b670d800010000000a000
843554549000000002d7a0139
#EXTINF:5.020145,
seg145.ts
```

### `x_splicepoint`
* CUE-OUT
```lua
#EXT-X-DISCONTINUITY
#EXT-X-SPLICEPOINT-SCTE35:/DAvAAAAAAAAAP/wFAUAAAKWf+//4WoauH4BTFYgAAEAAAAKAAhDVUVJAAAAAOv1oqc=
#EXTINF:4.796145,
seg32.ts
```
* CUE-IN
```lua
#EXT-X-DISCONTINUITY
#EXT-X-SPLICEPOINT-SCTE35:/DAqAAAAAAAAAP/wDwUAAAKWf0//4rZw2AABAAAACgAIQ1VFSQAAAAAtegE5
#EXTINF:5.020145,
seg145.ts

```
[⇪ top](https://github.com/futzu/x9k3/blob/main/README.md#hls--scte35--x9k3)

## `VOD`

* x9k3 defaults to VOD style playlist generation.
* All segment are listed in the m3u8 file. 

## `Live`
* Activated by the `--live`, `--delete`, or `--replay` switch or by setting `X9K3.live=True`

### `--live`
   * Like VOD except:
     * M3u8 manifests are regenerated every time a segment is written
     * Segment creation is throttled when using non-live sources to simulate live streaming. ( like ffmpeg's "-re" )
     * default Sliding Window size is 5, it can be changed with the `-w` switch or by setting `X9k3.window.size` 
###  `--delete`
  * implies `--live`
  * deletes segments when they move out of the sliding window of the m3u8.
### `--replay`
  * implies `--live`
  * implies `--delete`
  * loops a video file and throttles segment creation to fake a live stream.

[⇪ top](https://github.com/futzu/x9k3/blob/main/README.md#hls--scte35--x9k3)


   ![image](https://github.com/futzu/x9k3/assets/52701496/65d915f9-8721-4386-9353-2e32911c6a64)

   
 






