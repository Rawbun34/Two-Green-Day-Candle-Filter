# Crypto Trading Signal Bot

A Python-based trading signal bot that identifies cryptocurrency pairs matching specific criteria and sends notifications via Telegram.

## Features

- Scans Binance market for pairs matching the "Two Green Candles" strategy:
  - Two consecutive green candles (Close > Open)
  - Last candle's close price above the 28-day Moving Average
- Sends real-time notifications via Telegram
- Supports manual scanning via bot commands
- Scheduled notifications at preset times
- Security features to restrict access to authorized users

## Prerequisites

- Python 3.7+
- Telegram bot token (obtained from [@BotFather](https://t.me/botfather))
- Binance API access (no API key needed for this version as it uses public endpoints)

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd <repository-directory>
```

2. Install required packages:
```
pip install python-telegram-bot requests pandas numpy matplotlib
```

## Configuration

### Telegram Bot Token

You can provide your Telegram Bot Token in one of two ways:

1. **Environment Variable (Recommended):**
   - Set an environment variable called `API_KEY` with your Telegram Bot Token:
     - Windows: `set API_KEY=your_token_here`
     - Linux/macOS: `export API_KEY=your_token_here`

2. **Manual Input:**
   - If no environment variable is found, the bot will prompt you to enter your token when starting the program

### Additional Configuration

1. Update the `ALLOWED_CHAT_IDS` list in `crypto_telegram_bot.py` with your Telegram User ID
   - You can get your ID from [@userinfobot](https://t.me/userinfobot)
2. Optionally modify the `SCHEDULE_TIMES` list to set your preferred notification times (in UTC)

## Usage

### Starting the Bot

Run the bot with:
```
python crypto_telegram_bot.py
```

### Telegram Commands

Once the bot is running, open Telegram and use these commands:

- `/start` - Start interacting with the bot
- `/help` - Show available commands
- `/scan` - Scan for signals using default settings (30 days of data)
- `/scan [days]` - Scan with a specific number of days (e.g., `/scan 45`)
- `/settings` - Show current strategy settings

### Scheduled Notifications

The bot will automatically send notifications at midnight UTC by default. You can customize the schedule by modifying the `SCHEDULE_TIMES` array in the code.

## Strategy Details

The "Two Green Candles" strategy identifies pairs where:

1. The last two daily candles are green (Close > Open)
2. The latest close price is above the 28-day Moving Average
3. A stop loss is calculated at the lowest point of the two green candles

All pairs are sorted by trading volume to prioritize more liquid assets.

## Customization

You can modify various aspects of the strategy in `two_green_filter_binance.py`:

- `quote_currency` - The quote currency to filter pairs (default: 'USDT')
- `days_to_fetch` - Number of days of historical data to fetch
- `timeframe` - The candle timeframe (default: '1d' for daily)

## Troubleshooting

- **Token Invalid Error**: Make sure your token is correct and properly formatted (should contain a colon)
- **Connection Issues**: Ensure you have internet connectivity and can access the Telegram API
- **Rate Limiting**: The bot includes delays to avoid Binance API rate limits, but you may need to adjust these if encountering issues

## License

[Include your license information here]

## Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS. 