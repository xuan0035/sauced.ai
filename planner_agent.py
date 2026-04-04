"""
Agent 3 — Meal Planner Agent
Takes top-matched recipes, scales to user's prep quantity,
generates a shopping list, and optionally places an Instacart order.

TODO (Person 1 / Person 2):
  - Integrate real Instacart API when available
  - Wire into Fetch.AI uAgents message bus
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from models import (
    RecipeResult, UserProfile, MealPlan,
    ScaledRecipe, ShoppingListItem, Ingredient, NutritionInfo
)


class PlannerAgent:
    """
    Fetch.AI uAgent that scales recipes and builds a weekly meal plan
    with an aggregated shopping list.
    """

    async def plan(
        self,
        matched_recipes: list[RecipeResult],
        profile: UserProfile,
        servings_per_recipe: int = 4,
    ) -> MealPlan:
        """
        Pick top recipes (up to meals_per_week), scale them,
        and aggregate a shopping list.
        """
        # Select top N recipes
        top = matched_recipes[:profile.meals_per_week]

        scaled = []
        for recipe in top:
            scaled.append(self._scale_recipe(recipe, servings_per_recipe))

        shopping_list = self._build_shopping_list(scaled)
        total_cal = self._total_calories(scaled)
        cost_est = self._estimate_cost(shopping_list)

        week_start = datetime.utcnow()
        week_label = f"Week of {week_start.strftime('%b %d, %Y')}"

        return MealPlan(
            week_label=week_label,
            total_calories=total_cal,
            total_cost_estimate_usd=cost_est,
            recipes=scaled,
            shopping_list=shopping_list,
            instacart_order_url=self._build_instacart_url(shopping_list),
        )

    def _scale_recipe(
        self,
        recipe: RecipeResult,
        target_servings: int,
    ) -> ScaledRecipe:
        original = recipe.servings or 2
        ratio = target_servings / original

        scaled_ingredients = [
            self._scale_ingredient(ing, ratio)
            for ing in recipe.ingredients
        ]

        scaled_nutrition = None
        if recipe.nutrition:
            n = recipe.nutrition
            scaled_nutrition = NutritionInfo(
                calories=self._scale_val(n.calories, ratio),
                protein_g=self._scale_val(n.protein_g, ratio),
                carbs_g=self._scale_val(n.carbs_g, ratio),
                fat_g=self._scale_val(n.fat_g, ratio),
                fiber_g=self._scale_val(n.fiber_g, ratio),
            )

        return ScaledRecipe(
            recipe=recipe,
            scaled_servings=target_servings,
            scaled_ingredients=scaled_ingredients,
            scaled_nutrition=scaled_nutrition or NutritionInfo(),
        )

    def _scale_ingredient(self, ing: Ingredient, ratio: float) -> Ingredient:
        """Try to scale numeric amounts; leave strings as-is."""
        if ing.amount:
            try:
                original_amount = self._parse_fraction(ing.amount)
                new_amount = original_amount * ratio
                # Format nicely: use fractions for small numbers
                formatted = self._format_amount(new_amount)
                return Ingredient(name=ing.name, amount=formatted, unit=ing.unit)
            except ValueError:
                pass
        return Ingredient(name=ing.name, amount=ing.amount, unit=ing.unit)

    def _parse_fraction(self, s: str) -> float:
        """Parse '1/2', '1 1/2', '3', etc."""
        s = s.strip()
        if " " in s:
            parts = s.split(" ", 1)
            return float(parts[0]) + self._parse_fraction(parts[1])
        if "/" in s:
            num, den = s.split("/")
            return float(num) / float(den)
        return float(s)

    def _format_amount(self, val: float) -> str:
        fractions = {0.25: "¼", 0.5: "½", 0.75: "¾", 0.33: "⅓", 0.67: "⅔"}
        whole = int(val)
        frac = val - whole
        for f_val, f_str in fractions.items():
            if abs(frac - f_val) < 0.05:
                return f"{whole} {f_str}".strip() if whole else f_str
        return f"{val:.1f}".rstrip("0").rstrip(".")

    def _scale_val(self, val: Optional[float], ratio: float) -> Optional[float]:
        if val is None:
            return None
        return round(val * ratio, 1)

    def _build_shopping_list(self, scaled: list[ScaledRecipe]) -> list[ShoppingListItem]:
        """
        Aggregate ingredients across all scaled recipes.
        Simple grouping by name — enhance with unit conversion for production.
        """
        aggregated: dict[str, dict] = {}
        for sr in scaled:
            for ing in sr.scaled_ingredients:
                key = ing.name.lower().strip()
                if key not in aggregated:
                    aggregated[key] = {
                        "ingredient": ing.name,
                        "parts": [],
                        "unit": ing.unit,
                    }
                amount_str = f"{ing.amount or ''} {ing.unit or ''}".strip()
                aggregated[key]["parts"].append(amount_str)

        items = []
        for key, data in aggregated.items():
            total = ", ".join(p for p in data["parts"] if p)
            items.append(ShoppingListItem(
                ingredient=data["ingredient"],
                total_amount=total,
                estimated_cost_usd=self._estimate_ingredient_cost(data["ingredient"]),
                instacart_link=self._instacart_ingredient_link(data["ingredient"]),
            ))

        return sorted(items, key=lambda i: i.ingredient)

    def _estimate_ingredient_cost(self, ingredient: str) -> float:
        """Very rough cost heuristic — replace with real pricing API."""
        expensive = ["salmon", "beef", "shrimp", "chicken thigh", "chicken breast"]
        cheap = ["rice", "beans", "lentils", "oats", "eggs", "potato"]
        name = ingredient.lower()
        if any(e in name for e in expensive):
            return round(5.0 + hash(name) % 400 / 100, 2)
        if any(c in name for c in cheap):
            return round(1.0 + hash(name) % 200 / 100, 2)
        return round(2.0 + hash(name) % 300 / 100, 2)

    def _instacart_ingredient_link(self, ingredient: str) -> str:
        """Deep link to Instacart search for the ingredient."""
        query = ingredient.replace(" ", "+")
        return f"https://www.instacart.com/store/search_v3/term?term={query}"

    def _build_instacart_url(self, items: list[ShoppingListItem]) -> Optional[str]:
        """
        Placeholder — Instacart's Partner API requires approval.
        This generates a search URL; replace with real order API.
        """
        if not items:
            return None
        first = items[0].ingredient.replace(" ", "+")
        return f"https://www.instacart.com/store/search_v3/term?term={first}"

    def _total_calories(self, scaled: list[ScaledRecipe]) -> float:
        total = 0.0
        for sr in scaled:
            if sr.scaled_nutrition and sr.scaled_nutrition.calories:
                total += sr.scaled_nutrition.calories
        return round(total, 1)

    def _estimate_cost(self, shopping_list: list[ShoppingListItem]) -> float:
        return round(sum(
            item.estimated_cost_usd or 0
            for item in shopping_list
        ), 2)
