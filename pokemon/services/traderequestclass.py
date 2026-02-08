# services/traderequestclass.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from .dbclass import dbconn

class TradeRequest:
    """Service class for managing async Pokemon trade requests"""
    
    # Trade status constants
    STATUS_PENDING_RECEIVER = 'PENDING_RECEIVER_RESPONSE'
    STATUS_PENDING_SENDER = 'PENDING_SENDER_ACCEPTANCE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED_SENDER = 'CANCELLED_BY_SENDER'
    STATUS_CANCELLED_RECEIVER = 'CANCELLED_BY_RECEIVER'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_INVALID = 'INVALID'
    
    def __init__(self):
        self.statuscode = 0
        self.message = ''
    
    def create_trade_request(self, sender_discord_id: str, receiver_discord_id: str, sender_pokemon_id: int) -> Optional[int]:
        """Create a new trade request. Returns trade_id or None on failure."""
        db = None
        try:
            db = dbconn()
            query = """
                INSERT INTO trade_requests 
                (sender_discord_id, receiver_discord_id, sender_pokemon_id, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING trade_id
            """
            result = db.querySingle(query, [
                sender_discord_id, 
                receiver_discord_id, 
                sender_pokemon_id,
                self.STATUS_PENDING_RECEIVER
            ])
            
            if result:
                self.statuscode = 0
                self.message = 'Trade request created successfully'
                return result['trade_id']
            else:
                self.statuscode = 1
                self.message = 'Failed to create trade request'
                return None
                
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error creating trade request: {str(e)}'
            return None
        finally:
            if db:
                del db
    
    def get_active_trade(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Get any active trade involving this user. Returns trade data or None."""
        db = None
        try:
            db = dbconn()
            query = """
                SELECT 
                    t.*,
                    sp."pokemonName" as sender_pokemon_name,
                    sp."nickName" as sender_pokemon_nickname,
                    sp."currentLevel" as sender_pokemon_level,
                    rp."pokemonName" as receiver_pokemon_name,
                    rp."nickName" as receiver_pokemon_nickname,
                    rp."currentLevel" as receiver_pokemon_level
                FROM trade_requests t
                LEFT JOIN pokemon sp ON t.sender_pokemon_id = sp.id
                LEFT JOIN pokemon rp ON t.receiver_pokemon_id = rp.id
                WHERE (t.sender_discord_id = %s OR t.receiver_discord_id = %s)
                AND t.status IN (%s, %s)
                ORDER BY t.created_at DESC
                LIMIT 1
            """
            result = db.querySingle(query, [
                discord_id, 
                discord_id,
                self.STATUS_PENDING_RECEIVER,
                self.STATUS_PENDING_SENDER
            ])
            
            return result
            
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error fetching active trade: {str(e)}'
            return None
        finally:
            if db:
                del db
    
    def has_active_trade(self, discord_id: str) -> bool:
        """Check if user has any active trade."""
        return self.get_active_trade(discord_id) is not None
    
    def get_trade_by_id(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """Get trade request by ID with Pokemon details."""
        db = None
        try:
            db = dbconn()
            query = """
                SELECT 
                    t.*,
                    sp."pokemonName" as sender_pokemon_name,
                    sp."nickName" as sender_pokemon_nickname,
                    sp."currentLevel" as sender_pokemon_level,
                    sp.type_1 as sender_type_1,
                    sp.type_2 as sender_type_2,
                    rp."pokemonName" as receiver_pokemon_name,
                    rp."nickName" as receiver_pokemon_nickname,
                    rp."currentLevel" as receiver_pokemon_level,
                    rp.type_1 as receiver_type_1,
                    rp.type_2 as receiver_type_2
                FROM trade_requests t
                LEFT JOIN pokemon sp ON t.sender_pokemon_id = sp.id
                LEFT JOIN pokemon rp ON t.receiver_pokemon_id = rp.id
                WHERE t.trade_id = %s
            """
            result = db.querySingle(query, [trade_id])
            
            return result
            
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error fetching trade: {str(e)}'
            return None
        finally:
            if db:
                del db
    
    def update_receiver_pokemon(self, trade_id: int, receiver_pokemon_id: int) -> bool:
        """Update trade with receiver's Pokemon selection and change status."""
        db = None
        try:
            db = dbconn()
            query = """
                UPDATE trade_requests
                SET receiver_pokemon_id = %s,
                    status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE trade_id = %s
                AND status = %s
            """
            db.execute(query, [
                receiver_pokemon_id,
                self.STATUS_PENDING_SENDER,
                trade_id,
                self.STATUS_PENDING_RECEIVER
            ])
            
            self.statuscode = 0
            self.message = 'Receiver pokemon updated'
            return True
            
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error updating receiver pokemon: {str(e)}'
            return False
        finally:
            if db:
                del db
    
    def complete_trade(self, trade_id: int) -> bool:
        """Mark trade as completed."""
        db = None
        try:
            db = dbconn()
            query = """
                UPDATE trade_requests
                SET status = %s,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE trade_id = %s
                AND status = %s
            """
            db.execute(query, [
                self.STATUS_COMPLETED,
                trade_id,
                self.STATUS_PENDING_SENDER
            ])
            
            self.statuscode = 0
            self.message = 'Trade completed'
            return True
            
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error completing trade: {str(e)}'
            return False
        finally:
            if db:
                del db
    
    def cancel_trade(self, trade_id: int, cancelled_by_discord_id: str) -> bool:
        """Cancel a trade request."""
        db = None
        try:
            db = dbconn()
            
            # First get the trade to determine who cancelled
            trade = self.get_trade_by_id(trade_id)
            if not trade:
                self.statuscode = 1
                self.message = 'Trade not found'
                return False
            
            # Determine cancellation status
            if cancelled_by_discord_id == trade['sender_discord_id']:
                new_status = self.STATUS_CANCELLED_SENDER
            else:
                new_status = self.STATUS_CANCELLED_RECEIVER
            
            query = """
                UPDATE trade_requests
                SET status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE trade_id = %s
                AND status IN (%s, %s)
            """
            db.execute(query, [
                new_status,
                trade_id,
                self.STATUS_PENDING_RECEIVER,
                self.STATUS_PENDING_SENDER
            ])
            
            self.statuscode = 0
            self.message = 'Trade cancelled'
            return True
            
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error cancelling trade: {str(e)}'
            return False
        finally:
            if db:
                del db
    
    def invalidate_trade(self, trade_id: int) -> bool:
        """Mark trade as invalid (Pokemon no longer exists or ownership changed)."""
        db = None
        try:
            db = dbconn()
            query = """
                UPDATE trade_requests
                SET status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE trade_id = %s
            """
            db.execute(query, [self.STATUS_INVALID, trade_id])
            
            self.statuscode = 0
            self.message = 'Trade invalidated'
            return True
            
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error invalidating trade: {str(e)}'
            return False
        finally:
            if db:
                del db
    
    def get_trade_history(self, discord_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get completed trade history for a user."""
        db = None
        try:
            db = dbconn()
            query = """
                SELECT * FROM trade_history
                WHERE sender_discord_id = %s OR receiver_discord_id = %s
                ORDER BY completed_at DESC
                LIMIT %s
            """
            results = db.queryAll(query, [discord_id, discord_id, limit])
            
            return results if results else []
            
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error fetching trade history: {str(e)}'
            return []
        finally:
            if db:
                del db
    
    def update_notification_message_id(self, trade_id: int, message_id: str) -> bool:
        """Store the DM message ID for later editing."""
        db = None
        try:
            db = dbconn()
            query = """
                UPDATE trade_requests
                SET notification_message_id = %s
                WHERE trade_id = %s
            """
            db.execute(query, [message_id, trade_id])
            
            return True
            
        except Exception as e:
            self.statuscode = 1
            self.message = f'Error updating notification message ID: {str(e)}'
            return False
        finally:
            if db:
                del db
    
    def validate_trade_execution(self, trade_id: int) -> tuple[bool, Optional[str]]:
        """
        Validate that a trade can be executed.
        Returns (is_valid, error_message)
        """
        trade = self.get_trade_by_id(trade_id)
        if not trade:
            return False, "Trade not found"
        
        if not trade['receiver_pokemon_id']:
            return False, "Receiver has not selected a Pokemon"
        
        # Check both Pokemon still exist and ownership hasn't changed
        db = None
        try:
            db = dbconn()
            
            # Validate sender's Pokemon
            query = "SELECT id, discord_id FROM pokemon WHERE id = %s"
            sender_poke = db.querySingle(query, [trade['sender_pokemon_id']])
            if not sender_poke:
                return False, "Sender's Pokemon no longer exists"
            if sender_poke['discord_id'] != trade['sender_discord_id']:
                return False, "Sender no longer owns their Pokemon"
            
            # Validate receiver's Pokemon
            receiver_poke = db.querySingle(query, [trade['receiver_pokemon_id']])
            if not receiver_poke:
                return False, "Receiver's Pokemon no longer exists"
            if receiver_poke['discord_id'] != trade['receiver_discord_id']:
                return False, "Receiver no longer owns their Pokemon"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
        finally:
            if db:
                del db