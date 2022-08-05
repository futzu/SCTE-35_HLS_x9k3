[Details](#details) |
[Install](#requires) |
[Use](#how-to-use) |
[Customize](#faq) |
[Live Events](#live) |
[Bugs](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues) |
[Feedback](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues) |
[Cue](https://github.com/futzu/scte35-threefive/blob/master/cue.md) |
[Stream Diff](#stream-diff)

# x9k3
##  __HLS Segmenter__ with __SCTE-35__ baked in.
scte-35 by  [__threefive__. ](https://github.com/futzu/scte35-threefive)


* __SCTE-35 Cues__ in __Mpegts Streams__ are Translated into __HLS tags__.
* Segments are __Split on SCTE-35 Cues__ as needed.
* __M3U8__ Manifests are created with __SCTE-35 HLS tags__.
* Supports __h264__ and __h265__ and __mpeg2__ video.
* __Multi-protocol.__ Files, __Http(s)__, __Multicast__, and __Udp__.
* Supports [__Live__](https://github.com/futzu/scte35-hls-x9k3#live) __Streaming__.
* [__Customizable__](https://github.com/futzu/scte35-hls-x9k3/blob/main/README.md#faq)  Ad Break __Criteria__

### Heads Up, New Features Coming This Week.

* SCTE-35 Cue Playlist Injection via Sidecar File.
* Re-segmentation of Existing Playlists.
> x9k3 will be able to read SCTE-35 Cues from a sidecar text file and inject them into the m3u8 playlist.
> x9k3 will be able to take an m3u8 playlist as input and read the SCTE-35 Cues from the existing segments or a sidecar file,
> and adjusst segments to match SCTE-35 Cue Outs. I have it all working, I just want to smooth out the wrinkles. This is super cool. 

---




*  This is not yet stable. Expect changes. 

## Requires 
---
* python 3.6+ or pypy3
* [threefive](https://github.com/futzu/scte35-threefive)  
```smalltalk
pip3 install threefive
```

## How to Use
---

```smalltalk
$ pypy3 x9k3.py -h

usage: x9k3.py [-h] [-i INPUT] [-o OUTPUT_DIR] [-l] [-d]

optional arguments:

  -h, --help            show this help message and exit

  -i INPUT, --input INPUT
                        Input source, like "/home/a/vid.ts" or
                        "udp://@235.35.3.5:3535" or "https://futzu.com/xaa.ts"
                        
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        Directory for segments and index.m3u8 Directory is
                        created if it does not exist
                        
  -l, --live            Flag for a live event.(enables sliding window m3u8)
  
  -d, --delete          delete segments (implies live mode)

```
### __Example Usage__

 * local file as input
 ```smalltalk
    python3 x9k3.py -i video.mpegts
 ```
  ---
   * multicast stream as input
      * with a live sliding window   
   ```smalltalk
   python3 x9k3.py --live -i udp://@235.35.3.5:3535
   ```
 ---
 
   * Use ffmpeg to read multicast stream as input
   * Use x9k3 to segment 
      * with a sliding window, 
      * and  expiring old segments.
      * --delete implies --live
      
   ```smalltalk
    ffmpeg  -re -copyts -i udp://@235.35.3.5:3535 -map 0 -c copy -f mpegts - | python3 x9k3.py --delete
   ```
 ---
  * https stream for input
  * and writing segments to an output directory.
     * directory is created if it does not exist.
  ```smalltalk
   pypy3 x9k3.py -i https://so.slo.me/longb.ts --output_dir /home/a/variant0
  ```
  ---
   * using stdin as input 
   ```smalltalk
   cat video.ts | python3 x9k3.py
   ```
---

## Details 
---

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
---


* SCTE-35 cues with a preroll are inserted again at the splice point.

```smalltalk
# Splice Point @ 17129.086244
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:0.867544,
seg2.ts

```
---

* CUE-OUT ans CUE-IN are added at the splice point.

```smalltalk
#EXT-X-SCTE35:CUE="/DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==" CUE-OUT=YES
#EXTINF:1.668334,
seg13.ts

```
---
### `VOD`

* x9k3 defaults to VOD style playlist generation.
* All segment are listed in the m3u8 file. 
---
### `Live`
---
 * Activated by the --live switch or by setting X9K3.live=True

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

### Stream Diff
---
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
* __Live stream non-live stuff__
   
* stream_diff with `--live` or `--delete`

   * stream_diff automatically throttles non-live streams for realtime playback . 
   * stream_diff keeps segmentation and the sliding window in sync.
 
 ```lua
 a@debian:~/x9k3$ time pypy3 x9k3.py  -i local-vid.ts --live
 ./seg0.ts	start:  3.545000	duration:  2.112000	stream diff:  2.093996
 ./seg1.ts	start:  5.593000	duration:  2.048000	stream diff:  2.012526
 ./seg2.ts	start:  7.598333	duration:  2.005333	stream diff:  1.95753
 ./seg3.ts	start:  9.625000	duration:  2.026667	stream diff:  1.96211
 ./seg4.ts	start:  11.673000	duration:  2.048000	stream diff:  1.973159
 ./seg5.ts	start:  13.785000	duration:  2.112000	stream diff:  2.018733
 ./seg6.ts	start:  15.833000	duration:  2.048000	stream diff:  1.945783
 
 ...
 ./seg77.ts	start:  163.011667	duration:  2.176000	stream diff:  1.378177
 ./seg78.ts	start:  165.187667	duration:  2.176000	stream diff:  1.373616  <-- small stream diff

real	2m44.775s   <-- real time segmenting to sync live stream sliding window
user	0m0.678s
sys	0m0.169s
```
 
 
![image](https://user-images.githubusercontent.com/52701496/180592124-7ef7004b-41ac-4499-b63a-d88856c9e988.png)


### FAQ
---
#### Q.
How do I Customize CUE-OUT and CUE-IN ad break events?
#### A. 
Override the `X9K3.scte35.is_cue_out` and  `X9K3.scte35.is_cue_in` static methods.



 The __X9K3 class__ has __three static methods__ you can __override__ and __customize__.

|   @staticmethod                                                                                                     |  arg                                                        |return value|  details                                                              |
|---------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|------------|-----------------------------------------------------------------------|
| [mk_cue_tag](https://github.com/futzu/x9k3/blob/main/x9k3.py#L74) | [cue](https://github.com/futzu/scte35-threefive#cue-class)  | text       | called to generate scte35 hls tags                                    |
|  [is_cue_out](https://github.com/futzu/scte35-hls-x9k3/blob/main/x9k3.py#L81)| [cue](https://github.com/futzu/scte35-threefive#cue-class)  |  bool      |returns True if the cue is a CUE-OUT                                   |
| [ is_cue_in](https://github.com/futzu/x9k3/blob/main/x9k3.py#L93)|   [cue](https://github.com/futzu/scte35-threefive#cue-class)| bool       |                                    returns True if the cue is a CUE-IN|


##### Example
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
---


![image](https://user-images.githubusercontent.com/52701496/180024811-02a3e3b1-6986-4c11-9e04-20c1051b08c1.png)





