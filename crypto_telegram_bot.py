import logging
import os
from datetime import datetime, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
from telegram.error import TelegramError
from dotenv import load_dotenv
from database import Database

# Try to load from .env file
load_dotenv()
env_loaded = True

# Import the trading strategy
from two_green_filter_binance import CryptoTradingStrategy

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get token from environment variable or set it to None
TELEGRAM_BOT_TOKEN = os.getenv('API_KEY')

class CryptoSignalBot:
    def __init__(self, token):
        """Initialize the bot with token and trading strategy"""
        self.token = token
        self.application = ApplicationBuilder().token(token).build()
        self.crypto_strategy = None
        self.db = Database()  # Initialize database
        self.setup_handlers()
        self.setup_jobs()

    def setup_jobs(self):
        """Set up scheduled jobs"""
        job_queue = self.application.job_queue
        
        # Get all active subscribers and their preferred notification times
        subscribers = self.db.get_active_subscribers()
        
        # Schedule jobs for each subscriber's preferred time
        for subscriber in subscribers:
            chat_id, _, _, _, scan_days, notification_time = subscriber
            if notification_time:
                try:
                    hour, minute = map(int, notification_time.split(':'))
                    job_queue.run_daily(
                        self.scheduled_scan,
                        time=time(hour, minute),
                        days=(0, 1, 2, 3, 4, 5, 6),
                        data={'chat_id': chat_id, 'scan_days': scan_days or 30}
                    )
                except Exception as e:
                    logger.error(f"Error scheduling job for {chat_id}: {e}")
        
        logger.info(f"Scheduled jobs set up for {len(subscribers)} subscribers")

    def setup_handlers(self):
        """Set up command handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("settings", self.settings))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        # self.application.add_handler(CommandHandler("settime", self.set_notification_time))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        user = update.effective_user
        self.db.add_subscriber(
            chat_id=update.effective_chat.id,
            username=user.username,
        )

        await update.message.reply_text(
            "🤖 歡迎黎到日綫兩陽選股機器人!\n\n"
            "此bot會每日掃描所有符合日綫兩陽指標既加密幣種，並且會根據排名，揀出10隻最值得投資既幣種，發送俾你.\n\n"
            "Use /help to see available commands."
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            "Available commands:\n\n"
            "/settings - Show current settings\n"
            "/subscribe - Subscribe to daily notifications\n"
            "/unsubscribe - Unsubscribe from notifications\n"
            # "/settime HH:MM - Set your preferred notification time (24h format)\n"
            "/help - Show this help message"
        )

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current settings"""
        chat_id = update.effective_chat.id
        settings = self.db.get_user_settings(chat_id)
        
        if settings:
            scan_days, notification_time = settings
            await update.message.reply_text(
                f"Current settings:\n"
                f"報價貨幣: {self.crypto_strategy.quote_currency}\n"
                # f"Notification time: {notification_time}\n"
                f"Status: {'Subscribed' if self.db.get_active_subscribers() else 'Unsubscribed'}"
            )
        else:
            await update.message.reply_text("No settings found. Use /subscribe to start receiving notifications.")

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Subscribe to notifications"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        if self.db.add_subscriber(
            chat_id=chat_id,
            username=user.username,
        ):
            await update.message.reply_text(
                "✅ Successfully subscribed to notifications!\n"
            )
        else:
            await update.message.reply_text("❌ Failed to subscribe. Please try again later.")

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unsubscribe from notifications"""
        chat_id = update.effective_chat.id
        
        if self.db.remove_subscriber(chat_id):
            await update.message.reply_text("✅ Successfully unsubscribed from notifications.")
        else:
            await update.message.reply_text("❌ Failed to unsubscribe. Please try again later.")

    async def scheduled_scan(self, context: CallbackContext):
        """Run scheduled scan for a specific subscriber"""
        job_data = context.job.data
        chat_id = job_data['chat_id']
        scan_days = job_data['scan_days']
        
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔄 Running scheduled scan ({scan_days} days of data)..."
            )
            
            # Initialize the strategy with parameters
            self.crypto_strategy = CryptoTradingStrategy(quote_currency='USDT')
            
            # Fetch and process data
            await context.bot.send_message(
                chat_id=chat_id,
                text="⏳ Fetching market data..."
            )
            
            pairs_count = self.crypto_strategy.fetch_data()
            
            # Filter pairs with signals
            matching_pairs = self.crypto_strategy.filter_pairs_with_signals()
            
            # Format and send results
            if matching_pairs:
                message = f"✅ Found {len(matching_pairs)} matching pairs at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n\n"
                
                for i, pair in enumerate(matching_pairs[:10], 1):
                    message += (
                        f"{i}. {pair['symbol']}\n"
                        f"   Price: ${pair['last_close']:.6f}\n"
                        f"   Stop Loss: ${pair['stop_loss']:.6f} (Risk: {pair['risk_pct']:.2f}%)\n\n"
                    )
                    
                if len(matching_pairs) > 10:
                    message += f"...and {len(matching_pairs) - 10} more pairs."
                
                await context.bot.send_message(chat_id=chat_id, text=message)
                self.db.update_last_notification(chat_id)
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ No matching pairs found in scheduled scan."
                )
        except TelegramError as e:
            logger.error(f"Error sending scheduled message to {chat_id}: {e}")
        except Exception as e:
            logger.error(f"Error during scheduled scan: {e}")
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Error during scheduled scan: {str(e)}"
                )
            except:
                pass

    def run(self):
        """Start the bot."""
        self.application.run_polling()


def main():
    """Main function to start the bot"""
    # Check if token is set
    token = TELEGRAM_BOT_TOKEN
    
    # If token is not set in environment variable, prompt for it
    if not token:
        print("Telegram Bot Token not found in environment variable 'API_KEY'")
        token = input("Please enter your Telegram Bot Token: ")
        
    if not token:
        print("No token provided. Exiting...")
        return
        
    # Validate token format (basic check)
    if ":" not in token:
        print("Invalid token format. Token should contain a colon (:). Please check your token.")
        return

    # Create and run the bot
    try:
        print("Starting bot...")
        bot = CryptoSignalBot(token)
        bot.run()
    except Exception as e:
        print(f"Error starting bot: {str(e)}")


if __name__ == "__main__":
    main() 