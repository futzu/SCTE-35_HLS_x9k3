# x9k3
x9k3 is an hls segmenter with SCTE-35 Support. SCTE-35 Cues in Mpegts streams are translated into #EXT-X-SCTE35 tags as specified in the 2020 SCTE-35 Specification.

### Requires 
* python 3.6+
* threefive  
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
#EXT-X-SCTE35:CUE="/DAxAAAAAAAAAP/wFAUAAABdf+/+zHRtOn4Ae6DOAAAAAAAMAQpDVUVJsZ8xMjEqLYemJQ=="
#EXTINF:2.3023,
seg5.ts
#EXTINF:2.168833,
seg6.ts
#EXTINF:2.7027,
seg7.ts
#EXTINF:3.3033,
seg8.ts
#EXTINF:2.2022,
seg9.ts


```

* segments are named seg1.ts seg2.ts etc...

### Test
```
ffplay index.m3u8
```

