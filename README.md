# Neighborhood Ingredient Exchanger Telegram Bot

A Telegram bot that connects neighbors to share leftover ingredients, reduce food waste, and discover collaborative cooking opportunities.

## Features

- User registration with location sharing for proximity-based matching
- Ingredient management (add, remove, list)
- Offering and requesting ingredients from neighbors
- Location-based matching within 5km radius
- Recipe suggestions based on combined pantries
- Ingredient swap calculations to reduce food waste
- Privacy-protecting chat system
- Integration with Spoonacular API for recipe data

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   cp .env.example .env
   ```
4. Edit the `.env` file with your:
   - Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather))
   - Spoonacular API Key (get it from [spoonacular.com](https://spoonacular.com/food-api))
   - MongoDB connection details (optional, defaults to local MongoDB)

5. Start the bot:
   ```
   python main.py
   ```

## Bot Commands

- `/start` - Start the bot and get welcome message
- `/help` - Show help information
- `/register` - Create a user profile
- `/profile` - View your profile
- `/setlocation` - Update your location
- `/add <ingredient> <amount> <unit>` - Add ingredient to your pantry
- `/remove <ingredient>` - Remove ingredient from your pantry
- `/list` - List all your ingredients
- `/offer <ingredient>` - Offer an ingredient to neighbors
- `/request <ingredient>` - Request an ingredient from neighbors
- `/matches` - See potential matches nearby
- `/search <ingredient>` - Search for a specific ingredient nearby

## Project Structure

```
├── bot/
│   └── handlers.py     # Telegram bot command handlers
├── models/
│   ├── user.py         # User model
│   └── ingredient.py   # Ingredient model
├── services/
│   ├── matching.py     # User and ingredient matching logic
│   └── recipe_service.py  # Recipe API integration
├── utils/
│   ├── distance.py     # Distance calculation utilities
│   └── recipe_helper.py   # Recipe helper functions
├── .env.example        # Example environment variables
├── config.py           # Configuration settings
├── main.py             # Bot entry point
├── README.md           # This file
└── requirements.txt    # Python dependencies
```

## Database Schema

The application uses MongoDB with the following collections:

1. **Users**
   - `_id`: Unique user ID
   - `telegram_id`: Telegram user ID
   - `name`: User's name
   - `location`: User's geographic location (latitude, longitude)
   - `created_at`: Account creation timestamp
   - `offers`: List of offered ingredients
   - `requests`: List of requested ingredients

2. **Ingredients**
   - `_id`: Unique ingredient ID
   - `user_id`: Owner's user ID
   - `name`: Ingredient name
   - `amount`: Quantity available
   - `unit`: Unit of measurement
   - `category`: Ingredient category
   - `created_at`: When the ingredient was added

3. **Chats**
   - `_id`: Unique chat ID
   - `user1_id`: First user's ID
   - `user2_id`: Second user's ID
   - `created_at`: Chat creation timestamp
   - `messages`: List of messages exchanged

## Privacy Considerations

- User locations are only used for proximity-based matching
- Exact addresses are never shared between users
- Communications happen through the bot's built-in chat system
- Users can delete their data at any time

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.