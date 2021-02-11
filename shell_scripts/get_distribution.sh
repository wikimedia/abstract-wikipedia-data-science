now=$(date +"%s")

## ---- code to run in cronjob ----
cd abstract-wikipedia-data-science/
source venv/bin/activate
python3 get_distribution.py
## --------------------------------

then=$(date +"%s")
diff=$((($then - $now)/60))
echo "Took $diff minute(s) to run"
