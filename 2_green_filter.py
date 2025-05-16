import pandas as pd
import numpy as np
import datetime
import ccxt
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from typing import List, Dict, Tuple, Optional

class CryptoTradingStrategy:
    def __init__(self, quote_currency='USDT', days_to_fetch=3):
        """
        Initialize the strategy with Binance API and configuration.
        
        Args:
            quote_currency: The quote currency to filter pairs (e.g., 'USDT', 'BTC')
            days_to_fetch: Number of days of historical data to fetch
        """
        self.exchange = ccxt.binance()
        self.quote_currency = quote_currency
        self.days_to_fetch = days_to_fetch
        self.timeframe = '1d'  # Daily timeframe
        self.data = {}
        self.signals = {}
        self.matching_pairs = []
    
    def fetch_all_pairs(self):
        """Fetch all available cryptocurrency pairs from Binance that match the quote currency."""
        try:
            # Load markets from Binance
            markets = self.exchange.load_markets()
            
            # Filter by quote currency
            symbols = [
                symbol for symbol in markets.keys() 
                if symbol.endswith(f'/{self.quote_currency}')
            ]
            
            print(f"Found {len(symbols)} pairs with {self.quote_currency} as quote currency")
            return symbols
        except Exception as e:
            print(f"Error fetching market pairs: {str(e)}")
            return []
    
    def fetch_data(self, limit_pairs=None):
        """
        Fetch historical data for all cryptocurrency pairs.
        
        Args:
            limit_pairs: Optional limit on number of pairs to analyze (for testing)
        """
        # Get all available pairs
        all_symbols = self.fetch_all_pairs()
        
        # Limit the number of pairs if specified
        symbols = all_symbols[:limit_pairs] if limit_pairs else all_symbols
        
        print(f"Fetching data for {len(symbols)} cryptocurrency pairs...")
        
        # Calculate millisecond timestamp for start date
        since = int((datetime.datetime.now() - datetime.timedelta(days=self.days_to_fetch)).timestamp() * 1000)
        
        for symbol in symbols:
            try:
                # Fetch OHLCV data from Binance
                ohlcv = self.exchange.fetch_ohlcv(symbol, self.timeframe, since=since)
                
                if len(ohlcv) > 0:
                    # Convert to DataFrame
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    
                    print(f"✓ {symbol}: {len(df)} days of data")
                    
                    # Calculate if candle is green (Close > Open)
                    df['is_green'] = df['Close'] > df['Open']
                    
                    # Calculate the 28-day Moving Average
                    df['MA28'] = df['Close'].rolling(window=28).mean()
                    
                    # Calculate candle low points
                    df['low_point'] = df['Low']
                    
                    print(df)
                    
                    self.data[symbol] = df
                else:
                    print(f"✗ {symbol}: No data available")
            except Exception as e:
                print(f"✗ Error fetching {symbol}: {str(e)}")
            
            # Add a small delay to avoid rate limits
            self.exchange.sleep(50)  # 50ms delay between requests
        
        return len(self.data)
    
    def filter_pairs_with_signals(self):
        """
        Filter cryptocurrency pairs that match our entry conditions:
        1. Two consecutive green candles
        2. Close of 2nd candle above MA28
        
        Returns:
            List of matching pairs with signal details
        """
        matching_pairs = []
        
        for symbol, df in self.data.items():
            # Skip if not enough data or MA28 isn't established yet
            if len(df) < 30 or df['MA28'].isna().iloc[-1]:
                continue
                
            # Check the last two candles
            if len(df) >= 2:
                last_candle = df.iloc[-1]
                second_last_candle = df.iloc[-2]
                
                # Check conditions:
                # 1. Last two candles are green
                # 2. Last candle closes above MA28
                if (last_candle['is_green'] and 
                    second_last_candle['is_green'] and 
                    last_candle['Close'] > last_candle['MA28']):
                    
                    # Find the lowest point of the two green candles for stop loss
                    stop_loss = min(last_candle['Low'], second_last_candle['Low'])
                    
                    # Calculate risk percentage
                    risk_pct = (last_candle['Close'] / stop_loss - 1) * 100
                    
                    matching_pairs.append({
                        'symbol': symbol,
                        'last_close': last_candle['Close'],
                        'last_date': df.index[-1],
                        'ma28': last_candle['MA28'],
                        'stop_loss': stop_loss,
                        'risk_pct': risk_pct,
                        'volume': last_candle['Volume']
                    })
        
        # Sort by volume (descending) to prioritize more liquid pairs
        matching_pairs = sorted(matching_pairs, key=lambda x: x['volume'], reverse=True)
        self.matching_pairs = matching_pairs
        
        return matching_pairs
    
    def display_matching_pairs(self):
        """Display the matching pairs in a nice formatted table."""
        if not self.matching_pairs:
            print("No cryptocurrency pairs match the criteria currently.")
            return
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(self.matching_pairs)
        
        # Format columns
        df['last_close'] = df['last_close'].map('${:,.6f}'.format)
        df['ma28'] = df['ma28'].map('${:,.6f}'.format)
        df['stop_loss'] = df['stop_loss'].map('${:,.6f}'.format)
        df['risk_pct'] = df['risk_pct'].map('{:.2f}%'.format)
        df['volume'] = df['volume'].map('${:,.0f}'.format)
        
        # Print the table
        print(f"\n{len(df)} Cryptocurrency Pairs Match the Entry Criteria:")
        print("=" * 100)
        print(df[['symbol', 'last_date', 'last_close', 'ma28', 'stop_loss', 'risk_pct', 'volume']])
        print("=" * 100)
    
    def visualize_pair(self, symbol):
        """
        Visualize a specific cryptocurrency pair with entry signals.
        
        Args:
            symbol: The cryptocurrency symbol to visualize
        """
        if symbol not in self.data:
            print(f"No data available for {symbol}")
            return
        
        df = self.data[symbol]
        
        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot close price
        ax.plot(df.index, df['Close'], label='Close Price', color='blue', alpha=0.5)
        
        # Plot MA28
        ax.plot(df.index, df['MA28'], label='MA28', color='orange', linewidth=1)
        
        # Plot green and red candles
        green_candles = df[df['is_green']]
        red_candles = df[~df['is_green']]
        
        # Use stems to represent candles
        ax.vlines(x=green_candles.index, ymin=green_candles['Open'], ymax=green_candles['Close'], 
                 color='green', alpha=0.7, linewidth=4)
        ax.vlines(x=red_candles.index, ymin=red_candles['Open'], ymax=red_candles['Close'], 
                 color='red', alpha=0.7, linewidth=4)
        
        # Add high-low lines
        ax.vlines(x=df.index, ymin=df['Low'], ymax=df['High'], 
                 color='black', alpha=0.2, linewidth=1)
        
        # Check for entry signal at the end
        if len(df) >= 2 and df['is_green'].iloc[-1] and df['is_green'].iloc[-2] and df['Close'].iloc[-1] > df['MA28'].iloc[-1]:
            ax.scatter([df.index[-1]], [df['Close'].iloc[-1]], 
                      marker='^', color='green', s=120, label='Entry Signal')
            
            # Show stop loss
            stop_loss = min(df['Low'].iloc[-1], df['Low'].iloc[-2])
            ax.axhline(y=stop_loss, color='red', linestyle='--', 
                      label=f'Stop Loss: ${stop_loss:.6f}')
        
        # Add title and labels
        ax.set_title(f'{symbol} - Trading Strategy Visualization', fontsize=16)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format dates on x-axis
        date_form = DateFormatter("%Y-%m-%d")
        ax.xaxis.set_major_formatter(date_form)
        plt.xticks(rotation=45)
        
        # Add legend
        ax.legend()
        
        plt.tight_layout()
        plt.show()


# Example usage
if __name__ == "__main__":
    # Create the strategy instance
    # Note: You might need to install ccxt package first: pip install ccxt
    strategy = CryptoTradingStrategy(quote_currency='USDT', days_to_fetch=3)
    
    # Fetch data for all available pairs (limit to 20 for testing)
    # Remove the limit for production use
    strategy.fetch_data()
    
    # Filter pairs that match our signal conditions
    matching_pairs = strategy.filter_pairs_with_signals()
    
    # Display matching pairs
    strategy.display_matching_pairs()
    
    # # Visualize the first matching pair (if any exist)
    # if strategy.matching_pairs:
    #     top_pair = strategy.matching_pairs[0]['symbol']
    #     print(f"\nVisualizing top matching pair: {top_pair}")
    #     strategy.visualize_pair(top_pair)