from __future__ import annotations
from typing import List, Tuple, Dict, Any
from datetime import datetime
import sys

# Import the existing database class
# Adjust the import path based on where db.py is located relative to this cog
try:
    from ...dbclass import db
except:
    # Fallback if the path is different
    try:
        from dbclass import db
    except:
        print("WARNING: Could not import database class. Stats will not work.", file=sys.stderr)
        db = None


class DankDatabase:
    """
    Database wrapper for Dank Hall statistics and tracking.
    
    Uses the existing db.py class to interface with PostgreSQL.
    """
    
    def __init__(self):
        """Initialize database connection."""
        if db is None:
            self.conn = None
            print("Database connection unavailable", file=sys.stderr)
        else:
            try:
                self.conn = db()
            except Exception as e:
                self.conn = None
                print(f"Database connection failed: {e}", file=sys.stderr)
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            del self.conn
    
    async def create_tables(self):
        """
        Create necessary database tables if they don't exist.
        
        Table: dank_certified_messages
        - Tracks all certified messages
        - Prevents duplicate certifications
        - Stores stats for leaderboards
        """
        if not self.conn:
            return
        
        try:
            # Main table for certified messages
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS dank_certified_messages (
                    message_id BIGINT PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    channel_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    emoji TEXT NOT NULL,
                    reaction_count INTEGER NOT NULL,
                    hall_message_id BIGINT,
                    certified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes separately
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_guild_user 
                ON dank_certified_messages(guild_id, user_id)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_guild_channel 
                ON dank_certified_messages(guild_id, channel_id)
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
            result = self.conn.querySingle(
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
        reaction_count: int
    ) -> bool:
        """Add a newly certified message to the database."""
        if not self.conn:
            return False
        
        try:
            self.conn.execute(
                """
                INSERT INTO dank_certified_messages 
                (message_id, guild_id, channel_id, user_id, emoji, hall_message_id, reaction_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [message_id, guild_id, channel_id, user_id, emoji, hall_message_id, reaction_count]
            )
            return True
        except Exception as e:
            print(f"Error adding certified message: {e}", file=sys.stderr)
            return False
    
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
            total_result = self.conn.querySingle(
                """
                SELECT COUNT(*) 
                FROM dank_certified_messages 
                WHERE guild_id = %s AND user_id = %s
                """,
                [guild_id, user_id]
            )
            total = total_result[0] if total_result else 0
            
            # By emoji
            emoji_results = self.conn.queryAll(
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
            result = self.conn.querySingle(
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
            results = self.conn.queryAll(
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
            results = self.conn.queryAll(
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
            results = self.conn.queryAll(
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
            result = self.conn.querySingle(
                "SELECT COUNT(*) FROM dank_certified_messages WHERE guild_id = %s",
                [guild_id]
            )
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting total certifications: {e}", file=sys.stderr)
            return 0