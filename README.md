 [Install](#install) |
 [Use](#how-to-use) |
 [CUE-OUT](#cue-out) |
 [CUE-IN](#cue-in)   |
 [SCTE-35 Tags](#hls--tags) |
 [Sidecar SCTE35](#sidecar-files) |
 [Live](#live)  |
 [Bugs](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues)

# HLS + SCTE35 = x9k3
## `x9k3` is a HLS segmenter with SCTE-35 parsing and cue injection.
### `Latest` is `v.0.1.85` 

   * __SCTE-35 Cues__ in __Mpegts Streams__ are Translated into __HLS tags__.
   * __SCTE-35 Cues can be added from a [Sidecar File](#sidecar-files)__.
   * Segments are __Split on SCTE-35 Cues__ as needed.
   * Supports __h264__ and __h265__ .
   * __Multi-protocol.__ Input sources may be __Files, Http(s), Multicast, and Udp streams__.
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

### `Example Usage`

 #### `local file as input`
 ```smalltalk
    x9k3 -i video.mpegts
 ```
 #### `multicast stream as input with a live sliding window`   
   ```smalltalk
   x9k3 --live -i udp://@235.35.3.5:3535
   ```
  #### Live mode works with a live source or static files.
  
   ```js
   # x9k3 will throttle segment creation to mimic a live stream.
   x9k3 --live -i /some/video.ts
   ```
 #### `live sliding window and deleting expired segments`
   ```smalltalk
   x9k3  -i udp://@235.35.3.5:3535 --delete
   ```
#### `https stream for input, and writing segments to an output directory`
      directory will be created if it does not exist.
 ```smalltalk
   x9k3 -i https://so.slo.me/longb.ts --output_dir /home/a/variant0
 ```
  
#### `using stdin as input`
   ```smalltalk
   cat video.ts | x9k3
   ```
   
#### Cli tool

```smalltalk
a@debian:~/build/x9k3$ x9k3 -h
usage: x9k3 [-h] [-i INPUT] [-o OUTPUT_DIR] [-s SIDECAR] [-t TIME]
            [-T HLS_TAG] [-w WINDOW_SIZE] [-d] [-l] [-r] [-S] [-v] [-p]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT  
                        Input source, like "/home/a/vid.ts" or
                        "udp://@235.35.3.5:3535" or "https://futzu.com/xaa.ts"
                                             
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory for segments and index.m3u8 ( created if it
                        does not exist )
  -s SIDECAR, --sidecar SIDECAR
                        Sidecar file of scte35 cues. each line contains PTS,
                        Cue
  -t TIME, --time TIME  Segment time in seconds ( default is 2)
  -T HLS_TAG, --hls_tag HLS_TAG
                        x_scte35, x_cue, x_daterange, or x_splicepoint
                        (default x_cue)
  -w WINDOW_SIZE, --window_size WINDOW_SIZE
                        sliding window size(default:5)
  -d, --delete          delete segments ( enables --live )
  -l, --live            Flag for a live event ( enables sliding window m3u8 )
  -r, --replay          Flag for replay (looping) ( enables --live and
                        --delete )
  -S, --shulga          Flag to enable Shulga iframe detection mode
  -v, --version         Show version
  -p, --program_date_time
                        Flag to add Program Date Time tags to index.m3u8 (
                        enables --live)

```

#### Programmatically
```js
x9 = X9K3("https://iodisco.com/fu.ts")
x9.run()
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
      * 0x10: "Program Start",
      * 0x20: "Chapter Start"
      * 0x22: "Break Start",
      * 0x30: "Provider Advertisement Start",
      * 0x32: "Distributor Advertisement Start",
      * 0x34: "Provider Placement Opportunity Start",
      * 0x36: "Distributor Placement Opportunity Start",
      * 0x3C: "Provider Promo Start",
      * 0x3E: "Distributor Promo Start",
      * 0x44: "Provider Ad Block Start",
      * 0x46: "Distributor Ad Block Start",


## `CUE-IN`
#### A CUE-IN is defined as:
* `A Splice Insert Command`
  *  with the `out_of_network_indicator` set to `False`

* `A Time Signal Command` and a Segmentation Descriptor with:
   *  a `segmentation_type_id` of:
      *  0x11: "Program End",
      * 0x21: "Chapter End",
      * 0x23: "Break End",
      * 0x31: "Provider Advertisement End",
      * 0x33: "Distributor Advertisement End",
      * 0x35: "Provider Placement Opportunity End",
      * 0x37: "Distributor Placement Opportunity End",
      * 0x3D: "Provider Promo End",
      * 0x3F: "Distributor Promo End",
      * 0x45: "Provider Ad Block End",
      * 0x47: "Distributor Ad Block End",

* For CUE-OUT and CUE-IN, `only the first Segmentation Descriptor will be used`
---
    
## `HLS  Tags`
#### These are the HLS tags that can be generated.

####  `x_cue`
```lua
#EXT-X-DISCONTINUITY
# Splice Point @ 89742.161689
#EXT-X-CUE-OUT:242.0
#PTS 89739.505522
#EXTINF:4.796145,
seg32.ts


#EXT-X-CUE-OUT-CONT:4.796145/242.0
#PTS 89744.301667
#EXTINF:2.12,


#EXT-X-DISCONTINUITY
# Splice Point @ 89984.161689
#EXT-X-CUE-IN
#PTS 89981.281522
#EXTINF:5.020145,
seg145.ts

```
#### `x_scte35`
```lua
#EXT-X-DISCONTINUITY
# Splice Point @ 89742.161689
#EXT-X-SCTE35:CUE="/DAvAAAAAAAAAP/wFAUAAAKWf+//4WoauH4BTFYgAAEAAAAKAAhDVUVJAAAAAOv1oqc=" ,CUE-OUT=YES 
#PTS 89739.505522
#EXTINF:4.796145,
seg32.ts

#EXT-X-SCTE35:CUE="/DAvAAAAAAAAAP/wFAUAAAKWf+//4WoauH4BTFYgAAEAAAAKAAhDVUVJAAAAAOv1oqc=" ,CUE-OUT=CONT
#PTS 89744.301667
#EXTINF:2.12,
seg33.ts

#EXT-X-DISCONTINUITY
# Splice Point @ 89984.161689
#EXT-X-SCTE35:CUE="/DAqAAAAAAAAAP/wDwUAAAKWf0//4rZw2AABAAAACgAIQ1VFSQAAAAAtegE5" ,CUE-IN=YES 
#PTS 89981.281522
#EXTINF:5.020145,
seg145.ts
```
#### `x_daterange`
```lua
#EXT-X-DISCONTINUITY
# Splice Point @ 89742.161689
#EXT-X-DATERANGE:ID="1",START-DATE="2022-10-14T17:36:58.321731Z",PLANNED-DURATION=242.0,SCTE35-OUT=0xfc302f00000000000000fff01405000002967fefffe16a1ab87e014c562000010000000a00084355454900000000ebf5a2a7
#PTS 89739.505522
#EXTINF:4.796145,
seg32.ts



#EXT-X-DISCONTINUITY
# Splice Point @ 89984.161689
#EXT-X-DATERANGE:ID="2",END-DATE="2022-10-14T17:36:58.666073Z",SCTE35-IN=0xfc302a00000000000000fff00f05000002967f4fffe2b670d800010000000a000
843554549000000002d7a0139
#PTS 89981.281522
#EXTINF:5.020145,
seg145.ts
```

#### `x_splicepoint`
```lua
#EXT-X-DISCONTINUITY
# Splice Point @ 89742.161689
#EXT-X-SPLICEPOINT-SCTE35:/DAvAAAAAAAAAP/wFAUAAAKWf+//4WoauH4BTFYgAAEAAAAKAAhDVUVJAAAAAOv1oqc=
#PTS 89739.505522
#EXTINF:4.796145,
seg32.ts

#EXT-X-DISCONTINUITY
# Splice Point @ 89984.161689
#EXT-X-SPLICEPOINT-SCTE35:/DAqAAAAAAAAAP/wDwUAAAKWf0//4rZw2AABAAAACgAIQ1VFSQAAAAAtegE5
#PTS 89981.281522
#EXTINF:5.020145,
seg145.ts


```

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



   
   
 






