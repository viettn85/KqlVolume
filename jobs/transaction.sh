#!/bin/bash
# cd /apps/KqlVolume/
cd /apps/KqlVolume/
nohup python3 src/crawler/intraday_hsc.py > logs/intraday.log &
