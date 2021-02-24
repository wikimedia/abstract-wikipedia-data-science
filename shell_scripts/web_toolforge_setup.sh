# copy python script
cp -avp ../web/* $HOME/www/python/src/

# copy js script
cp -avr ../web/client/* $HOME/www/js/

# run docker for js
webservice --backend=kubernetes node10 shell

# move to js folder
cd $HOME/www/js

# install dependencies
npm install

# build js
npm run build

# exit docker
exit

# copy dist folder
cp -avp dist/ $HOME/www/python/src/client/

# restart python server
webservice --backend=kubernetes python3.7 restart