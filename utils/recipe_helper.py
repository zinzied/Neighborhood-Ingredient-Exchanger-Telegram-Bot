import logging
from services.recipe_service import get_recipe_by_ingredients, get_recipe_swap_suggestions

logger = logging.getLogger(__name__)

def suggest_recipe_with_swaps(user_ingredients, other_user_ingredients):
    """
    Suggest recipes that can be made with ingredient swaps between users.
    
    Parameters:
    - user_ingredients: List of user's ingredient names
    - other_user_ingredients: List of other user's ingredient names
    
    Returns:
    - List of recipe suggestions with possible swaps
    """
    # Combine ingredients to find recipes
    combined_ingredients = list(set(user_ingredients + other_user_ingredients))
    recipes = get_recipe_by_ingredients(combined_ingredients)
    
    if not recipes:
        return []
    
    result = []
    
    for recipe in recipes:
        recipe_ingredients = []
        for ing in recipe.get('usedIngredients', []) + recipe.get('missedIngredients', []):
            recipe_ingredients.append(ing.get('name', '').lower())
        
        # Determine which ingredients each user has
        user_has = []
        other_has = []
        missing = []
        
        for ing in recipe_ingredients:
            if ing in user_ingredients:
                user_has.append(ing)
            elif ing in other_user_ingredients:
                other_has.append(ing)
            else:
                missing.append(ing)
        
        # Get possible swaps for missing ingredients
        swaps = {}
        if missing:
            swap_suggestions = get_recipe_swap_suggestions(missing)
            
            # Check if any swaps are in either user's pantry
            for missing_ing, substitutes in swap_suggestions.items():
                valid_swaps = []
                
                for substitute in substitutes:
                    # Extract the ingredient name from the substitute string
                    # Example: "1 cup of Greek yogurt" -> "Greek yogurt"
                    parts = substitute.lower().split(' ')
                    if len(parts) > 2:
                        sub_name = ' '.join(parts[2:])
                    else:
                        sub_name = parts[-1]
                    
                    if sub_name in user_ingredients or sub_name in other_user_ingredients:
                        valid_swaps.append(substitute)
                
                if valid_swaps:
                    swaps[missing_ing] = valid_swaps
        
        # Add to result
        result.append({
            'recipe': recipe,
            'user_provides': user_has,
            'other_provides': other_has,
            'missing': missing,
            'possible_swaps': swaps
        })
    
    # Sort by fewest missing ingredients
    result.sort(key=lambda x: len(x['missing']))
    
    return result