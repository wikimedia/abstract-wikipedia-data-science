# move to js folder
cd $HOME/www/js

# install dependencies
npm install

# build js
npm run build

# copy dist folder
cp -avp dist/ $HOME/www/python/src/client/
