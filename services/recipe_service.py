import logging
import requests
from config import SPOONACULAR_API_KEY

logger = logging.getLogger(__name__)

def get_recipe_by_ingredients(ingredients, number=5):
    """
    Get recipes that can be made with the given ingredients.
    
    Parameters:
    - ingredients: List of ingredient names
    - number: Maximum number of recipes to return
    
    Returns:
    - List of recipe dictionaries
    """
    if not SPOONACULAR_API_KEY:
        logger.warning("No Spoonacular API key provided.")
        return []
    
    if not ingredients:
        return []
    
    # Build the API URL
    base_url = "https://api.spoonacular.com/recipes/findByIngredients"
    
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'ingredients': ','.join(ingredients),
        'number': number,
        'ranking': 2,  # Maximize used ingredients
        'ignorePantry': False
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            recipes = response.json()
            
            # Fetch additional recipe information
            detailed_recipes = []
            for recipe in recipes:
                details = get_recipe_details(recipe['id'])
                if details:
                    # Merge the details with the original recipe
                    merged_recipe = {**recipe, **details}
                    detailed_recipes.append(merged_recipe)
            
            return detailed_recipes
        else:
            logger.error(f"Error fetching recipes: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error in recipe API request: {e}")
        return []

def get_recipe_details(recipe_id):
    """
    Get detailed information about a specific recipe.
    
    Parameters:
    - recipe_id: ID of the recipe
    
    Returns:
    - Dictionary with recipe details
    """
    if not SPOONACULAR_API_KEY:
        return {}
    
    # Build the API URL
    base_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'includeNutrition': False
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching recipe details: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error in recipe details API request: {e}")
        return {}

def search_recipes(query, number=5):
    """
    Search for recipes by query.
    
    Parameters:
    - query: Search query
    - number: Maximum number of recipes to return
    
    Returns:
    - List of recipe dictionaries
    """
    if not SPOONACULAR_API_KEY:
        return []
    
    # Build the API URL
    base_url = "https://api.spoonacular.com/recipes/complexSearch"
    
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'query': query,
        'number': number,
        'addRecipeInformation': True
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        else:
            logger.error(f"Error searching recipes: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error in recipe search API request: {e}")
        return []

def get_recipe_swap_suggestions(ingredients):
    """
    Get ingredient swap suggestions for recipes.
    
    Parameters:
    - ingredients: List of ingredient names
    
    Returns:
    - Dictionary of ingredients and their possible substitutes
    """
    if not SPOONACULAR_API_KEY:
        return {}
    
    result = {}
    
    for ingredient in ingredients:
        # Build the API URL
        base_url = f"https://api.spoonacular.com/food/ingredients/substitutes"
        
        params = {
            'apiKey': SPOONACULAR_API_KEY,
            'ingredientName': ingredient
        }
        
        try:
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result[ingredient] = data.get('substitutes', [])
            else:
                logger.error(f"Error getting substitutes: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error in substitute API request: {e}")
    
    return result