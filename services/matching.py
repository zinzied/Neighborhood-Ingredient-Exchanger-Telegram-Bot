import logging
from models.user import User
from models.ingredient import Ingredient
from services.recipe_service import get_recipe_by_ingredients
from utils.distance import calculate_distance
from config import MAX_DISTANCE_KM

logger = logging.getLogger(__name__)

def find_nearby_users(user, ingredient=None, name=None):
    """
    Find nearby users who either:
    1. Have requested an ingredient that the user is offering
    2. Are offering an ingredient that the user has requested
    
    Parameters:
    - user: User object
    - ingredient: Ingredient object (optional)
    - name: String, ingredient name (optional)
    
    Returns:
    - List of dictionaries with user and distance
    """
    if not user.location:
        return []
    
    # Get all users with location
    collection = User.get_collection()
    if not collection:
        return []
    
    all_users = collection.find({
        '_id': {'$ne': user.id},
        'location': {'$exists': True}
    })
    
    matches = []
    
    for user_data in all_users:
        other_user = User(user_data)
        
        # Calculate distance
        distance = calculate_distance(
            user.location['latitude'], user.location['longitude'],
            other_user.location['latitude'], other_user.location['longitude']
        )
        
        # Skip if too far
        if distance > MAX_DISTANCE_KM:
            continue
        
        # Case 1: User is offering an ingredient, check if other user has requested it
        if ingredient:
            for request in other_user.requests:
                if request['ingredient'].lower() == ingredient.name.lower():
                    matches.append({
                        'user': other_user,
                        'distance': distance,
                        'ingredient': ingredient.name,
                        'match_type': 'offer'
                    })
                    break
        
        # Case 2: User is requesting an ingredient, check if other user is offering it
        elif name:
            other_user_ingredients = Ingredient.find_by_user_id(other_user.id)
            
            for ing in other_user_ingredients:
                if ing.name.lower() == name.lower():
                    # Check if it's being offered
                    for offer in other_user.offers:
                        if offer.get('ingredient_id') == ing.id:
                            matches.append({
                                'user': other_user,
                                'distance': distance,
                                'ingredient': name,
                                'match_type': 'request'
                            })
                            break
        
        # Case 3: General search for potential recipe matches
        else:
            matches.append({
                'user': other_user,
                'distance': distance
            })
    
    # Sort by distance
    matches.sort(key=lambda x: x['distance'])
    return matches

def find_matching_recipes(user, nearby_users):
    """
    Find recipes that can be made by combining the user's ingredients
    with those of nearby users.
    
    Parameters:
    - user: User object
    - nearby_users: List of nearby user matches
    
    Returns:
    - List of recipe matches
    """
    if not nearby_users:
        return []
    
    recipe_matches = []
    
    # Get user's ingredients
    user_ingredients = Ingredient.find_by_user_id(user.id)
    user_ingredient_names = [ing.name for ing in user_ingredients]
    
    # For each nearby user, check if their ingredients + user's ingredients make complete recipes
    for nearby in nearby_users:
        other_user = nearby['user']
        
        # Get other user's ingredients
        other_ingredients = Ingredient.find_by_user_id(other_user.id)
        other_ingredient_names = [ing.name for ing in other_ingredients]
        
        # Combine ingredients
        combined_ingredients = list(set(user_ingredient_names + other_ingredient_names))
        
        # Get recipes that can be made with combined ingredients
        recipes = get_recipe_by_ingredients(combined_ingredients)
        
        if recipes:
            for recipe in recipes:
                recipe_match = {
                    'user': other_user,
                    'recipe': recipe,
                    'distance': nearby['distance']
                }
                
                # Determine which ingredients are missing
                required_ingredients = recipe.get('missedIngredients', [])
                missing = []
                
                for ing in required_ingredients:
                    ing_name = ing.get('name', '').lower()
                    if ing_name not in user_ingredient_names and ing_name not in other_ingredient_names:
                        missing.append(ing_name)
                
                if missing:
                    recipe_match['missing_ingredients'] = missing
                
                recipe_matches.append(recipe_match)
    
    # Remove duplicates and sort by least missing ingredients
    unique_recipes = {}
    for match in recipe_matches:
        recipe_id = match['recipe'].get('id')
        missing_count = len(match.get('missing_ingredients', []))
        
        if recipe_id not in unique_recipes or missing_count < len(unique_recipes[recipe_id].get('missing_ingredients', [])):
            unique_recipes[recipe_id] = match
    
    result = list(unique_recipes.values())
    result.sort(key=lambda x: len(x.get('missing_ingredients', [])))
    
    return result