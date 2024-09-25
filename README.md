# telegram_bot_sample
A simple bot that checks for updates to a particular website hosted on [fly.io](https://fly.io/)

- Automaticaly dumps subscribers in a json file when the app receives SIGINT
- Send an alert message when an update is detected
- Read urls from a dictionary stored in `urls.py`
- Uses env variables for the telegram secret

### References
[Tutorial](https://bakanim.xyz/posts/deploy-telegram-bot-to-fly-io/)