# Create a python environment with the following commands
# activate it and install dependencies

# python3 -mvenv my_venv
# source my_venv/bin/activate
# pip install -r requirements.txt

# Make script executable
# chmod +x script.sh

## ---- code to run in cronjob ----
cd abstract-wikipedia-data-science/
source my_venv/bin/activate
python3 fetch_content.py $1 $2
# arguments are the start and end indices of links to run from wikipages.csv file
## --------------------------------

# How to run this file:
# run: crontab -e
# add this to the end of the file: 0 0 * * * jsub script.sh 1 10
# 1, 10 are the indices that you need to change in each command.
# The crontab will have 50 of these files running...

# Or to run instantly: jsub script.sh 1 10

