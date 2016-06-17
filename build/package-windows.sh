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

pip install typing || true


# frontend
pyinstaller frontend/phagocytes.windows.spec
cp ../frontend/config.cfg dist/
cp frontend/README dist/

rm -r build

mv dist phagocytes-client-windows

mv phagocytes-client-windows archives/


# auth server
pyinstaller auth-server/phagocytes-auth.windows.spec
cp ../authentication_server/config.cfg dist/
cp auth-server/README dist/

rm -r build

mv dist phagocytes-auth-windows

mv phagocytes-auth-windows archives/


# game server
pyinstaller game-server/phagocytes-game.windows.spec
cp ../game_server/config.cfg dist/
cp game-server/README dist/

mv dist phagocytes-game-windows

rm -r build

mv phagocytes-game-windows archives/

if [ -d .env ]; then
    rm -r .env
fi
