import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue, AIORateLimiter
from urls import URL
import json, os, sys
import random
from datetime import datetime,time  as ttime# this imports the datetime class, not the module
from zoneinfo import ZoneInfo


TOKEN = os.environ.get('TOKEN')
SUBSCRIBERS_FILE = 'subscribers.json'

# Define the time window in the target time zone
TARGET_TIMEZONE = ZoneInfo("Europe/Rome")  # GMT+2
START_TIME = ttime(7, 45)  # 07:45
END_TIME = ttime(19, 0)    # 19:00
MIN5_TIME_START = ttime(7, 45)   # 07:45
MIN5_TIME_END = ttime(13, 0)     # 13:00

COUNTER = -1

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'
]

# Check interval in seconds
CHECK_INTERVAL = 300 # 5 minutes

print(URL.items())

# Initialize an empty set for subscribers
subscribed_users = set()

# Initial content of the webpage
initial_content = ['' for _ in range(len(URL))]



# Function to load subscribers from file
def load_subscribers():
    global subscribed_users
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, 'r') as f:
                subscribed_users = set(json.load(f))  # Load the subscribed_users from file
                print(f"Loaded {len(subscribed_users)} subscribers.")
        except Exception as e:
            print(f"Error loading subscribers: {e}")
    else:
        print("No subscribers file found. Starting with an empty set.")

# Function to save subscribers to file
def save_subscribers():
    global subscribed_users
    try:
        with open(SUBSCRIBERS_FILE, 'w+') as f:
            json.dump(list(subscribed_users), f)  # Save subscribed_users as a list
            print(f"Saved {len(subscribed_users)} subscribers.")
    except Exception as e:
        print(f"Error saving subscribers: {e}")    
        
# Function to handle shutdown on Ctrl + C
def handle_exit():
    print("\nGraceful shutdown. Saving subscribers...")
    save_subscribers()  # Save subscribers on exit
    sys.exit(0)
            
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the bot and send a welcome message."""
    start_message = 'Hello grina! I will notify you of any changes on the following website:\n'+ '\n'.join(URL.values())
    start_message += '\n\nUse /subscribe to receive change alerts.'
    start_message += '\nUse /unsubscribe to stop receiving change alerts.'
    # start_message += '\nUse /giorgio to '
    
    await update.message.reply_text(start_message)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe a user to change alerts."""
    user_id = update.message.chat_id
    if user_id in subscribed_users:
        return await update.message.reply_text('You are already subscribed.')
    if len(subscribed_users) >=2:
        return await update.message.reply_text('This is a private bot.')
    if user_id not in subscribed_users:
        subscribed_users.add(user_id)
        print(f"User {user_id} has subscribed.")
        return await update.message.reply_text('You have subscribed to change alerts.')
        

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe a user from change alerts."""
    user_id = update.message.chat_id
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        await update.message.reply_text('You have unsubscribed from change alerts.')
    else:
        await update.message.reply_text('You are not subscribed.')

async def check_website(application: Application) -> None:
    """Check the website for changes and notify users if there are any."""
    global initial_content
    if len(subscribed_users) == 0:
        print("No users subscribed -> skipping check")
        return
    # Request the webpage content
    for i, (loc, url) in enumerate(URL.items()):
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS)
            }
            response = requests.get(url,headers=headers, timeout=10)
            # print in GMT+2
            print(f"Checked the website for " + loc + " at time " + datetime.now(TARGET_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S"))

            # Parse the webpage content with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract relevant content (e.g., all text within the body)
            current_content = soup.get_text()

            # Compare with the initial content
            if initial_content[i] and current_content != initial_content[i]:
                alert_message = 'The monitored webpage of ' + loc + ' has changed!\n\n'
                alert_message += 'Check the website at: ' + url
                print(alert_message)
                await send_alert_to_users(alert_message, application)
            else:
                print("No changes detected.")
            # Update the initial content
            initial_content[i] = current_content

        except Exception as e:
            print(f"Error checking the website: {e}")

async def scheduled_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled task to repeatedly check the website."""
    global TARGET_TIMEZONE, START_TIME, END_TIME, MIN5_TIME_START, MIN5_TIME_END, COUNTER

    # Get the current time in the target time zone
    now = datetime.now(TARGET_TIMEZONE)
    now_time = now.time()


    # Check if the current time is within the defined time window
    if START_TIME <= now_time <= END_TIME:
        if MIN5_TIME_START <= now_time <= MIN5_TIME_END:
            # check every time
            # print("5 min zone -> check every time")
            return await check_website(context.application)
        else:
            # check every 15 minutes
            COUNTER += 1
            if COUNTER % 4 == 0:
                # print("15 min zone -> check every 15 minutes")
                return await check_website(context.application)
            # else:
                # print("15 min zone -> Skipping")
    else:
        return  # Do nothing if outside of the time window

async def send_alert_to_users(message: str, application: Application) -> None:
    """Send an alert message to all subscribed users and via email."""
    for user_id in subscribed_users:
        try:
            await application.bot.send_message(
                chat_id=user_id,
                text=f"🚨 *ALERT* 🚨\n\n{message}",
                parse_mode='Markdown',
                disable_notification=False
            )
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")

            
if __name__ == '__main__':
    # Create the Application object with the bot token
    application = Application.builder() \
                             .token(TOKEN) \
                             .rate_limiter(AIORateLimiter()) \
                             .build()

    # Add handlers for commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Schedule the website check function
    job_queue = application.job_queue
    job_queue.run_repeating(scheduled_check, interval=CHECK_INTERVAL, first=4)

    # Load subscribers from file
    load_subscribers()
    for user_id in subscribed_users:
        print(f"Retrieved subscribtion of user {user_id} .")
    # Start the bot
    print("Bot started")
    application.run_polling()
    handle_exit()