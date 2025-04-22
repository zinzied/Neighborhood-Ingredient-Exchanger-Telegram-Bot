import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext, ConversationHandler
from models.user import User
from models.ingredient import Ingredient
from services.matching import find_nearby_users, find_matching_recipes
from services.recipe_service import get_recipe_by_ingredients

logger = logging.getLogger(__name__)

# Conversation states
NAME, LOCATION = range(2)

def start_command(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    
    welcome_message = (
        f"👋 Hi {user.first_name}! Welcome to the Neighborhood Ingredient Exchanger Bot!\n\n"
        "I help you share leftover ingredients with neighbors and reduce food waste.\n\n"
        "🔍 Here's what I can do:\n"
        "• Share ingredients you no longer need\n"
        "• Find ingredients you're looking for\n"
        "• Get recipe ideas from your combined pantries\n"
        "• Connect with neighbors to exchange ingredients\n\n"
        "To get started, please register with /register"
    )
    
    keyboard = [
        [KeyboardButton("📝 Register", callback_data="register")],
        [KeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message when the command /help is issued."""
    help_text = (
        "🌿 *Neighborhood Ingredient Exchanger* 🌿\n\n"
        "*Basic Commands:*\n"
        "/register - Create your profile\n"
        "/profile - View your profile\n"
        "/setlocation - Update your location\n\n"
        
        "*Ingredient Management:*\n"
        "/add <ingredient name> <amount> <unit> - Add ingredient to your pantry\n"
        "/remove <ingredient name> - Remove ingredient from your pantry\n"
        "/list - List all your ingredients\n\n"
        
        "*Exchange Functions:*\n"
        "/offer <ingredient> - Offer an ingredient to share\n"
        "/request <ingredient> - Request an ingredient you need\n"
        "/matches - See potential ingredient matches nearby\n"
        "/search <ingredient> - Search for specific ingredient offers nearby\n\n"
        
        "For any other questions, just type your question and I'll try to help!"
    )
    update.message.reply_text(help_text, parse_mode="Markdown")

def register_command(update: Update, context: CallbackContext) -> int:
    """Start the registration process."""
    user = update.effective_user
    
    # Check if user is already registered
    existing_user = User.find_by_telegram_id(user.id)
    if existing_user:
        update.message.reply_text(
            f"You're already registered as {existing_user.name}!\n"
            "You can update your profile with /profile"
        )
        return ConversationHandler.END
    
    update.message.reply_text(
        "Let's get you registered! What's your first name or nickname?"
    )
    return NAME

def profile_command(update: Update, context: CallbackContext) -> None:
    """Show user profile and settings."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You're not registered yet! Use /register to create your profile."
        )
        return
    
    # Get user's ingredients
    ingredients = Ingredient.find_by_user_id(user_data.id)
    ingredient_list = "\n".join([f"• {ing.name} ({ing.amount} {ing.unit})" for ing in ingredients]) if ingredients else "No ingredients added yet"
    
    profile_text = (
        f"📋 *Your Profile*\n\n"
        f"Name: {user_data.name}\n"
        f"Location: {'Set' if user_data.location else 'Not set'}\n"
        f"Total Ingredients: {len(ingredients)}\n"
        f"Active Offers: {len(user_data.offers)}\n"
        f"Active Requests: {len(user_data.requests)}\n\n"
        f"*Your Ingredients:*\n{ingredient_list}"
    )
    
    keyboard = [
        [InlineKeyboardButton("Update Location", callback_data="update_location")],
        [InlineKeyboardButton("Add Ingredients", callback_data="add_ingredients")],
        [InlineKeyboardButton("Manage Offers", callback_data="manage_offers")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode="Markdown")

def set_location_command(update: Update, context: CallbackContext) -> int:
    """Set or update user location."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You need to register first! Use /register to create your profile."
        )
        return ConversationHandler.END
    
    if update.message.location:
        # User sent their location
        location = {
            "latitude": update.message.location.latitude,
            "longitude": update.message.location.longitude
        }
        
        User.update_location(user_data.id, location)
        update.message.reply_text(
            "Your location has been updated successfully! Now you can start sharing ingredients with neighbors."
        )
        return ConversationHandler.END
    else:
        # Ask for location
        location_button = KeyboardButton("Share Location", request_location=True)
        keyboard = [[location_button], [KeyboardButton("Cancel")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        update.message.reply_text(
            "Please share your location so I can find neighbors near you.",
            reply_markup=reply_markup
        )
        return LOCATION

def add_ingredient_command(update: Update, context: CallbackContext) -> None:
    """Add an ingredient to user's pantry."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You need to register first! Use /register to create your profile."
        )
        return
    
    args = context.args
    if len(args) < 2:
        update.message.reply_text(
            "Please provide ingredient name and amount.\n"
            "Example: /add flour 500 g"
        )
        return
    
    name = args[0].lower()
    amount = args[1]
    unit = args[2] if len(args) > 2 else ""
    
    result = Ingredient.add(user_data.id, name, amount, unit)
    if result:
        update.message.reply_text(
            f"✅ Added {amount} {unit} of {name} to your pantry!"
        )
    else:
        update.message.reply_text(
            "Failed to add ingredient. Please try again."
        )

def remove_ingredient_command(update: Update, context: CallbackContext) -> None:
    """Remove an ingredient from user's pantry."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You need to register first! Use /register to create your profile."
        )
        return
    
    args = context.args
    if not args:
        update.message.reply_text(
            "Please provide the ingredient name to remove.\n"
            "Example: /remove flour"
        )
        return
    
    name = args[0].lower()
    result = Ingredient.remove(user_data.id, name)
    
    if result:
        update.message.reply_text(
            f"✅ Removed {name} from your pantry!"
        )
    else:
        update.message.reply_text(
            f"Could not find {name} in your pantry. Use /list to see your ingredients."
        )

def list_ingredients_command(update: Update, context: CallbackContext) -> None:
    """List all ingredients in user's pantry."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You need to register first! Use /register to create your profile."
        )
        return
    
    ingredients = Ingredient.find_by_user_id(user_data.id)
    
    if not ingredients:
        update.message.reply_text(
            "Your pantry is empty! Add ingredients with /add command."
        )
        return
    
    # Group ingredients by category
    categories = {}
    for ing in ingredients:
        cat = ing.category or "Other"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ing)
    
    # Build the message
    message = "🍽️ *Your Pantry* 🍽️\n\n"
    
    for category, items in categories.items():
        message += f"*{category}*:\n"
        for ing in items:
            message += f"• {ing.name} ({ing.amount} {ing.unit})\n"
        message += "\n"
    
    message += "Use /add to add more ingredients or /remove to remove some."
    
    update.message.reply_text(message, parse_mode="Markdown")

def offer_command(update: Update, context: CallbackContext) -> None:
    """Offer an ingredient to share with neighbors."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You need to register first! Use /register to create your profile."
        )
        return
    
    if not user_data.location:
        update.message.reply_text(
            "You need to set your location first! Use /setlocation to continue."
        )
        return
    
    args = context.args
    if not args:
        # Show list of user's ingredients as buttons
        ingredients = Ingredient.find_by_user_id(user_data.id)
        
        if not ingredients:
            update.message.reply_text(
                "Your pantry is empty! Add ingredients with /add command first."
            )
            return
        
        keyboard = []
        for ing in ingredients:
            keyboard.append([InlineKeyboardButton(f"{ing.name} ({ing.amount} {ing.unit})", callback_data=f"offer_{ing.id}")])
        
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "Select an ingredient to offer to your neighbors:",
            reply_markup=reply_markup
        )
        return
    
    # User specified ingredient in command
    name = args[0].lower()
    ingredient = Ingredient.find_by_name_and_user(user_data.id, name)
    
    if not ingredient:
        update.message.reply_text(
            f"Could not find {name} in your pantry. Use /list to see your ingredients."
        )
        return
    
    # Create offer
    result = User.add_offer(user_data.id, ingredient.id)
    
    if result:
        update.message.reply_text(
            f"✅ You're now offering {name} to your neighbors!\n"
            f"I'll notify you when someone nearby is interested."
        )
        
        # Find matching requests in the area
        matches = find_nearby_users(user_data, ingredient)
        
        if matches:
            update.message.reply_text(
                f"📣 Good news! {len(matches)} neighbors are looking for {name}!\n"
                f"Use /matches to see potential matches."
            )
    else:
        update.message.reply_text(
            "Failed to create offer. Please try again."
        )

def request_command(update: Update, context: CallbackContext) -> None:
    """Request an ingredient from neighbors."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You need to register first! Use /register to create your profile."
        )
        return
    
    if not user_data.location:
        update.message.reply_text(
            "You need to set your location first! Use /setlocation to continue."
        )
        return
    
    args = context.args
    if not args:
        update.message.reply_text(
            "Please specify what ingredient you need.\n"
            "Example: /request sugar"
        )
        return
    
    name = args[0].lower()
    amount = args[1] if len(args) > 1 else ""
    unit = args[2] if len(args) > 2 else ""
    
    # Create request
    result = User.add_request(user_data.id, name, amount, unit)
    
    if result:
        update.message.reply_text(
            f"✅ You're now requesting {amount} {unit} {name} from neighbors!\n"
            f"I'll notify you when someone nearby can help."
        )
        
        # Find matching offers in the area
        matches = find_nearby_users(user_data, name=name)
        
        if matches:
            update.message.reply_text(
                f"📣 Good news! {len(matches)} neighbors are offering {name}!\n"
                f"Use /matches to see potential matches."
            )
            
            # Check if we can suggest recipes
            recipe_matches = find_matching_recipes(user_data, matches)
            if recipe_matches:
                update.message.reply_text(
                    f"🍳 I found {len(recipe_matches)} recipes you could make by combining pantries with neighbors!\n"
                    f"Use /matches to see recipe suggestions."
                )
    else:
        update.message.reply_text(
            "Failed to create request. Please try again."
        )

def matches_command(update: Update, context: CallbackContext) -> None:
    """Show potential matches for user's offers and requests."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You need to register first! Use /register to create your profile."
        )
        return
    
    if not user_data.location:
        update.message.reply_text(
            "You need to set your location first! Use /setlocation to continue."
        )
        return
    
    # Get matches for user's offers
    offer_matches = []
    for offer in user_data.offers:
        ing = Ingredient.find_by_id(offer['ingredient_id'])
        if ing:
            nearby_matches = find_nearby_users(user_data, ing)
            offer_matches.extend(nearby_matches)
    
    # Get matches for user's requests
    request_matches = []
    for request in user_data.requests:
        nearby_matches = find_nearby_users(user_data, name=request['ingredient'])
        request_matches.extend(nearby_matches)
    
    # Get recipe suggestions
    recipe_matches = []
    all_matches = offer_matches + request_matches
    if all_matches:
        recipe_matches = find_matching_recipes(user_data, all_matches)
    
    if not (offer_matches or request_matches):
        update.message.reply_text(
            "No matches found nearby yet. Try offering or requesting more ingredients!"
        )
        return
    
    # Build the message
    message = "🔍 *Your Matches* 🔍\n\n"
    
    if offer_matches:
        message += "*People who need your ingredients:*\n"
        for match in offer_matches[:5]:  # Limit to 5 matches
            distance = match['distance']
            user_name = match['user'].name
            ing_name = match['ingredient']
            message += f"• {user_name} (within {distance:.1f}km) needs {ing_name}\n"
        
        if len(offer_matches) > 5:
            message += f"...and {len(offer_matches) - 5} more\n"
        message += "\n"
    
    if request_matches:
        message += "*People who have ingredients you need:*\n"
        for match in request_matches[:5]:  # Limit to 5 matches
            distance = match['distance']
            user_name = match['user'].name
            ing_name = match['ingredient']
            message += f"• {user_name} (within {distance:.1f}km) has {ing_name}\n"
        
        if len(request_matches) > 5:
            message += f"...and {len(request_matches) - 5} more\n"
        message += "\n"
    
    if recipe_matches:
        message += "*Recipe Suggestions:*\n"
        for match in recipe_matches[:3]:  # Limit to 3 recipe suggestions
            recipe = match['recipe']
            user_name = match['user'].name
            message += f"• You and {user_name} could make {recipe['title']}\n"
        
        if len(recipe_matches) > 3:
            message += f"...and {len(recipe_matches) - 3} more recipe ideas\n"
    
    # Add contact buttons
    keyboard = []
    
    all_user_matches = set()
    for match in offer_matches + request_matches:
        all_user_matches.add(match['user'].id)
    
    for user_id in list(all_user_matches)[:5]:  # Limit to 5 users
        user_obj = User.find_by_id(user_id)
        if user_obj:
            keyboard.append([InlineKeyboardButton(f"Contact {user_obj.name}", callback_data=f"contact_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("See Recipe Details", callback_data="recipe_details")])
    keyboard.append([InlineKeyboardButton("Close", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

def search_command(update: Update, context: CallbackContext) -> None:
    """Search for specific ingredients offered by neighbors."""
    user = update.effective_user
    user_data = User.find_by_telegram_id(user.id)
    
    if not user_data:
        update.message.reply_text(
            "You need to register first! Use /register to create your profile."
        )
        return
    
    if not user_data.location:
        update.message.reply_text(
            "You need to set your location first! Use /setlocation to continue."
        )
        return
    
    args = context.args
    if not args:
        update.message.reply_text(
            "Please specify what ingredient you're looking for.\n"
            "Example: /search sugar"
        )
        return
    
    ingredient_name = args[0].lower()
    
    # Find users offering this ingredient
    matches = find_nearby_users(user_data, name=ingredient_name)
    
    if not matches:
        update.message.reply_text(
            f"No neighbors offering {ingredient_name} found nearby.\n"
            f"Try /request {ingredient_name} to let others know you need it!"
        )
        return
    
    # Build the message
    message = f"🔍 *Search Results for {ingredient_name}* 🔍\n\n"
    message += f"Found {len(matches)} neighbors offering {ingredient_name}:\n\n"
    
    for match in matches[:8]:  # Limit to 8 matches
        distance = match['distance']
        user_name = match['user'].name
        message += f"• {user_name} (within {distance:.1f}km)\n"
    
    if len(matches) > 8:
        message += f"...and {len(matches) - 8} more\n"
    
    # Add contact buttons
    keyboard = []
    for match in matches[:5]:  # Limit to 5 users
        user_obj = match['user']
        keyboard.append([InlineKeyboardButton(f"Contact {user_obj.name}", callback_data=f"contact_{user_obj.id}")])
    
    keyboard.append([InlineKeyboardButton("Request This Ingredient", callback_data=f"request_{ingredient_name}")])
    keyboard.append([InlineKeyboardButton("Close", callback_data="cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == "cancel":
        query.edit_message_text("Action cancelled.")
        return
    
    if data.startswith("offer_"):
        # Handle offer selection
        ingredient_id = data.split("_")[1]
        user = update.effective_user
        user_data = User.find_by_telegram_id(user.id)
        
        if user_data:
            ingredient = Ingredient.find_by_id(ingredient_id)
            if ingredient:
                result = User.add_offer(user_data.id, ingredient_id)
                if result:
                    query.edit_message_text(
                        f"✅ You're now offering {ingredient.name} to your neighbors!\n"
                        f"I'll notify you when someone nearby is interested."
                    )
                    
                    # Find matching requests in the area
                    matches = find_nearby_users(user_data, ingredient)
                    
                    if matches:
                        context.bot.send_message(
                            chat_id=user.id,
                            text=f"📣 Good news! {len(matches)} neighbors are looking for {ingredient.name}!\n"
                                f"Use /matches to see potential matches."
                        )
                else:
                    query.edit_message_text("Failed to create offer. Please try again.")
            else:
                query.edit_message_text("Ingredient not found. Please try again.")
    
    elif data.startswith("contact_"):
        # Handle contact request
        target_user_id = data.split("_")[1]
        user = update.effective_user
        user_data = User.find_by_telegram_id(user.id)
        target_user = User.find_by_id(target_user_id)
        
        if user_data and target_user:
            # Create chat or get existing one
            chat_id = User.create_chat(user_data.id, target_user_id)
            
            if chat_id:
                query.edit_message_text(
                    f"I've set up a chat with {target_user.name}.\n"
                    f"You can now discuss ingredient exchange details privately."
                )
                
                # Send a message to both users
                context.bot.send_message(
                    chat_id=user.id,
                    text=f"🤝 You're now connected with {target_user.name} for ingredient exchange.\n"
                        f"Use /chat_{chat_id} to send messages."
                )
                
                context.bot.send_message(
                    chat_id=target_user.telegram_id,
                    text=f"🤝 {user_data.name} wants to exchange ingredients with you!\n"
                        f"Use /chat_{chat_id} to respond."
                )
            else:
                query.edit_message_text("Failed to create chat. Please try again later.")
    
    elif data.startswith("request_"):
        # Handle request creation from search
        ingredient_name = data.split("_")[1]
        user = update.effective_user
        user_data = User.find_by_telegram_id(user.id)
        
        if user_data:
            result = User.add_request(user_data.id, ingredient_name)
            
            if result:
                query.edit_message_text(
                    f"✅ You're now requesting {ingredient_name} from neighbors!\n"
                    f"I'll notify you when someone nearby can help."
                )
                
                # Find matching offers in the area
                matches = find_nearby_users(user_data, name=ingredient_name)
                
                if matches:
                    context.bot.send_message(
                        chat_id=user.id,
                        text=f"📣 Good news! {len(matches)} neighbors are offering {ingredient_name}!\n"
                            f"Use /matches to see potential matches."
                    )
            else:
                query.edit_message_text("Failed to create request. Please try again.")
    
    elif data == "recipe_details":
        # Show recipe details
        user = update.effective_user
        user_data = User.find_by_telegram_id(user.id)
        
        if user_data:
            all_matches = []
            
            # Get matches for user's offers
            for offer in user_data.offers:
                ing = Ingredient.find_by_id(offer['ingredient_id'])
                if ing:
                    nearby_matches = find_nearby_users(user_data, ing)
                    all_matches.extend(nearby_matches)
            
            # Get matches for user's requests
            for request in user_data.requests:
                nearby_matches = find_nearby_users(user_data, name=request['ingredient'])
                all_matches.extend(nearby_matches)
            
            # Get recipe suggestions
            recipe_matches = find_matching_recipes(user_data, all_matches)
            
            if recipe_matches:
                # Build the message
                message = "🍳 *Recipe Suggestions* 🍳\n\n"
                
                for i, match in enumerate(recipe_matches[:5]):  # Limit to 5 recipes
                    recipe = match['recipe']
                    user_name = match['user'].name
                    missing_ingredients = match.get('missing_ingredients', [])
                    
                    message += f"*{i+1}. {recipe['title']}*\n"
                    message += f"Cook with: {user_name}\n"
                    message += f"Cook time: {recipe.get('readyInMinutes', 'N/A')} minutes\n"
                    message += f"Servings: {recipe.get('servings', 'N/A')}\n"
                    
                    if missing_ingredients:
                        message += f"Still needed: {', '.join(missing_ingredients)}\n"
                    
                    message += "\n"
                
                # Add action buttons
                keyboard = []
                for i, match in enumerate(recipe_matches[:3]):
                    recipe = match['recipe']
                    keyboard.append([InlineKeyboardButton(f"View Recipe #{i+1}", url=recipe.get('sourceUrl', ''))])
                
                keyboard.append([InlineKeyboardButton("Contact Cooks", callback_data="contact_cooks")])
                keyboard.append([InlineKeyboardButton("Back", callback_data="matches")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                query.edit_message_text("No recipe suggestions found. Try adding more ingredients or connecting with more neighbors!")
    
    elif data == "matches":
        # Go back to matches view
        context.user_data['command'] = "matches"
        matches_command(update, context)
    
    elif data == "contact_cooks":
        # Show a list of potential cooking partners
        user = update.effective_user
        user_data = User.find_by_telegram_id(user.id)
        
        if user_data:
            all_matches = []
            
            # Get all possible matches
            for offer in user_data.offers:
                ing = Ingredient.find_by_id(offer['ingredient_id'])
                if ing:
                    nearby_matches = find_nearby_users(user_data, ing)
                    all_matches.extend(nearby_matches)
            
            for request in user_data.requests:
                nearby_matches = find_nearby_users(user_data, name=request['ingredient'])
                all_matches.extend(nearby_matches)
            
            # Get unique users
            unique_users = {}
            for match in all_matches:
                if match['user'].id not in unique_users:
                    unique_users[match['user'].id] = match['user']
            
            if unique_users:
                # Build the message
                message = "👨‍🍳 *Potential Cooking Partners* 👩‍🍳\n\n"
                message += "Select a neighbor to contact for cooking together:\n\n"
                
                # Add contact buttons
                keyboard = []
                for user_id, user_obj in unique_users.items():
                    keyboard.append([InlineKeyboardButton(f"Contact {user_obj.name}", callback_data=f"contact_{user_id}")])
                
                keyboard.append([InlineKeyboardButton("Back", callback_data="recipe_details")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                query.edit_message_text("No potential cooking partners found nearby.")

def cancel_command(update: Update, context: CallbackContext) -> int:
    """Cancel current conversation."""
    update.message.reply_text(
        "Action cancelled. What would you like to do next?"
    )
    return ConversationHandler.END

def text_handler(update: Update, context: CallbackContext) -> None:
    """Handle regular text messages."""
    text = update.message.text.lower()
    
    # Check if this is a chat message
    if text.startswith("/chat_"):
        # Handle chat message
        parts = text.split(" ", 1)
        if len(parts) < 2:
            update.message.reply_text("Please include a message after the chat command.")
            return
        
        chat_id = parts[0].replace("/chat_", "")
        message = parts[1]
        
        # Forward the message to the other user in the chat
        user = update.effective_user
        user_data = User.find_by_telegram_id(user.id)
        
        if user_data:
            # Get the chat
            chat = User.get_chat(chat_id)
            
            if chat and (user_data.id == chat['user1_id'] or user_data.id == chat['user2_id']):
                # Get the other user
                other_user_id = chat['user1_id'] if user_data.id == chat['user2_id'] else chat['user2_id']
                other_user = User.find_by_id(other_user_id)
                
                if other_user:
                    # Send the message
                    context.bot.send_message(
                        chat_id=other_user.telegram_id,
                        text=f"💬 {user_data.name}: {message}\n\nReply with /chat_{chat_id} [your message]"
                    )
                    
                    update.message.reply_text("Message sent!")
                else:
                    update.message.reply_text("User not found.")
            else:
                update.message.reply_text("Chat not found or you don't have access to it.")
        return
    
    # Handle common keywords
    if "help" in text or "how" in text:
        help_command(update, context)
    elif "register" in text:
        register_command(update, context)
    elif "add" in text and "ingredient" in text:
        update.message.reply_text(
            "To add an ingredient, use the /add command followed by the ingredient name, amount, and unit.\n"
            "Example: /add sugar 500 g"
        )
    elif "recipe" in text or "cook" in text:
        update.message.reply_text(
            "Looking for recipe ideas? Use /matches to see potential recipe matches with neighbors.\n"
            "Or you can add more ingredients to your pantry with /add to get better suggestions!"
        )
    elif "location" in text:
        set_location_command(update, context)
    elif "offer" in text or "share" in text:
        update.message.reply_text(
            "To offer an ingredient to neighbors, use the /offer command followed by the ingredient name.\n"
            "Example: /offer flour\n"
            "Or just type /offer to see a list of your ingredients."
        )
    elif "need" in text or "request" in text or "looking for" in text:
        update.message.reply_text(
            "To request an ingredient from neighbors, use the /request command followed by the ingredient name.\n"
            "Example: /request sugar"
        )
    else:
        # Generic response for unrecognized messages
        update.message.reply_text(
            "I'm not sure how to respond to that. Type /help to see available commands.\n"
            "You can try:\n"
            "• /register - Create your profile\n"
            "• /add - Add ingredients to your pantry\n"
            "• /offer - Share ingredients with neighbors\n"
            "• /request - Ask for ingredients you need\n"
            "• /matches - See ingredient matches nearby"
        )