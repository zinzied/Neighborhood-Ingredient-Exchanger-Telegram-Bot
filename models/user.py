import logging
from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class User:
    """User model for managing user data."""
    
    def __init__(self, user_data):
        """Initialize the user object."""
        self.id = user_data.get('_id')
        self.telegram_id = user_data.get('telegram_id')
        self.name = user_data.get('name')
        self.location = user_data.get('location')
        self.created_at = user_data.get('created_at')
        self.offers = user_data.get('offers', [])
        self.requests = user_data.get('requests', [])
    
    @classmethod
    def get_collection(cls):
        """Get the users collection from MongoDB."""
        try:
            client = MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            return db.users
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return None
    
    @classmethod
    def create(cls, telegram_id, name, location=None):
        """Create a new user."""
        collection = cls.get_collection()
        if collection is None:
            return None
        
        try:
            user_data = {
                '_id': str(uuid.uuid4()),
                'telegram_id': telegram_id,
                'name': name,
                'location': location,
                'created_at': datetime.now(),
                'offers': [],
                'requests': []
            }
            
            result = collection.insert_one(user_data)
            if result.acknowledged:
                return cls(user_data)
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    @classmethod
    def find_by_telegram_id(cls, telegram_id):
        """Find a user by their Telegram ID."""
        collection = cls.get_collection()
        if collection is None:
            return None
        
        try:
            user_data = collection.find_one({'telegram_id': telegram_id})
            if user_data:
                return cls(user_data)
            return None
        except Exception as e:
            logger.error(f"Error finding user: {e}")
            return None
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find a user by their internal ID."""
        collection = cls.get_collection()
        if collection is None:
            return None
        
        try:
            user_data = collection.find_one({'_id': user_id})
            if user_data:
                return cls(user_data)
            return None
        except Exception as e:
            logger.error(f"Error finding user: {e}")
            return None
    
    @classmethod
    def update_location(cls, user_id, location):
        """Update a user's location."""
        collection = cls.get_collection()
        if collection is None:
            return False
        
        try:
            result = collection.update_one(
                {'_id': user_id},
                {'$set': {'location': location}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating location: {e}")
            return False
    
    @classmethod
    def add_offer(cls, user_id, ingredient_id):
        """Add an ingredient offer."""
        collection = cls.get_collection()
        if collection is None:
            return False
        
        try:
            offer = {
                'ingredient_id': ingredient_id,
                'created_at': datetime.now()
            }
            
            result = collection.update_one(
                {'_id': user_id},
                {'$push': {'offers': offer}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding offer: {e}")
            return False
    
    @classmethod
    def add_request(cls, user_id, ingredient_name, amount="", unit=""):
        """Add an ingredient request."""
        collection = cls.get_collection()
        if collection is None:
            return False
        
        try:
            request = {
                'ingredient': ingredient_name,
                'amount': amount,
                'unit': unit,
                'created_at': datetime.now()
            }
            
            result = collection.update_one(
                {'_id': user_id},
                {'$push': {'requests': request}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding request: {e}")
            return False
    
    @classmethod
    def remove_offer(cls, user_id, offer_index):
        """Remove an ingredient offer."""
        collection = cls.get_collection()
        if collection is None:
            return False
        
        try:
            user = cls.find_by_id(user_id)
            if not user or offer_index >= len(user.offers):
                return False
            
            offers = user.offers
            offers.pop(offer_index)
            
            result = collection.update_one(
                {'_id': user_id},
                {'$set': {'offers': offers}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error removing offer: {e}")
            return False
    
    @classmethod
    def remove_request(cls, user_id, request_index):
        """Remove an ingredient request."""
        collection = cls.get_collection()
        if collection is None:
            return False
        
        try:
            user = cls.find_by_id(user_id)
            if not user or request_index >= len(user.requests):
                return False
            
            requests = user.requests
            requests.pop(request_index)
            
            result = collection.update_one(
                {'_id': user_id},
                {'$set': {'requests': requests}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error removing request: {e}")
            return False
    
    @classmethod
    def find_nearby_users(cls, location, max_distance_km=5):
        """Find users within a specified distance."""
        collection = cls.get_collection()
        if collection is None:
            return []
        
        # MongoDB doesn't support geospatial queries in this version
        # So we'll do a simplified version by getting all users and filtering in Python
        try:
            all_users = collection.find({'location': {'$exists': True}})
            nearby_users = []
            
            for user_data in all_users:
                user = cls(user_data)
                # Calculate distance between locations using a utility function
                from utils.distance import calculate_distance
                distance = calculate_distance(
                    location['latitude'], location['longitude'],
                    user.location['latitude'], user.location['longitude']
                )
                
                if distance <= max_distance_km:
                    nearby_users.append({
                        'user': user,
                        'distance': distance
                    })
            
            # Sort by distance
            nearby_users.sort(key=lambda x: x['distance'])
            return nearby_users
        except Exception as e:
            logger.error(f"Error finding nearby users: {e}")
            return []
    
    @classmethod
    def create_chat(cls, user1_id, user2_id):
        """Create a chat between two users."""
        try:
            client = MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            chats_collection = db.chats
            
            # Check if chat already exists
            existing_chat = chats_collection.find_one({
                '$or': [
                    {'user1_id': user1_id, 'user2_id': user2_id},
                    {'user1_id': user2_id, 'user2_id': user1_id}
                ]
            })
            
            if existing_chat:
                return existing_chat['_id']
            
            # Create new chat
            chat_data = {
                '_id': str(uuid.uuid4()),
                'user1_id': user1_id,
                'user2_id': user2_id,
                'created_at': datetime.now(),
                'messages': []
            }
            
            result = chats_collection.insert_one(chat_data)
            if result.acknowledged:
                return chat_data['_id']
            return None
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            return None
    
    @classmethod
    def get_chat(cls, chat_id):
        """Get a chat by ID."""
        try:
            client = MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            chats_collection = db.chats
            
            chat = chats_collection.find_one({'_id': chat_id})
            return chat
        except Exception as e:
            logger.error(f"Error getting chat: {e}")
            return None
    
    @classmethod
    def add_message_to_chat(cls, chat_id, user_id, message):
        """Add a message to a chat."""
        try:
            client = MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            chats_collection = db.chats
            
            message_data = {
                'user_id': user_id,
                'content': message,
                'created_at': datetime.now()
            }
            
            result = chats_collection.update_one(
                {'_id': chat_id},
                {'$push': {'messages': message_data}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False
