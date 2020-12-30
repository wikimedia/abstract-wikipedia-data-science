# Create a python environment with the following commands
# activate it and install dependencies

# python3 -mvenv venv
# source venv/bin/activate
# pip install -r requirements.txt

# Make script executable
# chmod +x fetch_content.sh

now=$(date +"%s")

## ---- code to run in cronjob ----
cd abstract-wikipedia-data-science/shell_scripts
source venv/bin/activate
python3 ../fetch_content.py $1 $2
# arguments are the start and end indices of links to run
## --------------------------------

then=$(date +"%s")
diff=$((($then - $now)/60))
echo "Took $diff minute(s) to run"

# How to run this file:
# run: crontab -e
# add this to the end of the file: 0 0 * * * jsub fetch_content.sh 1 10
# 1, 10 are the indices that you need to change in each command.
# The crontab will have 50 of these files running...

# Or to run instantly: jsub fetch_content.sh 1 10

