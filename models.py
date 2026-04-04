"""
Shared Pydantic models for RecipeAgent.
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional, Any
from enum import Enum


class DietaryRestriction(str, Enum):
    vegan = "vegan"
    vegetarian = "vegetarian"
    gluten_free = "gluten-free"
    dairy_free = "dairy-free"
    nut_free = "nut-free"
    halal = "halal"
    kosher = "kosher"
    low_sodium = "low-sodium"


class CuisinePreference(str, Enum):
    chinese = "chinese"
    italian = "italian"
    mexican = "mexican"
    indian = "indian"
    mediterranean = "mediterranean"
    japanese = "japanese"
    thai = "thai"
    american = "american"
    french = "french"


class MacroGoals(BaseModel):
    calories_per_day: Optional[int] = None       # e.g. 2000
    protein_g: Optional[int] = None              # grams per day
    carbs_g: Optional[int] = None
    fat_g: Optional[int] = None
    fiber_g: Optional[int] = None


class UserProfile(BaseModel):
    name: str
    macros: MacroGoals
    dietary_restrictions: list[DietaryRestriction] = []
    cuisine_preferences: list[CuisinePreference] = []
    flavor_notes: Optional[str] = None           # e.g. "sweet recipes, bold spices"
    equipment_exclusions: Optional[str] = None   # e.g. "no stand mixer, no air fryer"
    weekly_budget_usd: Optional[float] = None    # e.g. 75.0
    meals_per_week: int = 5
    servings_per_meal: int = 2


class ScrapeRequest(BaseModel):
    url: str                                     # Substack newsletter URL
    max_recipes: int = 10


class Ingredient(BaseModel):
    name: str
    amount: Optional[str] = None
    unit: Optional[str] = None


class NutritionInfo(BaseModel):
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None


class Recipe(BaseModel):
    id: str
    title: str
    source_url: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    ingredients: list[Ingredient] = []
    instructions: list[str] = []
    prep_time_min: Optional[int] = None
    cook_time_min: Optional[int] = None
    servings: Optional[int] = None
    nutrition: Optional[NutritionInfo] = None
    tags: list[str] = []
    raw_text: Optional[str] = None              # for Edamam parsing


class RecipeResult(Recipe):
    match_score: float = 0.0                    # 0–100
    match_reasons: list[str] = []
    match_warnings: list[str] = []             # e.g. "contains nuts"


class ShoppingListItem(BaseModel):
    ingredient: str
    total_amount: str
    estimated_cost_usd: Optional[float] = None
    instacart_link: Optional[str] = None


class ScaledRecipe(BaseModel):
    recipe: RecipeResult
    scaled_servings: int
    scaled_ingredients: list[Ingredient]
    scaled_nutrition: NutritionInfo


class MealPlan(BaseModel):
    week_label: str
    total_calories: float
    total_cost_estimate_usd: Optional[float] = None
    recipes: list[ScaledRecipe]
    shopping_list: list[ShoppingListItem]
    instacart_order_url: Optional[str] = None


class MatchRequest(BaseModel):
    recipes: list[Recipe]
    profile: UserProfile


class MealPlanRequest(BaseModel):
    matched_recipes: list[RecipeResult]
    profile: UserProfile
    servings_per_recipe: int = 4


class JobStatus(BaseModel):
    job_id: str
    status: str                                 # pending | running | scraping | matching | planning | complete | error
    agent: str
    created_at: str
    result: Optional[Any] = None
    error: Optional[str] = None
