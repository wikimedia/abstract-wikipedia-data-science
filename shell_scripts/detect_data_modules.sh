cd abstract-wikipedia-data-science/
source venv/bin/activate

if [ $1 = "f" ]
then
    python3 detect_data_modules.py -f
else
    python3 detect_data_modules.py
fi
