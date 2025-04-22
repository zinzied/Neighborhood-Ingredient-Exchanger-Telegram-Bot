from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the token from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("No TELEGRAM_TOKEN found in .env file")

# Spoonacular API Key for recipe suggestions
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Database settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "ingredient_exchanger")

# App settings
MAX_DISTANCE_KM = 5  # Maximum distance to match users (in kilometers)
MAX_INGREDIENTS_PER_USER = 30  # Maximum number of ingredients a user can have
MIN_INGREDIENTS_FOR_RECIPE = 4  # Minimum number of ingredients needed for recipe suggestion