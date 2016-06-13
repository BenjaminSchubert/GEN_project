#!/bin/sh

mkdir -p archives

pyinstaller frontend/phagocytes.spec
cp ../frontend/config.cfg dist/
cp frontend/README dist/

mv dist phagocytes-client-linux
zip -r phagocytes-client-linux.zip phagocytes-client-linux/

rm -r build 
rm -r phagocytes-client-linux

mv phagocytes-client-linux.zip archives/
