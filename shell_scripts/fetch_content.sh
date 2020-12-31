# Create a python environment: python3 -mvenv venv
# activate it: source venv/bin/activate
# run init.sh



now=$(date +"%s")

## ---- code to run in cronjob ----
cd abstract-wikipedia-data-science/
source venv/bin/activate
python3 fetch_content.py $1 $2
# arguments are the start and end indices of links to run
## --------------------------------

then=$(date +"%s")
diff=$((($then - $now)/60))
echo "Took $diff minute(s) to run"



# How to run this file:

# run: crontab -e
# add this to the end of the file: 0 0 * * * jsub fetch_content.sh 1 10
# 1, 10 are the indices that you need to change in each command.
# The crontab can have 50 of these files running from toolforge

# Or to run instantly: jsub fetch_content.sh 1 10

