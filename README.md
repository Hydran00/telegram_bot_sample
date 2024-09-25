# telegram_bot_sample
A simple bot that checks for update to a particular website hosted on [fly.io](https://fly.io/)

- Automaticaly dumps subscribers on SIGINT received in a json file
- Send an alert message when an update is detected
- Read urls from a dictionary stored in `urls.py`
- Uses env variables for the telegram secret