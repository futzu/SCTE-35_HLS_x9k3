[Details](#details)  |
 [Install](#requires) |
 [Use](#how-to-use) |
 [Customize](#faq)  |
 [Live Events](#live)  |
 [Bugs](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues)  |
 [Feedback](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues)  |
 [Cue](https://github.com/futzu/scte35-threefive/blob/master/cue.md)  |
 [Stream Diff](#stream-diff)  |
 [Sidecar SCTE35](#load-scte35-cues-from-a-text-file)


# `x9k3`
##  `HLS Segmenter with SCTE-35 Baked In`
   * __SCTE-35 Cues__ in __Mpegts Streams__ are Translated into __HLS tags__.
   * Segments are __Split on SCTE-35 Cues__ as needed.
   * __M3U8__ Manifests are created with __SCTE-35 HLS tags__.
   * Supports __h264__ and __h265__ and __mpeg2__ video.
   * __Multi-protocol.__ Files, __Http(s)__, __Multicast__, and __Udp__.
   * Supports [__Live__](https://github.com/futzu/scte35-hls-x9k3#live) __Streaming__.
   * [__Customizable__](https://github.com/futzu/scte35-hls-x9k3/blob/main/README.md#faq)  Ad Break __Criteria__
   *  __SCTE-35 Cues Can Now Load from a [Sidecar File](https://github.com/futzu/x9k3/blob/main/README.md#load-scte35-cues-from-a-text-file)__.



## `Requires` 
* python 3.6+ or pypy3
* [threefive](https://github.com/futzu/scte35-threefive)  
```smalltalk
pip3 install threefive
```

## `How to Use`

```smalltalk
a@debian:~/x9k3$ pypy3 x9k3.py -h

usage: x9k3.py [-h] [-i INPUT] [-o OUTPUT_DIR] [-s SIDECAR] [-l] [-d]

optional arguments:

  -h, --help            show this help message and exit

  -i INPUT, --input INPUT
                        Input source, like "/home/a/vid.ts" or "udp://@235.35.3.5:3535" or
                        "https://futzu.com/xaa.ts"

  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory for segments and index.m3u8 ( created if it does not exist )
  
  -s SIDECAR, --sidecar SIDECAR
                        sidecar file of scte35 cues. each line contains (PTS, CueString) Example:
                        89718.451333, /DARAAAAAAAAAP/wAAAAAHpPv/8=
  
  -l, --live            Flag for a live event ( enables sliding window m3u8 )
  
  -d, --delete          delete segments ( enables live mode )


```
## `Example Usage`

 #### `local file as input`
 ```smalltalk
    python3 x9k3.py -i video.mpegts
 ```
  
 #### `multicast stream as input with a live sliding window`   
   ```smalltalk
   python3 x9k3.py --live -i udp://@235.35.3.5:3535
   ```
 
 
 #### `use ffmpeg to read multicast stream as input and x9k3 to segment`
      with a sliding window, and  expiring old segments.
       --delete implies --live
      
   ```smalltalk
    ffmpeg  -re -copyts -i udp://@235.35.3.5:3535 -map 0 -c copy -f mpegts - | python3 x9k3.py --delete
   ```
 
#### `https stream for input, and writing segments to an output directory`
      directory will be created if it does not exist.
  ```smalltalk
   pypy3 x9k3.py -i https://so.slo.me/longb.ts --output_dir /home/a/variant0
  ```
  
#### `using stdin as input`
   ```smalltalk
   cat video.ts | python3 x9k3.py
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
  pypy3 x9k3.py -i  noscte35.ts  -s sidecar.txt 
  ```
---

## `Details` 

* Segments are cut on iframes.

* Segment size is 2 seconds or more, determined by GOP size. 
* Segments are named seg1.ts seg2.ts etc...

*  For SCTE-35, Video segments are cut at the the first iframe >=  the splice point pts.
*  If no pts time is present in the SCTE-35 cue, the segment is cut at the next iframe. 

*  SCTE-35 cues are added when received.

*  All SCTE35 cue commands are added.

```smalltalk
# Time Signal
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:2.085422,
seg1.ts
```

#### `SCTE-35 cues with a preroll are inserted again at the splice point`

```smalltalk
# Splice Point @ 17129.086244
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:0.867544,
seg2.ts

```

####  `CUE-OUT ans CUE-IN are added at the splice point`

```smalltalk
#EXT-X-SCTE35:CUE="/DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==" CUE-OUT=YES
#EXTINF:1.668334,
seg13.ts

```

## `VOD`

* x9k3 defaults to VOD style playlist generation.
* All segment are listed in the m3u8 file. 

## `Live`

 * Activated by the `--live` switch or by setting `X9K3.live=True`

 * Like VOD except:
     * M3u8 manifests are regenerated every time a segment is written.
     * Segments are generated to realtime, even if the stream isn't live. ( like ffmpeg's "-re" ) 
     * Sliding Window for 5 [WINDOW_SLOTS](https://github.com/futzu/scte35-hls-x9k3/blob/main/x9k3.py#L118)
     * A cue out continue tag is added to first segment in manifest during an ad break.  

```smalltalk
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:3
#EXT-X-SCTE35:CUE="/DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==",CUE-OUT=CONT
#EXTINF:2.002,
seg43.ts
#EXTINF:2.002,
seg44.ts
#EXTINF:2.002,
seg45.ts
# Splice Insert
#EXT-X-SCTE35:CUE="/DAsAAAAAAAAAP/wDwUAAABef0/+zPACTQAAAAAADAEKQ1VFSbGfMTIxIxGolm0="
#EXTINF:2.168834,
seg46.ts
# Splice Point @ 38203.125478
#EXT-X-SCTE35:CUE="/DAsAAAAAAAAAP/wDwUAAABef0/+zPACTQAAAAAADAEKQ1VFSbGfMTIxIxGolm0=",CUE-IN=YES
#EXTINF:1.001,
seg47.ts
#EXTINF:2.836166,
seg48.ts
#EXTINF:2.002,
seg49.ts
#EXTINF:2.002,
....
```

## `Stream Diff`

* stream diff is the difference between the playback time of the stream and generation of segments by x9k3.

*  A segment with a 2 second duration that takes 0.5 seconds to generate would have a stream diff of 1.5.
 

* __In the default mode, stream_diff is a benchmark of playlist generation.__
 
 ```lua
 a@debian:~/x9k3$ time pypy3 x9k3.py  -i local-vid.ts 
 ./seg0.ts	start:  3.545000	duration:  2.112000	stream diff:  2.094049
 ./seg1.ts	start:  5.593000	duration:  2.048000	stream diff:  4.133058
 ./seg2.ts	start:  7.598333	duration:  2.005333	stream diff:  6.133111
 ./seg3.ts	start:  9.625000	duration:  2.026667	stream diff:  8.151764
 ./seg4.ts	start:  11.673000	duration:  2.048000	stream diff:  10.196475
 ./seg5.ts	start:  13.785000	duration:  2.112000	stream diff:  12.298679
 ./seg6.ts	start:  15.833000	duration:  2.048000	stream diff:  14.343878

   ...
   
 ./seg77.ts	start:  163.011667	duration:  2.176000	stream diff:  161.307591
 ./seg78.ts	start:  165.187667	duration:  2.176000	stream diff:  163.482903 <-- big stream diff

real	0m0.482s             <--  fast segmenting for VOD
user	0m0.334s
sys	0m0.128s

```
#### `Live stream non-live stuff`
   
* stream_diff with `--live` or `--delete`

   * stream_diff automatically throttles non-live streams for realtime playback . 
   * stream_diff keeps segmentation and the sliding window in sync.
 
 ```lua
 a@debian:~/x9k3$ time pypy3 x9k3.py  -i local-vid.ts --live
 ./seg0.ts	start:  1.433000	duration:  2.112000	stream diff:  1.749682
 ./seg1.ts	start:  3.545000	duration:  2.048000	stream diff:  1.664505
 ./seg2.ts	start:  5.593000	duration:  2.005333	stream diff:  1.604484
 ./seg3.ts	start:  7.598333	duration:  2.026667	stream diff:  1.608694
 ./seg4.ts	start:  9.625000	duration:  2.048000	stream diff:  1.614071
 ./seg5.ts	start:  11.673000	duration:  2.112000	stream diff:  1.660427
 ./seg6.ts	start:  13.785000	duration:  2.048000	stream diff:  1.570947
 ./seg7.ts
 
 ...
 ./seg65.ts	start:  136.025000	duration:  2.005333	stream diff:  0.197508
 ./seg66.ts	start:  138.030333	duration:  2.069334	stream diff:  0.227942
 ./seg67.ts	start:  140.099667	duration:  2.112000	stream diff:  0.240508
 ./seg68.ts	start:  142.211667	duration:  2.026666	stream diff:  0.132231
 ./seg69.ts	start:  144.238333	duration:  2.026667	stream diff:  0.111408
 ./seg70.ts	start:  146.265000	duration:  2.005333	stream diff:  0.064351
 ./seg71.ts	start:  148.270333	duration:  2.026667	stream diff:  0.063869
 ./seg72.ts	start:  150.297000	duration:  2.112000	stream diff:  0.129556
 ./seg73.ts	start:  152.409000	duration:  2.005333	stream diff:  0.004607
 ./seg74.ts	start:  154.414333	duration:  2.133334	stream diff:  0.112022
 ./seg75.ts	start:  156.547667	duration:  2.069333	stream diff:  0.018838
 ./seg76.ts	start:  158.617000	duration:  2.218667	stream diff:  0.151273
 ./seg77.ts	start:  160.835667	duration:  2.176000	stream diff:  0.101823
 ./seg78.ts	start:  163.011667	duration:  2.176000	stream diff:  0.100369  <-- small stream diff

real	2m44.775s   <-- real time segmenting to sync live stream sliding window
user	0m0.678s
sys	0m0.169s
```
 

## `FAQ`

#### `Q.`
How do I Customize CUE-OUT and CUE-IN ad break events?
#### `A.` 
Override the `X9K3.scte35.is_cue_out` and  `X9K3.scte35.is_cue_in` static methods.



 The __X9K3 class__ has __three static methods__ you can __override__ and __customize__.

|   @staticmethod                                                                                                     |  arg                                                        |return value|  details                                                              |
|---------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|------------|-----------------------------------------------------------------------|
| [mk_cue_tag](https://github.com/futzu/x9k3/blob/main/x9k3.py#L74) | [cue](https://github.com/futzu/scte35-threefive#cue-class)  | text       | called to generate scte35 hls tags                                    |
|  [is_cue_out](https://github.com/futzu/scte35-hls-x9k3/blob/main/x9k3.py#L81)| [cue](https://github.com/futzu/scte35-threefive#cue-class)  |  bool      |returns True if the cue is a CUE-OUT                                   |
| [ is_cue_in](https://github.com/futzu/x9k3/blob/main/x9k3.py#L93)|   [cue](https://github.com/futzu/scte35-threefive#cue-class)| bool       |                                    returns True if the cue is a CUE-IN|


#### `Example`
---
*  __Override__ the static method __X9K3.scte35.is_cue_out(cue)__ 
*  Require 
   * a Splice Command of type `6`, __Time Signal__ 
   * a Splice Descriptor tag of type `2`, __Segmentation Descriptor__   
   * a Segmentation Type Id of `0x22`, __"Break Start"__
    
```smalltalk
def my_cue_out(cue):
    """
    my_cue_out returns True 
    if the splice command is a time signal
    """
    if cue.command.command_type == 6: # time signal
        for d in cue.descriptors:      # cue.descriptors is always list
            if d.tag ==2:              # Segmentation Descriptor tag
                if d.segmentation_type_id == 0x22:  # Break Start
                    return True
    return False


```
* __Create__ an __X9K3__ instance

```smalltalk
from x9k3 import X9K3
x9 = X9K3("vid.ts")
```
* __set is_cue_out to your custom function__

```smalltalk
x9.scte35.is_cue_out = my_cue_out
x9.decode()
```








