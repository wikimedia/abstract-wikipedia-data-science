now=$(date +"%s")

## ---- code to run in cronjob ----
cd abstract-wikipedia-data-science/
source venv/bin/activate

if [[ $# -eq 0 ]]
then
    python3 get_pageviews.py
elif [[ $# -eq 2 ]]
then
    echo $1 $2
    python3 get_pageviews.py -d -rest
elif [[ $1 = "d" ]]
then
    python3 get_pageviews.py -d
elif [[ $1 = "rest" ]]
then
    python3 get_pageviews.py -rest
fi
## --------------------------------

then=$(date +"%s")
diff=$((($then - $now)/60))
echo "Took $diff minute(s) to run"
