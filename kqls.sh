if [ $1 == 'help' ]
then
    while read line; do echo $line; done < kqls.help
elif [ $1 == 'vol' ] 
then
    python3 src/volume/analysisVolume.py $2 $3 $4 $5
elif [ $1 == 'check' ] 
then
    python3 src/volume/checkMarket.py $2 $3 $4 $5
fi
