now=$(date +"%s")

## ---- code to run in cronjob ----
cd abstract-wikipedia-data-science/
source venv/bin/activate
python3 fetch_db_info.py
# arguments are the start and end indices of links to run
## --------------------------------

then=$(date +"%s")
diff=$((($then - $now)/60))
echo "Took $diff minute(s) to run"