#!/bin/sh

pyinstaller phagocytes.spec
cp ../config.cfg dist/
cp README dist/

mv dist phagocytes-linux
zip -r phagocytes-linux.zip phagocytes-linux/

rm -r build
rm -r phagocytes-linux
