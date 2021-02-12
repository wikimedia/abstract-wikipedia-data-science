now=$(date +"%s")

## ---- code to run in cronjob ----
cd abstract-wikipedia-data-science/
source venv/bin/activate
if [[ $# -eq 0 ]]
then
    python3 detect_similarity.py
else
    python3 detect_similarity.py -d
fi
## --------------------------------

then=$(date +"%s")
diff=$((($then - $now)/60))
echo "Took $diff minute(s) to run"