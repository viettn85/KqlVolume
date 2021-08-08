if [ $1 == 'help' ]
then
    while read line; do echo $line; done < volume.help
elif [ $1 == 'helpall' ]
then
    while read line; do echo $line; done < volume_full.help
elif [ $1 == 'history' ] 
then
    python3 src/crawler/history.py
elif [ $1 == 'crawl' ] 
then
    python3 src/crawler/crawlMarket.py
elif [ $1 == 'update' ] 
then
    if [ $2 == 'daily' ]
    then
        python3 src/crawler/dailyCrawler.py
    elif [ $2 == 'realtime' ]
    then
        python3 src/crawler/realtime.py
    fi
elif [ $1 == 'filter' ] 
then
    python3 src/volume/filterStocks.py
elif [ $1 == 'check' ] 
then
    python3 src/volume/checkMarket.py $2 $3 $4 $5
elif [ $1 == 'report' ] 
then
    python3 src/volume/analysisVolume.py $2 $3 $4 $5
elif [ $1 == 'shoot' ] 
then
    python3 src/chart/ducky.py $2
elif [ $1 == 'market' ] 
then
    python3 src/scan/ducky.py $2
fi
