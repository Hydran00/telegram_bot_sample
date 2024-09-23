import time
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue, AIORateLimiter
from .secret import TOKEN
# Telegram bot token

# URL to monitor
# URL = 'https://vicenza.istruzioneveneto.gov.it/avvisi-interpelli-docenti-vicenza/'
URL = 'http://0.0.0.0:9000/'
# Initial content of the webpage
initial_content = ''

# Check interval in seconds
CHECK_INTERVAL = 900  # 15 minutes

    
# List of subscribed users
subscribed_users = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the bot and send a welcome message."""
    start_message = 'Hello grina! I will notify you of any changes on the following website:\n'+URL
    start_message += '\n\nUse /subscribe to receive change alerts.'
    start_message += '\nUse /unsubscribe to stop receiving change alerts.'
    # start_message += '\nUse /giorgio to '
    
    await update.message.reply_text(start_message)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe a user to change alerts."""
    user_id = update.message.chat_id
    if user_id not in subscribed_users:
        subscribed_users.append(user_id)
        await update.message.reply_text('You have subscribed to change alerts.')
    else:
        await update.message.reply_text('You are already subscribed.')

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
    try:
        # Request the webpage content
        response = requests.get(URL)
        response.raise_for_status()

        # Parse the webpage content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract relevant content (e.g., all text within the body)
        current_content = soup.get_text()

        # Compare with the initial content
        if initial_content and current_content != initial_content:
            alert_message = 'The monitored webpage has new content! \n Check it out at: ' + URL
            await send_alert_to_users(alert_message, application)

        # Update the initial content
        initial_content = current_content

    except Exception as e:
        print(f"Error checking the website: {e}")

async def scheduled_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled task to repeatedly check the website."""
    await check_website(context.application)

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
    job_queue.run_repeating(scheduled_check, interval=CHECK_INTERVAL, first=0)

    # Start the bot
    print("Bot started")
    application.run_polling()
