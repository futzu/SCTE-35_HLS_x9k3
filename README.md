# x9k3
* __x9k3__ is an __HLS Segmenter with SCTE-35 Support__. 
* __SCTE-35 Cues__ in __MpegTS Streams__ are Translated into `#EXT-X-SCTE35` tags.
* Segments are __Split on SCTE-35 Cues__ as needed.
* Supports __h264__ and __h265__(hevc)
* Supports __Files, Http(s), Multicast, and UDP MpegTS__ inputs.  
 
### Requires 
* python 3.6+ or pypy3
* [threefive](https://github.com/futzu/scte35-threefive)  
```
pip3 install threefive
```

### How to Use
```sh
python3 x9k3.py video.mpegts
```
```sh 
python3 x9k3.py https://example.com/video.ts
```
```sh
cat video.ts | python3 x9k3.py
```

### Output
* index.m3u8
```
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
#EXTINF:3.336667,
seg3.ts
#EXTINF:2.969633,
seg4.ts
#EXT-X-SCTE35:CUE="/DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ==" CUE-OUT="YES" DURATION=90.023267 
#EXTINF:2.3023,
seg5.ts
#EXTINF:2.168833,
seg6.ts
#EXTINF:2.7027,
seg7.ts
#EXTINF:1.668334,
seg8.ts


```

* segments are named seg1.ts seg2.ts etc...

### Test
```
ffplay index.m3u8
```

### 2020 SCTE-35 Specification Regarding The HLS `#EXT-X-SCTE35` Tag

![image](https://user-images.githubusercontent.com/52701496/160178288-fc75bcfc-b408-43f0-a7ec-83ecdfb10e8b.png)
![image](https://user-images.githubusercontent.com/52701496/160177961-aa7f1706-2f49-4144-a3e3-36efb458037d.png)
![image](https://user-images.githubusercontent.com/52701496/160178082-a978772d-d650-4093-a442-2aeb907bba19.png)








