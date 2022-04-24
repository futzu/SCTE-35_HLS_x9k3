

# x9k3
##  __HLS Segmenter__ with __SCTE-35__ baked in.
scte-35 by  [__threefive__. ](https://github.com/futzu/scte35-threefive)


* __SCTE-35 Cues__ in __Mpegts Streams__ are Translated into __HLS tags__.
* Segments are __Split on SCTE-35 Cues__ as needed.
* __M3U8__ Manifests are created with __SCTE-35 HLS tags__.
* Supports __h264__ and __h265__(hevc)
* __Multi-protocol.__ Files, __Http(s)__, __Multicast__, and __Udp__.
* Supports [__Live__](https://github.com/futzu/scte35-hls-x9k3#live) __Streaming__.
* [__Customizable__](https://github.com/futzu/scte35-hls-x9k3/blob/main/README.md#faq)  Ad Break __Criteria__

# Clean Code.
* This code is cleaner than your dishes.
 
```smalltalk
a@fumatica:~/x9k3$ pylint x9k3.py 

************* Module x9k3
x9k3.py:20:0: R0902: Too many instance attributes (15/7) (too-many-instance-attributes)

------------------------------------------------------------------
Your code has been rated at 9.95/10 (previous run: 9.95/10, +0.00)

```


# Heads Up.
---
> This is not yet stable.`Expect changes. 
# Be Cool.
---
  * __Write Code__, if you do that or want to learn.
  * __Write Docs__, if code is not your thing.
  * __Break Stuff__ and tell me what happened.
  

 If you have a patch or idea or suggestion, Open an issue, I want to hear it. 
 I reply to everybody that takes the time to contact me.
 If I dont use your idea, I'll tell you why .
  
 
# Requires 
---
* python 3.6+ or pypy3
* [threefive](https://github.com/futzu/scte35-threefive)  
```smalltalk
pip3 install threefive
```

# How to Use
---

```smalltalk
$ pypy3  x9k3.py -h
usage: x9k3.py [-h] [-i INPUT] [-l]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input source, like "/home/a/vid.ts" or "udp://@235.35.3.5:3535" or "https://futzu.com/xaa.ts"
  -l, --live            Flag for a live event.(enables sliding window m3u8)
```
### [`the --live flag`](https://github.com/futzu/scte35-hls-x9k3#live)


```smalltalk
python3 x9k3.py -i video.mpegts
```


```smalltalk
python3 x9k3.py --live -i udp://@235.35.3.5:3535
```
 (Try [`mudpie`](https://github.com/futzu/mudpie) to stream multicast to x9k3)

```smalltalk
cat video.ts | python3 x9k3.py
```
## `VOD` 
---
### Output

* index.m3u8

```smalltalk
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:3
#EXT-X-MEDIA-SEQUENCE:0
 
#EXTINF:2.002,
seg0.ts
#EXTINF:2.002,
seg1.ts
#EXTINF:2.002,
seg2.ts

```

*  __SCTE-35 Cues are Added When Received__


```smalltalk
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:3

#EXTINF:2.152145,
seg0.ts
# Time Signal
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:2.085422,
seg1.ts
```


*  Video Segments are __cut at the the first iframe >=  the splice point pts__.
* __SCTE-35 Cues with a preroll__ are __Inserted Again__ at the __splice point__.

```smalltalk
# Splice Point @ 17129.086244
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:0.867544,
seg2.ts
#EXTINF:2.235556,
seg3.ts

```

* __CUE-OUT ans CUE-IN__ are added at __the splice point__.

```smalltalk
#EXT-X-SCTE35:CUE="/DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==" CUE-OUT=YES
#EXTINF:1.668334,
seg13.ts

```

* Segments are __cut on iframes__.
* __Segment size is 2 seconds or more, determined by GOP size__. 
* Segments are named __seg1.ts seg2.ts etc...__

```smalltalk
seg47.ts
#EXTINF:2.002,
seg48.ts
#EXTINF:2.002,
seg49.ts
#EXTINF:2.002,
seg50.ts

```

## `Live`
---
 * __M3u8 Manifests are regenerated every time a segment is written__.
 * __Sliding Window__ for 10 [MEDIA_SLOTS](https://github.com/futzu/scte35-hls-x9k3/blob/main/x9k3.py#L15)
 * A `#EXT-X-SCTE35:CUE="..."` with a `CUE-OUT=CONT`  __Added to First Segment in Manifest during an Ad Break__.  

### Output

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

## FAQ
---
#### Q.
     How do I __Customize CUE-OUT and CUE-IN__ ad break events?
#### A. 
__Override__ the `X9K3.is_cue_out` and  `X9K3.is_cue_in` static methods_



 __The X9K3 class has three static methods you can Override and Customize __.

|   @staticmethod                                                                                                     |  arg                                                        |return value|  details                                                              |
|---------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|------------|-----------------------------------------------------------------------|
| [mk_cue_tag](https://github.com/futzu/scte35-hls-x9k3/blob/6218928792b12221aa8d1208dbcced391980dc1d/x9k3.py#L47-52) | [cue](https://github.com/futzu/scte35-threefive#cue-class)  | text       | called to generate scte35 hls tags                                    |
|  [is_cue_out](https://github.com/futzu/scte35-hls-x9k3/blob/6218928792b12221aa8d1208dbcced391980dc1d/x9k3.py#L54-64)| [cue](https://github.com/futzu/scte35-threefive#cue-class)  |  bool      |returns True if the cue is a CUE-OUT                                   |
| [ is_cue_out](https://github.com/futzu/scte35-hls-x9k3/blob/6218928792b12221aa8d1208dbcced391980dc1d/x9k3.py#L66-76)|   [cue](https://github.com/futzu/scte35-threefive#cue-class)| bool       |                                    returns True id the cue is a CUE-IN|


#### Example
---

*  __Override__ the static method __X9K3.is_cue_out(cue)__ 
      *     define a function that matches the interface.
 

    
```smalltalk
def my_cue_out(cue):
    """
    my_cue_out returns True 
    if the splice command is a time signal
    """
      if cue.command.command_type == 6: # time signal
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

![image](https://user-images.githubusercontent.com/52701496/164541045-5f1ac01d-23e0-4dc7-89cf-b2507dcdfa41.png)




## Test
```
ffplay index.m3u8
```

# 2020 SCTE-35 Specification Regarding The HLS `#EXT-X-SCTE35` Tag

![image](https://user-images.githubusercontent.com/52701496/160178288-fc75bcfc-b408-43f0-a7ec-83ecdfb10e8b.png)
![image](https://user-images.githubusercontent.com/52701496/160177961-aa7f1706-2f49-4144-a3e3-36efb458037d.png)
![image](https://user-images.githubusercontent.com/52701496/160178082-a978772d-d650-4093-a442-2aeb907bba19.png)







