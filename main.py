import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from bot.handlers import (
    start_command, help_command, register_command, add_ingredient_command,
    remove_ingredient_command, list_ingredients_command, search_command,
    offer_command, request_command, matches_command, set_location_command,
    button_handler, cancel_command, profile_command, text_handler
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    from config import TELEGRAM_TOKEN
    
    if not TELEGRAM_TOKEN:
        logger.error("No TELEGRAM_TOKEN provided in environment variables!")
        return

    # Create the Updater and pass it your bot's token
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Basic commands
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("profile", profile_command))
    
    # Registration conversation handler
    register_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_command)],
        states={
            "NAME": [MessageHandler(Filters.text & ~Filters.command, register_command)],
            "LOCATION": [MessageHandler(Filters.location, set_location_command)]
        },
        fallbacks=[CommandHandler("cancel", cancel_command)]
    )
    dp.add_handler(register_conv_handler)
    
    # Set location command
    dp.add_handler(CommandHandler("setlocation", set_location_command))
    
    # Ingredient management
    dp.add_handler(CommandHandler("add", add_ingredient_command))
    dp.add_handler(CommandHandler("remove", remove_ingredient_command))
    dp.add_handler(CommandHandler("list", list_ingredients_command))
    
    # Exchange functionality
    dp.add_handler(CommandHandler("offer", offer_command))
    dp.add_handler(CommandHandler("request", request_command))
    dp.add_handler(CommandHandler("matches", matches_command))
    dp.add_handler(CommandHandler("search", search_command))
    
    # Handle button callbacks
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    # Handle text messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))
    
    # Start the Bot
    updater.start_polling()
    logger.info("Bot started successfully!")
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()