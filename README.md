# x9k3
x9k3 is an hls segmenter for mpegts.

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
* segments named seg1.ts seg2.ts etc...

### Test
```
ffplay index.m3u8
```

