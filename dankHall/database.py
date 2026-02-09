from __future__ import annotations
from typing import List, Tuple, Dict, Any
from datetime import datetime
import sys
import os

try:
    import psycopg as pg
except ImportError:
    print("ERROR: psycopg library not found. Install with: pip install psycopg", file=sys.stderr)
    pg = None


class DankDatabase:
    """
    Database wrapper for Dank Hall statistics and tracking.
    
    Uses psycopg to connect directly to PostgreSQL.
    """
    
    # Database connection configuration
    # Modify these values to match your database setup
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "postgres_container"),
        "dbname": os.getenv("DB_NAME", "discord"),
        "user": os.getenv("DB_USER", "redbot"),
        "password": os.getenv("DB_PASSWORD"),  # No default!
        "port": int(os.getenv("DB_PORT", "5432"))
    }
    
    def __init__(self):
        """Initialize database connection."""
        if pg is None:
            self.conn = None
            print("Database connection unavailable - psycopg not installed", file=sys.stderr)
            return
        
        try:
            self.conn = pg.connect(**self.DB_CONFIG)
            print(f"Connected to database: {self.DB_CONFIG['dbname']}", file=sys.stderr)
        except Exception as e:
            self.conn = None
            print(f"Database connection failed: {e}", file=sys.stderr)
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def _execute(self, query: str, params: list = None):
        """Execute a query without returning results."""
        if not self.conn:
            return
        
        try:
            cur = self.conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            self.conn.commit()
            cur.close()
        except Exception as e:
            print(f"Database execute error: {e}", file=sys.stderr)
            self.conn.rollback()
            raise
    
    def _query_one(self, query: str, params: list = None):
        """Execute a query and return one result."""
        if not self.conn:
            return None
        
        try:
            cur = self.conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            result = cur.fetchone()
            cur.close()
            return result
        except Exception as e:
            print(f"Database query error: {e}", file=sys.stderr)
            return None
    
    def _query_all(self, query: str, params: list = None):
        """Execute a query and return all results."""
        if not self.conn:
            return []
        
        try:
            cur = self.conn.cursor()
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            results = cur.fetchall()
            cur.close()
            return results
        except Exception as e:
            print(f"Database query error: {e}", file=sys.stderr)
            return []
    
    async def create_tables(self):
        """
        Create necessary database tables if they don't exist.
        
        Table: dank_certified_messages
        - Tracks all certified messages
        - Prevents duplicate certifications
        - Stores stats for leaderboards
        """
        if not self.conn:
            print("Cannot create tables - no database connection", file=sys.stderr)
            return
        
        try:
            # Main table for certified messages
            self._execute("""
                CREATE TABLE IF NOT EXISTS dank_certified_messages (
                    message_id BIGINT PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    channel_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    emoji TEXT NOT NULL,
                    reaction_count INTEGER NOT NULL,
                    hall_message_id BIGINT,
                    hall_channel_id BIGINT,
                    certified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add hall_channel_id column if it doesn't exist (migration for existing tables)
            try:
                self._execute("""
                    ALTER TABLE dank_certified_messages 
                    ADD COLUMN IF NOT EXISTS hall_channel_id BIGINT
                """)
            except:
                pass  # Column might already exist or ALTER not supported
            
            # Create indexes separately
            self._execute("""
                CREATE INDEX IF NOT EXISTS idx_guild_user 
                ON dank_certified_messages(guild_id, user_id)
            """)
            
            self._execute("""
                CREATE INDEX IF NOT EXISTS idx_guild_channel 
                ON dank_certified_messages(guild_id, channel_id)
            """)
            
            self._execute("""
                CREATE INDEX IF NOT EXISTS idx_hall_channel 
                ON dank_certified_messages(guild_id, hall_channel_id)
            """)
            
            print("Database tables created successfully", file=sys.stderr)
        except Exception as e:
            print(f"Error creating tables: {e}", file=sys.stderr)
    
    # ==================== Certification Tracking ====================
    
    async def is_certified(self, message_id: int) -> bool:
        """Check if a message is already certified."""
        if not self.conn:
            return False
        
        try:
            result = self._query_one(
                "SELECT 1 FROM dank_certified_messages WHERE message_id = %s",
                [message_id]
            )
            return result is not None
        except Exception as e:
            print(f"Error checking certification: {e}", file=sys.stderr)
            return False
    
    async def add_certified_message(
        self,
        message_id: int,
        guild_id: int,
        channel_id: int,
        user_id: int,
        emoji: str,
        hall_message_id: int,
        reaction_count: int,
        hall_channel_id: int = None
    ) -> bool:
        """Add a newly certified message to the database."""
        if not self.conn:
            return False
        
        try:
            self._execute(
                """
                INSERT INTO dank_certified_messages 
                (message_id, guild_id, channel_id, user_id, emoji, hall_message_id, reaction_count, hall_channel_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [message_id, guild_id, channel_id, user_id, emoji, hall_message_id, reaction_count, hall_channel_id]
            )
            return True
        except Exception as e:
            print(f"Error adding certified message: {e}", file=sys.stderr)
            return False
    
    async def update_reaction_count(
        self,
        message_id: int,
        new_count: int
    ) -> bool:
        """Update the reaction count for a certified message if it's higher."""
        if not self.conn:
            return False
        
        try:
            self._execute(
                """
                UPDATE dank_certified_messages 
                SET reaction_count = %s
                WHERE message_id = %s AND reaction_count < %s
                """,
                [new_count, message_id, new_count]
            )
            return True
        except Exception as e:
            print(f"Error updating reaction count: {e}", file=sys.stderr)
            return False
    
    async def get_certified_message(self, message_id: int) -> dict:
        """Get details about a certified message."""
        if not self.conn:
            return None
        
        try:
            result = self._query_one(
                """
                SELECT message_id, guild_id, channel_id, user_id, emoji, 
                       hall_message_id, reaction_count, certified_at
                FROM dank_certified_messages 
                WHERE message_id = %s
                """,
                [message_id]
            )
            
            if result:
                return {
                    "message_id": result[0],
                    "guild_id": result[1],
                    "channel_id": result[2],
                    "user_id": result[3],
                    "emoji": result[4],
                    "hall_message_id": result[5],
                    "reaction_count": result[6],
                    "certified_at": result[7]
                }
            return None
        except Exception as e:
            print(f"Error getting certified message: {e}", file=sys.stderr)
            return None
    
    # ==================== Statistics Queries ====================
    
    async def get_user_stats(self, guild_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive stats for a user in a guild.
        
        Returns:
        - total: Total certifications
        - by_emoji: List of (emoji, count) tuples
        """
        if not self.conn:
            return {"total": 0, "by_emoji": []}
        
        try:
            # Total certifications
            total_result = self._query_one(
                """
                SELECT COUNT(*) 
                FROM dank_certified_messages 
                WHERE guild_id = %s AND user_id = %s
                """,
                [guild_id, user_id]
            )
            total = total_result[0] if total_result else 0
            
            # By emoji
            emoji_results = self._query_all(
                """
                SELECT emoji, COUNT(*) as count
                FROM dank_certified_messages
                WHERE guild_id = %s AND user_id = %s
                GROUP BY emoji
                ORDER BY count DESC
                LIMIT 10
                """,
                [guild_id, user_id]
            )
            
            return {
                "total": total,
                "by_emoji": [(row[0], row[1]) for row in emoji_results]
            }
        except Exception as e:
            print(f"Error getting user stats: {e}", file=sys.stderr)
            return {"total": 0, "by_emoji": []}
    
    async def get_user_rank(self, guild_id: int, user_id: int) -> int:
        """Get a user's rank in the guild leaderboard."""
        if not self.conn:
            return 0
        
        try:
            result = self._query_one(
                """
                SELECT COUNT(*) + 1
                FROM (
                    SELECT user_id, COUNT(*) as cert_count
                    FROM dank_certified_messages
                    WHERE guild_id = %s
                    GROUP BY user_id
                ) as user_counts
                WHERE cert_count > (
                    SELECT COUNT(*)
                    FROM dank_certified_messages
                    WHERE guild_id = %s AND user_id = %s
                )
                """,
                [guild_id, guild_id, user_id]
            )
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting user rank: {e}", file=sys.stderr)
            return 0
    
    async def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Tuple[int, int]]:
        """
        Get the top users by certification count.
        
        Returns: List of (user_id, count) tuples
        """
        if not self.conn:
            return []
        
        try:
            results = self._query_all(
                """
                SELECT user_id, COUNT(*) as cert_count
                FROM dank_certified_messages
                WHERE guild_id = %s
                GROUP BY user_id
                ORDER BY cert_count DESC
                LIMIT %s
                """,
                [guild_id, limit]
            )
            return [(row[0], row[1]) for row in results]
        except Exception as e:
            print(f"Error getting leaderboard: {e}", file=sys.stderr)
            return []
    
    async def get_top_channels(self, guild_id: int, limit: int = 10) -> List[Tuple[int, int]]:
        """
        Get the channels with the most certifications.
        
        Returns: List of (channel_id, count) tuples
        """
        if not self.conn:
            return []
        
        try:
            results = self._query_all(
                """
                SELECT channel_id, COUNT(*) as cert_count
                FROM dank_certified_messages
                WHERE guild_id = %s
                GROUP BY channel_id
                ORDER BY cert_count DESC
                LIMIT %s
                """,
                [guild_id, limit]
            )
            return [(row[0], row[1]) for row in results]
        except Exception as e:
            print(f"Error getting top channels: {e}", file=sys.stderr)
            return []
    
    async def get_top_emojis(self, guild_id: int, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get the most popular certification emojis.
        
        Returns: List of (emoji, count) tuples
        """
        if not self.conn:
            return []
        
        try:
            results = self._query_all(
                """
                SELECT emoji, COUNT(*) as cert_count
                FROM dank_certified_messages
                WHERE guild_id = %s
                GROUP BY emoji
                ORDER BY cert_count DESC
                LIMIT %s
                """,
                [guild_id, limit]
            )
            return [(row[0], row[1]) for row in results]
        except Exception as e:
            print(f"Error getting top emojis: {e}", file=sys.stderr)
            return []
    
    async def get_total_certifications(self, guild_id: int) -> int:
        """Get the total number of certifications in a guild."""
        if not self.conn:
            return 0
        
        try:
            result = self._query_one(
                "SELECT COUNT(*) FROM dank_certified_messages WHERE guild_id = %s",
                [guild_id]
            )
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting total certifications: {e}", file=sys.stderr)
            return 0
    
    async def get_god_tier_posts(self, guild_id: int) -> List[Dict[str, Any]]:
        """
        Get all posts with the highest reaction count (god tier).
        
        Returns: List of dicts with post details
        """
        if not self.conn:
            return []
        
        try:
            # First, get the highest reaction count
            max_result = self._query_one(
                """
                SELECT MAX(reaction_count)
                FROM dank_certified_messages
                WHERE guild_id = %s
                """,
                [guild_id]
            )
            
            if not max_result or max_result[0] is None:
                return []
            
            max_count = max_result[0]
            
            # Now get all posts with that count
            results = self._query_all(
                """
                SELECT message_id, channel_id, user_id, emoji, reaction_count, 
                       hall_message_id, certified_at
                FROM dank_certified_messages
                WHERE guild_id = %s AND reaction_count = %s
                ORDER BY certified_at DESC
                """,
                [guild_id, max_count]
            )
            
            posts = []
            for row in results:
                posts.append({
                    "message_id": row[0],
                    "channel_id": row[1],
                    "user_id": row[2],
                    "emoji": row[3],
                    "reaction_count": row[4],
                    "hall_message_id": row[5],
                    "certified_at": row[6]
                })
            
            return posts
        except Exception as e:
            print(f"Error getting god tier posts: {e}", file=sys.stderr)
            return []
    
    async def get_random_certification(self, guild_id: int) -> dict:
        """Get a random certified message from the guild."""
        if not self.conn:
            return None
        
        try:
            result = self._query_one(
                """
                SELECT message_id, guild_id, channel_id, user_id, emoji, 
                       hall_message_id, reaction_count, certified_at
                FROM dank_certified_messages
                WHERE guild_id = %s
                ORDER BY RANDOM()
                LIMIT 1
                """,
                [guild_id]
            )
            
            if result:
                return {
                    "message_id": result[0],
                    "guild_id": result[1],
                    "channel_id": result[2],
                    "user_id": result[3],
                    "emoji": result[4],
                    "hall_message_id": result[5],
                    "reaction_count": result[6],
                    "certified_at": result[7]
                }
            return None
        except Exception as e:
            print(f"Error getting random certification: {e}", file=sys.stderr)
            return None
    
    async def get_random_certification_with_count(self, guild_id: int, reaction_count: int) -> dict:
        """Get a random certified message with a specific reaction count."""
        if not self.conn:
            return None
        
        try:
            result = self._query_one(
                """
                SELECT message_id, guild_id, channel_id, user_id, emoji, 
                       hall_message_id, reaction_count, certified_at
                FROM dank_certified_messages
                WHERE guild_id = %s AND reaction_count = %s
                ORDER BY RANDOM()
                LIMIT 1
                """,
                [guild_id, reaction_count]
            )
            
            if result:
                return {
                    "message_id": result[0],
                    "guild_id": result[1],
                    "channel_id": result[2],
                    "user_id": result[3],
                    "emoji": result[4],
                    "hall_message_id": result[5],
                    "reaction_count": result[6],
                    "certified_at": result[7]
                }
            return None
        except Exception as e:
            print(f"Error getting random certification with count: {e}", file=sys.stderr)
            return None
    
    async def get_random_certification_with_emoji(self, guild_id: int, emoji: str) -> dict:
        """Get a random certified message with a specific emoji."""
        if not self.conn:
            return None
        
        try:
            result = self._query_one(
                """
                SELECT message_id, guild_id, channel_id, user_id, emoji, 
                       hall_message_id, reaction_count, certified_at
                FROM dank_certified_messages
                WHERE guild_id = %s AND emoji = %s
                ORDER BY RANDOM()
                LIMIT 1
                """,
                [guild_id, emoji]
            )
            
            if result:
                return {
                    "message_id": result[0],
                    "guild_id": result[1],
                    "channel_id": result[2],
                    "user_id": result[3],
                    "emoji": result[4],
                    "hall_message_id": result[5],
                    "reaction_count": result[6],
                    "certified_at": result[7]
                }
            return None
        except Exception as e:
            print(f"Error getting random certification with emoji: {e}", file=sys.stderr)
            return None
    
    async def get_random_certification_with_filters(
        self, 
        guild_id: int, 
        reaction_count: int = None, 
        emoji: str = None
    ) -> dict:
        """Get a random certified message with optional filters."""
        if not self.conn:
            return None
        
        try:
            # Build query dynamically based on filters
            query = """
                SELECT message_id, guild_id, channel_id, user_id, emoji, 
                       hall_message_id, reaction_count, certified_at
                FROM dank_certified_messages
                WHERE guild_id = %s
            """
            params = [guild_id]
            
            if reaction_count is not None:
                query += " AND reaction_count = %s"
                params.append(reaction_count)
            
            if emoji is not None:
                query += " AND emoji = %s"
                params.append(emoji)
            
            query += " ORDER BY RANDOM() LIMIT 1"
            
            result = self._query_one(query, params)
            
            if result:
                return {
                    "message_id": result[0],
                    "guild_id": result[1],
                    "channel_id": result[2],
                    "user_id": result[3],
                    "emoji": result[4],
                    "hall_message_id": result[5],
                    "reaction_count": result[6],
                    "certified_at": result[7]
                }
            return None
        except Exception as e:
            print(f"Error getting random certification with filters: {e}", file=sys.stderr)
            return None
    
    async def get_random_certification_by_hall(self, guild_id: int, hall_channel_id: int) -> dict:
        """Get a random certified message from a specific hall of fame channel."""
        if not self.conn:
            return None
        
        try:
            result = self._query_one(
                """
                SELECT message_id, guild_id, channel_id, user_id, emoji, 
                       hall_message_id, reaction_count, certified_at
                FROM dank_certified_messages
                WHERE guild_id = %s AND hall_channel_id = %s
                ORDER BY RANDOM()
                LIMIT 1
                """,
                [guild_id, hall_channel_id]
            )
            
            if result:
                return {
                    "message_id": result[0],
                    "guild_id": result[1],
                    "channel_id": result[2],
                    "user_id": result[3],
                    "emoji": result[4],
                    "hall_message_id": result[5],
                    "reaction_count": result[6],
                    "certified_at": result[7]
                }
            return None
        except Exception as e:
            print(f"Error getting random certification by hall: {e}", file=sys.stderr)
            return None