cd abstract-wikipedia-data-science/
source venv/bin/activate

if [[ $# -eq 0 ]]
then
    python3 detect_data_modules.py
else
    python3 detect_data_modules.py -f
fi
