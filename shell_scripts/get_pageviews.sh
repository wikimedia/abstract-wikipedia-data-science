now=$(date +"%s")

## ---- code to run in cronjob ----
cd abstract-wikipedia-data-science/
source venv/bin/activate

if [[ $# -eq 0 ]]
then
    python3 get_pageviews.py
else
    python3 get_pageviews.py -d $1
fi
## --------------------------------

then=$(date +"%s")
diff=$((($then - $now)/60))
echo "Took $diff minute(s) to run"
