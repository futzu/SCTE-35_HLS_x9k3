


# x9k3
##  __HLS Segmenter__ with __SCTE-35__ baked in.
scte-35 by  [__threefive__. ](https://github.com/futzu/scte35-threefive)


* SCTE-35 Cues in __Mpegts Streams__ are Translated into HLS tags.
* Segments are __Split on SCTE-35 Cues__ as needed.
* M3U8 Manifests are created with __SCTE-35 HLS tags__.
* Supports __h264__ and __h265__(hevc)
* __Multi-protocol.__ Files, Http(s), Multicast, and Udp.
* Built using the highest rated SCTE-35 lib on the Planet, [__threefive__](https://github.com/futzu/scte35-threefive)

# Clean Code.
* This code is cleaner than your dishes.
 
```smalltalk
a@fumatica:~/x9k3$ pylint x9k3.py 

************* Module x9k3
x9k3.py:12:0: R0902: Too many instance attributes (14/7) (too-many-instance-attributes)
x9k3.py:34:20: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)

-----------------------------------
Your code has been rated at 9.87/10

```


# Heads Up.
> This is not yet stable, vis-à-vis bugs.`Expect changes. 
# Be Cool.

  * __Write Code__, if you do that or want to learn.
  * __Write Docs__, if code is not your thing.
  * __Break Stuff__ and tell me what happened.
  

 If you have a patch or idea or suggestion, Open an issue, I want to hear it. 
 I reply to everybody that takes the time to contact me.
 If I dont use your idea, I'll tell you why .
  
 
# Requires 
* python 3.6+ or pypy3
* [threefive](https://github.com/futzu/scte35-threefive)  
```smalltalk
pip3 install threefive
```

# How to Use
```smalltalk
python3 x9k3.py video.mpegts
```
```smalltalk
python3 x9k3.py https://example.com/video.ts
```
```smalltalk
cat video.ts | python3 x9k3.py
```

# Output

* index.m3u8

```smalltalk
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:3
#EXT-X-MEDIA-SEQUENCE:0
 
#EXTINF:2.168833,
seg0.ts
#EXTINF:2.335667,
seg1.ts
#EXTINF:2.168833,
seg2.ts

```

*  SCTE-35 Cues are added when received


```smalltalk
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:3
#EXT-X-MEDIA-SEQUENCE:0

#EXTINF:2.152145,
seg0.ts
# Time Signal
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:2.085422,
seg1.ts
```


*  Video Segments are cut at the the first iframe >=  the splice point pts.
* SCTE-35 Cues with a preroll are inserted again at the splice point.

```smalltalk
# Splice Point @ 17129.086244
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:0.867544,
seg2.ts
#EXTINF:2.235556,
seg3.ts

```

* CUE-OUT ans CUE-IN are added for splice insert commands at the splice point.

```smalltalk
#EXT-X-SCTE35:CUE="/DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==" CUE-OUT=YES
#EXTINF:1.668334,
seg13.ts

```

* Segments are cut on iframes.
* Segment size is 2 seconds or more, determined by GOP size. 
* Segments are named seg1.ts seg2.ts etc...

```smalltalk
seg47.ts
#EXTINF:2.12,
seg48.ts
#EXTINF:2.12,
seg49.ts
#EXTINF:2.12,
seg50.ts

```

# Test
```
ffplay index.m3u8
```

# 2020 SCTE-35 Specification Regarding The HLS `#EXT-X-SCTE35` Tag

![image](https://user-images.githubusercontent.com/52701496/160178288-fc75bcfc-b408-43f0-a7ec-83ecdfb10e8b.png)
![image](https://user-images.githubusercontent.com/52701496/160177961-aa7f1706-2f49-4144-a3e3-36efb458037d.png)
![image](https://user-images.githubusercontent.com/52701496/160178082-a978772d-d650-4093-a442-2aeb907bba19.png)







