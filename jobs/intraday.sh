#!/bin/bash
# cd /Users/viet_tran/Workplace/kql/KqlVolume
cd /apps/KqlVolume
echo "Run Intraday Job"
nohup python3 src/crawler/intraday_hsc.py > logs/intraday.log &
