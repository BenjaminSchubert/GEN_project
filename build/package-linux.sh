#!/bin/sh

set -e

rm -rf archives
mkdir -p archives

if which virtualenv && [ ! -d .env ]; then
	echo "Installing virtualenv to have a clean installation"
	virtualenv -p /usr/bin/python3 .env
	source .env/bin/activate
fi

# install dependencies
pip install cython pyinstaller
pip install -r ../frontend/requirements.pip
pip install -r ../authentication_server/requirements.pip
pip install -r ../game_server/requirements.pip

# frontend

pyinstaller frontend/phagocytes.windows.spec
cp ../frontend/config.cfg dist/
cp frontend/README dist/

mv dist phagocytes-client-linux
zip -r phagocytes-client-linux.zip phagocytes-client-linux/

rm -r build 
rm -r phagocytes-client-linux

mv phagocytes-client-linux.zip archives/


# auth server
pyinstaller auth-server/phagocytes-auth.spec
cp ../authentication_server/config.cfg dist/
cp auth-server/README dist/

mv dist phagocytes-auth-linux
zip -r phagocytes-auth-linux.zip phagocytes-auth-linux/

rm -r build
rm -r phagocytes-auth-linux

mv phagocytes-auth-linux.zip archives/


# game server
pyinstaller game-server/phagocytes-game.spec
cp ../game_server/config.cfg dist/
cp game-server/README dist/

mv dist phagocytes-game-linux
zip -r phagocytes-game-linux.zip phagocytes-game-linux/

rm -r build
rm -r phagocytes-game-linux

mv phagocytes-game-linux.zip archives/

if [ -d .env ]; then
    rm -r .env
fi
