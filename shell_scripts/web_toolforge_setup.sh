# copy python script
cp -avp ../web/* $HOME/www/python/src/

# copy js script
cp -avr ../web/client/* $HOME/www/js/

# run docker for js
webservice --backend=kubernetes node10 shell

# restart python server
webservice --backend=kubernetes python3.7 restart