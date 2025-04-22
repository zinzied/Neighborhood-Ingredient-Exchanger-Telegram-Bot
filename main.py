import logging
import asyncio
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)
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

async def main():
    """Start the bot."""
    from config import TELEGRAM_TOKEN
    
    if not TELEGRAM_TOKEN:
        logger.error("No TELEGRAM_TOKEN provided in environment variables!")
        return

    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    # Basic commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    
    # Registration conversation handler
    register_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_command)],
        states={
            "NAME": [MessageHandler(filters.TEXT & ~filters.COMMAND, register_command)],
            "LOCATION": [MessageHandler(filters.LOCATION, set_location_command)]
        },
        fallbacks=[CommandHandler("cancel", cancel_command)]
    )
    application.add_handler(register_conv_handler)
    
    # Set location command
    application.add_handler(CommandHandler("setlocation", set_location_command))
    
    # Ingredient management
    application.add_handler(CommandHandler("add", add_ingredient_command))
    application.add_handler(CommandHandler("remove", remove_ingredient_command))
    application.add_handler(CommandHandler("list", list_ingredients_command))
    
    # Exchange functionality
    application.add_handler(CommandHandler("offer", offer_command))
    application.add_handler(CommandHandler("request", request_command))
    application.add_handler(CommandHandler("matches", matches_command))
    application.add_handler(CommandHandler("search", search_command))
    
    # Handle button callbacks
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Handle text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Run the bot
    logger.info("Starting bot...")
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)