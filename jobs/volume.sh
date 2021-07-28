#!/bin/bash
cd /apps/KqlVolume/
nohup python3 src/volume/analysisVolume.py auto > logs/kqls.log &
