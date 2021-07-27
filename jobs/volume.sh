#!/bin/bash
cd /root/apps/KqlVolume/
nohup python3 src/watch/getForumUpdate.py > logs/updatef.log &
nohup python3 src/volume/analysisVolume.py auto > logs/kqls.log &
