[Details](#details) |
[Install](#requires) |
[Use](#how-to-use) |
[Customize](#faq) |
[Live Events](#live) |
[Bugs](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues) |
[Feedback](https://github.com/futzu/scte35-hls-segmenter-x9k3/issues) |
[Cue](https://github.com/futzu/scte35-threefive/blob/master/cue.md)

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


##  `This is not yet stable. Expect changes.` 


## Be Cool.

* I'm cool, you be cool too.

* If you have a question, ask it. 

* If you have something to say, say it. 

* If you have a patch or idea or suggestion, 
Open an issue, and tell me about it.  
  
 
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
a@debian:~/x9k3$ pypy3 x9k3.py -h
usage: x9k3.py [-h] [-i INPUT] [-o OUTPUT_DIR] [-l] [-d]

optional arguments:
  -h, --help            show this help message and exit

  -i INPUT, --input INPUT
                        Input source, like "/home/a/vid.ts" or
                        "udp://@235.35.3.5:3535" or "https://futzu.com/xaa.ts"

  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        directory for segments and index.m3u8
  
  -l, --live            Flag for a live event.(enables sliding window m3u8)
  
  -d, --delete          delete segments when in live mode ( requires --live )

```
* Example Usage
    * local file as input
    ```smalltalk
    python3 x9k3.py -i video.mpegts
    ```
    * multicast stream as input using sliding window   
   ```smalltalk
   python3 x9k3.py --live -i udp://@235.35.3.5:3535
   ```

    * multicast stream as input using sliding window and deleting old segments.
    ```smalltalk
    python3 x9k3.py --live --delete -i udp://@235.35.3.5:3535
    ```
   * https stream for input and writing segments to an output directory.
   ```smalltalk
   pypy3 x9k3.py -i https://so.slo.me/longb.ts --output_dir /home/a/variant0
   ```
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
     * Sliding Window for 10 [MEDIA_SLOTS](https://github.com/futzu/scte35-hls-x9k3/blob/main/x9k3.py#L45)
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

### FAQ
---
#### Q.
How do I Customize CUE-OUT and CUE-IN ad break events?
#### A. 
Override the `X9K3.is_cue_out` and  `X9K3.is_cue_in` static methods.



 The __X9K3 class__ has __three static methods__ you can __override__ and __customize__.

|   @staticmethod                                                                                                     |  arg                                                        |return value|  details                                                              |
|---------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|------------|-----------------------------------------------------------------------|
| [mk_cue_tag](https://github.com/futzu/x9k3/blob/main/x9k3.py#L79-L84) | [cue](https://github.com/futzu/scte35-threefive#cue-class)  | text       | called to generate scte35 hls tags                                    |
|  [is_cue_out](https://github.com/futzu/scte35-hls-x9k3/blob/main/x9k3.py#L86-L96)| [cue](https://github.com/futzu/scte35-threefive#cue-class)  |  bool      |returns True if the cue is a CUE-OUT                                   |
| [ is_cue_in](https://github.com/futzu/scte35-hls-x9k3/blob/main/x9k3.py#L98-108)|   [cue](https://github.com/futzu/scte35-threefive#cue-class)| bool       |                                    returns True if the cue is a CUE-IN|


##### Example
---
*  __Override__ the static method __X9K3.is_cue_out(cue)__ 
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
x9.is_cue_out = my_cue_out
x9.decode()
```
---


![image](https://user-images.githubusercontent.com/52701496/167934615-a74b952b-56cc-4777-b0dc-a4dc764b4b5a.png)






