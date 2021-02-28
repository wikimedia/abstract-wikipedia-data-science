cd abstract-wikipedia-data-science/
source venv/bin/activate

now=$(date +"%s")

## The first arg should be the name of the function
## rest of the arg should be python file specific args
python3 $@ 

then=$(date +"%s")
diff=$((($then - $now)/60))
echo "Took $diff minute(s) to run"