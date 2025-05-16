import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file="subscribers.db"):
        """Initialize database connection"""
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_file)

    def init_db(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create subscribers table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS subscribers (
                        chat_id INTEGER PRIMARY KEY,
                        username TEXT,
                        subscribed_at TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        last_notification TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def add_subscriber(self, chat_id, username=None):
        """Add a new subscriber"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO subscribers 
                    (chat_id, username, subscribed_at, is_active)
                    VALUES (?, ?, ?, 1)
                ''', (chat_id, username, datetime.now()))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding subscriber: {e}")
            return False

    def remove_subscriber(self, chat_id):
        """Remove a subscriber"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE subscribers 
                    SET is_active = 0 
                    WHERE chat_id = ?
                ''', (chat_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing subscriber: {e}")
            return False

    def get_active_subscribers(self):
        """Get all active subscribers"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, username
                    FROM subscribers
                    WHERE is_active = 1
                ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting active subscribers: {e}")
            return []

    def update_last_notification(self, chat_id):
        """Update last notification timestamp"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE subscribers 
                    SET last_notification = ? 
                    WHERE chat_id = ?
                ''', (datetime.now(), chat_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating last notification: {e}")
            return False
