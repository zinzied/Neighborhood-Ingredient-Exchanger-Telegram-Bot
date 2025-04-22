import logging
from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class Ingredient:
    """Ingredient model for managing ingredient data."""
    
    def __init__(self, ingredient_data):
        """Initialize the ingredient object."""
        self.id = ingredient_data.get('_id')
        self.user_id = ingredient_data.get('user_id')
        self.name = ingredient_data.get('name')
        self.amount = ingredient_data.get('amount')
        self.unit = ingredient_data.get('unit')
        self.category = ingredient_data.get('category')
        self.created_at = ingredient_data.get('created_at')
    
    @classmethod
    def get_collection(cls):
        """Get the ingredients collection from MongoDB."""
        try:
            client = MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            return db.ingredients
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return None
    
    @classmethod
    def add(cls, user_id, name, amount, unit="", category=None):
        """Add a new ingredient to a user's pantry."""
        collection = cls.get_collection()
        if not collection:
            return None
        
        try:
            # Categorize the ingredient
            if not category:
                category = cls.categorize(name)
            
            ingredient_data = {
                '_id': str(uuid.uuid4()),
                'user_id': user_id,
                'name': name.lower(),
                'amount': amount,
                'unit': unit,
                'category': category,
                'created_at': datetime.now()
            }
            
            result = collection.insert_one(ingredient_data)
            if result.acknowledged:
                return cls(ingredient_data)
            return None
        except Exception as e:
            logger.error(f"Error adding ingredient: {e}")
            return None
    
    @classmethod
    def categorize(cls, name):
        """Categorize an ingredient based on its name."""
        name = name.lower()
        
        # Basic categorization
        if any(grain in name for grain in ['flour', 'rice', 'pasta', 'bread', 'oat', 'cereal']):
            return 'Grains'
        elif any(protein in name for protein in ['meat', 'chicken', 'beef', 'pork', 'fish', 'tofu']):
            return 'Proteins'
        elif any(dairy in name for dairy in ['milk', 'cheese', 'yogurt', 'cream', 'butter']):
            return 'Dairy'
        elif any(fruit in name for fruit in ['apple', 'orange', 'banana', 'berry', 'fruit']):
            return 'Fruits'
        elif any(vegetable in name for vegetable in ['carrot', 'tomato', 'potato', 'onion', 'vegetable']):
            return 'Vegetables'
        elif any(spice in name for spice in ['salt', 'pepper', 'spice', 'herb', 'seasoning']):
            return 'Spices & Herbs'
        elif any(sweet in name for sweet in ['sugar', 'honey', 'syrup', 'chocolate', 'candy']):
            return 'Sweeteners'
        elif any(oil in name for oil in ['oil', 'vinegar', 'sauce', 'dressing']):
            return 'Oils & Condiments'
        else:
            return 'Other'
    
    @classmethod
    def remove(cls, user_id, name):
        """Remove an ingredient from a user's pantry."""
        collection = cls.get_collection()
        if not collection:
            return False
        
        try:
            result = collection.delete_one({
                'user_id': user_id,
                'name': name.lower()
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error removing ingredient: {e}")
            return False
    
    @classmethod
    def find_by_id(cls, ingredient_id):
        """Find an ingredient by its ID."""
        collection = cls.get_collection()
        if not collection:
            return None
        
        try:
            ingredient_data = collection.find_one({'_id': ingredient_id})
            if ingredient_data:
                return cls(ingredient_data)
            return None
        except Exception as e:
            logger.error(f"Error finding ingredient: {e}")
            return None
    
    @classmethod
    def find_by_name_and_user(cls, user_id, name):
        """Find an ingredient by name and user ID."""
        collection = cls.get_collection()
        if not collection:
            return None
        
        try:
            ingredient_data = collection.find_one({
                'user_id': user_id,
                'name': name.lower()
            })
            if ingredient_data:
                return cls(ingredient_data)
            return None
        except Exception as e:
            logger.error(f"Error finding ingredient: {e}")
            return None
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """Find all ingredients belonging to a user."""
        collection = cls.get_collection()
        if not collection:
            return []
        
        try:
            ingredient_data = collection.find({'user_id': user_id})
            return [cls(data) for data in ingredient_data]
        except Exception as e:
            logger.error(f"Error finding ingredients: {e}")
            return []
    
    @classmethod
    def update(cls, ingredient_id, amount, unit):
        """Update an ingredient's amount and unit."""
        collection = cls.get_collection()
        if not collection:
            return False
        
        try:
            result = collection.update_one(
                {'_id': ingredient_id},
                {'$set': {'amount': amount, 'unit': unit}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating ingredient: {e}")
            return False