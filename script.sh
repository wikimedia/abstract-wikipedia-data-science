# Create a python environment with the following commands
# python3 -mvenv venv
# pip install -r requirements.txt

source venv/bin/activate

# arguments are the start and end indices of links to run from wiki_list.txt file
python3 fetch_content.py $1 $2

# How to run this file:
# run: crontab -e
# add this to the end of the file: 0 0 * * * jsub script.sh 1 10
# 1, 10 are the indices that you need to change in each command.
# The crontab will have 50 of these files running...

# Or to run instantly: jsub script.sh 1 10

