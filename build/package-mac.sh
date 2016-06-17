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

pyinstaller frontend/phagocytes.spec
cp ../frontend/config.cfg dist/
cp frontend/README dist/

mv dist phagocytes-client-mac
zip -r phagocytes-client-mac.zip phagocytes-client-mac/

rm -r build 
rm -r phagocytes-client-mac

mv phagocytes-client-mac.zip archives/


# auth server
pyinstaller auth-server/phagocytes-auth.spec
cp ../authentication_server/config.cfg dist/
cp auth-server/README dist/

mv dist phagocytes-auth-mac
zip -r phagocytes-auth-mac.zip phagocytes-auth-mac/

rm -r build
rm -r phagocytes-auth-mac

mv phagocytes-auth-mac.zip archives/


# game server
pyinstaller game-server/phagocytes-game.spec
cp ../game_server/config.cfg dist/
cp game-server/README dist/

mv dist phagocytes-game-mac
zip -r phagocytes-game-mac.zip phagocytes-game-mac/

rm -r build
rm -r phagocytes-game-mac

mv phagocytes-game-mac.zip archives/

if [ -d .env ]; then
    rm -r .env
fi
