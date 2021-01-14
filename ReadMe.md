# card game

## description

A card game.

frontend: [enchant.js](https://github.com/wise9/enchant.js), [Socket.IO](https://socket.io/)

backend: python, [Flask](https://flask.palletsprojects.com/en/1.1.x/), [Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO)

## How to setup

1. `python -m venv .env`
1. Activate the virtual env (see https://docs.python.org/3/library/venv.html)
1. `pip install -r requirements.txt`
1. `python app.py`
1. Access to http://localhost:8080
1. Input player name (anything OK) and hit login button
1. The game starts after 2 players connected
