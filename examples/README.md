# x9k3parser.py
An example parser. 


Check out [m3ufu](https://guthub.com/futzu/m3ufu), a more complete and robust m3u8 parser.

# Use
* Segment with x9k3.py
```smalltalk
a@fumatica:~/$ pypy3 x9k3.py -i gh25994aac.ts 

....


a@fumatica:~/$ cat index.m3u8
#EXTM3U
#EXT-X-VERSION:3
EXT-X-TARGETDURATION:3
#EXT-X-MEDIA-SEQUENCE:0
# STARTED @ 17125.149156
#EXTINF:2.002,
seg0.ts
# Time Signal
# Splice Point @ 17129.086244
#EXT-X-SCTE35:CUE="/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==" 
#EXTINF:2.085422,
seg1.ts
#EXTINF:2.1021,
seg2.ts
#EXTINF:2.135478,
seg3.ts
#EXTINF:2.002,
seg4.ts
#EXTINF:2.002,
seg5.ts
#EXTINF:2.002,
...
```

* parse with x9k3parser.py
```smalltalk
a@fumatica:~/$ pypy3 x9k3parser.py index.m3u8 
{
    "media": "seg0.ts",
    "pts": 17124.199011,
    "start": 17124.199011,
    "end": 17126.351156,
    "duration": 2.152145,
    "tags": {
        "#EXTINF": "2.152145"
    }
}
{
    "media": "seg1.ts",
    "start": 17126.351156,
    "end": 17128.436578,
    "duration": 2.085422,
    "cue": "/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ==",
    "cue_data": {
        "info_section": {
            "table_id": "0xfc",
            "section_syntax_indicator": false,
            "private": false,
            "sap_type": "0x3",
            "sap_details": "No Sap Type",
            "section_length": 190,
            "protocol_version": 0,
            "encrypted_packet": false,
            "encryption_algorithm": 0,
            "pts_adjustment_ticks": 0,
            "pts_adjustment": 0.0,
            "cw_index": "0x0",
            "tier": "0xfff",
            "splice_command_length": 5,
            "splice_command_type": 6,
            "descriptor_loop_length": 168,
            "crc": "0x8608ed25"
        },
        "command": {
            "command_length": 5,
            "command_type": 6,
            "name": "Time Signal",
            "time_specified_flag": true,
            "pts_time": 17129.086244,
            "pts_time_ticks": 1541617762
        },
        "descriptors": [
            {
                "tag": 2,
                "descriptor_length": 32,
                "name": "Segmentation Descriptor",
                "identifier": "CUEI",
                "components": [],
                "segmentation_event_id": "0x96dd80f",
                "segmentation_event_cancel_indicator": false,
                "program_segmentation_flag": true,
                "segmentation_duration_flag": false,
                "delivery_not_restricted_flag": false,
                "web_delivery_allowed_flag": true,
                "no_regional_blackout_flag": true,
                "archive_allowed_flag": true,
                "device_restrictions": "No Restrictions",
                "segmentation_message": "Provider Placement Opportunity End",
                "segmentation_upid_type": 1,
                "segmentation_upid_type_name": "Deprecated",
                "segmentation_upid_length": 17,
                
                
                ...
          }
        ]
    },
    "tags": {
        "#EXT-X-SCTE35": {
            "CUE": "/DC+AAAAAAAAAP/wBQb+W+M4YgCoAiBDVUVJCW3YD3+fARFEcmF3aW5nRlJJMTE1V0FCQzUBAQIZQ1VFSQlONI9/nwEKVEtSUjE2MDY3QREBAQIxQ1VFSQlw1HB/nwEiUENSMV8xMjEwMjExNDU2V0FCQ0dFTkVSQUxIT1NQSVRBTBABAQI2Q1VFSQlw1HF/3wAAFJlwASJQQ1IxXzEyMTAyMTE0NTZXQUJDR0VORVJBTEhPU1BJVEFMIAEBhgjtJQ=="
        },
        "#EXTINF": "2.085422"
    }
}
          


```


