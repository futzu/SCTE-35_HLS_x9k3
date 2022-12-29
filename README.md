 [Install](#install) |
 [Use](#how-to-use) |
 [CUE-OUT](#cue-out) |
 [CUE-IN](#cue-in)   |
 [SCTE-35 Tags](#hls--tags) |
 [Sidecar SCTE35](#load-scte35-cues-from-a-text-file) |
 [Live](#live)  |
 [Bugs](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues)
<details>
<summary><h1>Heads Up </h1>(click to expand)</summary>

 __I am working on a rewrite of x9k3__, there is too much code in the current version.

>After working with x9k3 for a while, there are some things I would do differently.
> I am going to do them differently now.

> __Why am I telling you this?__ 

> Because __I will be breaking things__ and I will __not__ be adding features __nor__ will I be addressing bugs.
>
> I am __not__ going to maintain two versions,I am going to work out of the main repo, 
>
> For the next few weeks __the git repo will not be stable.__
>
> __v.0.1.75 is the current stable version__. It is available via __pip__.
> __v.0.1.77 is the new remix version__ _(discretion is the better part of valor, go slow.)_  . It is available via __pip__.

### Update 13/29/2022
#### How accurate is the new x9k3? 
```js
#EXT-X-CUE-OUT-CONT:237.459978/242.0
#EXTINF:2.060000,
./seg141.ts
#EXT-X-CUE-OUT-CONT:239.519978/242.0
#EXTINF:2.300000,
./seg142.ts
#EXT-X-CUE-OUT-CONT:241.819978/242.0
#EXTINF:0.180022,                   #    Boom << Boom
./seg143.ts
#EXT-X-DISCONTINUITY
#EXT-X-CUE-IN
#EXTINF:2.139978,
```

### Update 12/28/2022
* `live/ fake live throttling` is working 
 * `Everything is now working` 
   * I need to do a little more testing, probably package it up for pip, Friday.  

### Update 12/27/2022
* Added `argparse` stuff
* Added looping
* I still need to add
     * `live throttling`

### Update 12/26/2022
> One of the main goals was to simply the logic used to cut segments, I have done that and I feel much better this code.   
This morning I turned on:
* `discontinuity tags`
* `program datetime flags`
* `discontinuity media sequence header`
* `shulga mode`
* `automatic break auto return`
* `sidecar file loading`
* `expired segment deleting`
* `Super accurate slicing`
* `CUE-OUT CONT timers`


### Update 12/25/2022
The remix is going very well. I still need to finish these parts. 

* CUE-OUT CONT timers
* break auto return
* throttling for live and fake live streaming
* adding command line arguments. 
> I am thinking I need another week to get it caught up.
</details>

# `x9k3` is a HLS segmenter with SCTE-35 parsing and cue injection.
### `Latest` is `v.0.1.75`
### `Remixed` is `v.0.1.77` _(discretion is the better part of valor, go slow)_ 
### Supported SCTE-35 HLS Tags 

 - [x] `#EXT-X-SCTE35` 
 - [x] `#EXT-X-CUE` 
 - [x] `#EXT-X-DATERANGE`  
 - [x] `#EXT-X-SPLICEPOINT` 
 
   * __SCTE-35 Cues__ in __Mpegts Streams__ are Translated into __HLS tags__.
   * __SCTE-35 Cues can be added from a [Sidecar File](https://github.com/futzu/x9k3/blob/main/README.md#load-scte35-cues-from-a-text-file)__.
   * Segments are __Split on SCTE-35 Cues__ as needed.
   * Supports __h264__ and __h265__ .
   * __Multi-protocol.__ Input sources may be __Files, Http(s), Multicast, and Udp streams__.
   * Supports [__Live__](https://github.com/futzu/scte35-hls-x9k3#live) __Streaming__.
   * [__amt-play__ ](https://github.com/vivoh-inc/amt-play)uses x9k3.
---

## `Details` 

*  __X-SCTE35__, __X-CUE__, __X-DATERANGE__, or __X-SPLICEPOINT__ HLS tags can be generated. set with the `--hls_tag` switch.


*  reading from stdin now available

```lua
 cat somevideo.ts | x9k3 

```


* Segments are cut on iframes.

* Segment size is 2 seconds or more, determined by GOP size. 
* Segments are named seg1.ts seg2.ts etc...

*  For SCTE-35, Video segments are cut at the the first iframe >=  the splice point pts.
*  If no pts time is present in the SCTE-35 cue, the segment is cut at the next iframe. 


```smalltalk
# Time Signal
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:2.085422,
seg1.ts
```

#### `SCTE-35 cues with a preroll are inserted at the splice point`

```smalltalk
# Splice Point @ 17129.086244
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:0.867544,
seg2.ts

```


## `Requires` 
* python 3.6+ or pypy3
* [threefive](https://github.com/futzu/scte35-threefive)  
* [new_reader](https://github.com/futzu/new_reader)
* [iframes](https://github.com/futzu/iframes)

## `Install`
* Use pip to install the the x9k3 lib and  executable script x9k3 (_will install threefive, new_reader and iframes too_)
```
# python3

python3 -mpip install x9k3

# pypy3 

pypy3 -mpip install x9k3
```

## `How to Use`
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

## `Example Usage`

 #### `local file as input`
 ```smalltalk
    x9k3 -i video.mpegts
 ```
  
 #### `multicast stream as input with a live sliding window`   
   ```smalltalk
   x9k3 --live -i udp://@235.35.3.5:3535
   ```
 
 
 #### `use ffmpeg to read multicast stream as input and x9k3 to segment`
      with a sliding window, and  expiring old segments.
       --delete implies --live
      
   ```smalltalk
    ffmpeg  -re -copyts -i udp://@235.35.3.5:3535 -map 0 -c copy -f mpegts - | x9k3 --delete
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
   
#### `load scte35 cues from a text file`
    
    Sidecar Cues will be handled the same as SCTE35 cues from a video stream.
    
    line format for text file : pts, cue
    
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
####   `In Live Mode you can do dynamic cue injection`
   ```smalltalk
   touch sidecar.txt
   
   x9k3 -i vid.ts -s sidecar.txt -l 
   
   # Open another terminal and printf cues into sidecar.txt
   
   printf '38103.868589, /DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==\n' > sidecar.txt
   
   ```
   ---
##   `CUE-OUT`

* `A Splice Insert Command` with:
   *  the `out_of_network_indicator` set to `True` 
   *  a `break_duration`.
        
* `A Time Signal Command` with:
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

* `A Splice Insert Command`
  *  with the `out_of_network_indicator` set to `False`

* `A Time Signal Command` with:
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
   
    ---
## `HLS  Tags`
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
     * Sliding Window for 5 [WINDOW_SLOTS](https://github.com/futzu/scte35-hls-x9k3/blob/main/x9k3.py#L118)
     * A cue out continue tag is added to first segment in manifest during an ad break.
###  `--delete`
  * implies `--live`
  * deletes segments when they move out of the sliding window of the m3u8.
### `--replay`
  * implies `--live`
  * implies `--delete`
  * loops a video file and throttles segment creation to fake a live stream.



## `Stream Diff`

* stream diff is the difference between the playback time of the stream and generation of segments by x9k3.

*  A segment with a 2 second duration that takes 0.5 seconds to generate would have a stream diff of 1.5.
 

* __In the default mode, stream_diff is a benchmark of playlist generation.__
 
 ```lua
 a@debian:~/x9k3$ time x9k3  -i local-vid.ts 
 ./seg0.ts	start:  3.545000	duration:  2.112000	stream diff:  2.094049
 ./seg1.ts	start:  5.593000	duration:  2.048000	stream diff:  4.133058
   ...
   
 ./seg77.ts	start:  163.011667	duration:  2.176000	stream diff:  161.307591
 ./seg78.ts	start:  165.187667	duration:  2.176000	stream diff:  163.482903 <-- big stream diff

real	0m0.482s             <--  fast segmenting for VOD
user	0m0.334s
sys	0m0.128s

```
   
* stream_diff with `--live` or `--delete` or `--replay`

   * stream_diff automatically throttles non-live streams for realtime playback . 
   * stream_diff keeps segmentation and the sliding window in sync.
 
 ```lua
 a@debian:~/x9k3$ time x9k3 -i local-vid.ts --live
 ./seg0.ts	start:  1.433000	duration:  2.112000	stream diff:  1.749682
 ./seg1.ts	start:  3.545000	duration:  2.048000	stream diff:  1.664505
 ./seg2.ts	start:  5.593000	duration:  2.005333	stream diff:  1.604484
 ./seg3.ts	start:  7.598333	duration:  2.026667	stream diff:  1.608694
 
 ...
 
 ./seg76.ts	start:  158.617000	duration:  2.218667	stream diff:  0.151273
 ./seg77.ts	start:  160.835667	duration:  2.176000	stream diff:  0.101823
 ./seg78.ts	start:  163.011667	duration:  2.176000	stream diff:  0.100369  <-- small stream diff

real	2m44.775s   <-- real time segmenting to sync live stream sliding window
user	0m0.678s
sys	0m0.169s
```
 


   
   
 






