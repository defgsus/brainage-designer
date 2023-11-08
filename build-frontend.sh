#!/bin/bash

cd frontend || exit
rm -r dist/
yarn build || exit
# ls -l dist/ || exit

rm ../bad/static/index*.css
rm ../bad/static/index*.js
rm ../bad/static/brain*.png
cp dist/index.html ../bad/static/
cp dist/index*.js ../bad/static/
cp dist/index*.css ../bad/static/
cp dist/brain*.png ../bad/static/
cd ..
