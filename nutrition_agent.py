"""
Agent 2 — Nutrition Matcher Agent
Calls Edamam Nutrition Analysis API to get macros for each recipe,
then scores and ranks recipes against the user's profile.

TODO (Person 2):
  - Register at https://developer.edamam.com/ for a free API key
  - Set EDAMAM_APP_ID and EDAMAM_APP_KEY in .env
  - Uncomment the real Edamam call in `_get_nutrition()`
"""

import asyncio
import os
import uuid
from typing import Optional

import httpx

from models import (
    Recipe, RecipeResult, UserProfile,
    NutritionInfo, DietaryRestriction
)

EDAMAM_BASE = "https://api.edamam.com/api/nutrition-details"


class NutritionAgent:
    """
    Fetch.AI uAgent that enriches recipes with Edamam nutrition data
    and scores them against the user's macro/dietary profile.
    """

    def __init__(self):
        self.app_id = os.getenv("EDAMAM_APP_ID", "")
        self.app_key = os.getenv("EDAMAM_APP_KEY", "")

    async def match(
        self,
        recipes: list[Recipe],
        profile: UserProfile,
    ) -> list[RecipeResult]:
        """
        Enrich each recipe with nutrition info, score against profile,
        return sorted list (best match first).
        """
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            tasks = [self._process_recipe(client, r, profile) for r in recipes]
            results = await asyncio.gather(*tasks)

        # Sort by match score descending
        results.sort(key=lambda r: r.match_score, reverse=True)
        return results

    async def _process_recipe(
        self,
        client: httpx.AsyncClient,
        recipe: Recipe,
        profile: UserProfile,
    ) -> RecipeResult:
        nutrition = await self._get_nutrition(client, recipe)
        score, reasons, warnings = self._score_recipe(recipe, nutrition, profile)
        return RecipeResult(
            **recipe.model_dump(),
            nutrition=nutrition,
            match_score=score,
            match_reasons=reasons,
            match_warnings=warnings,
        )

    async def _get_nutrition(
        self,
        client: httpx.AsyncClient,
        recipe: Recipe,
    ) -> NutritionInfo:
        """
        Call Edamam Nutrition Analysis API.
        Falls back to stub data if keys not set.
        """
        if not self.app_id or not self.app_key:
            return self._stub_nutrition(recipe)

        # Build ingredient list for Edamam
        ingredient_lines = [
            f"{ing.amount or ''} {ing.unit or ''} {ing.name}".strip()
            for ing in recipe.ingredients
        ]

        payload = {
            "title": recipe.title,
            "ingr": ingredient_lines,
        }

        try:
            resp = await client.post(
                EDAMAM_BASE,
                params={"app_id": self.app_id, "app_key": self.app_key},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            nutrients = data.get("totalNutrients", {})
            servings = recipe.servings or 1

            return NutritionInfo(
                calories=self._n(nutrients, "ENERC_KCAL", servings),
                protein_g=self._n(nutrients, "PROCNT", servings),
                carbs_g=self._n(nutrients, "CHOCDF", servings),
                fat_g=self._n(nutrients, "FAT", servings),
                fiber_g=self._n(nutrients, "FIBTG", servings),
            )
        except Exception as e:
            print(f"[NutritionAgent] Edamam error for '{recipe.title}': {e}")
            return self._stub_nutrition(recipe)

    def _n(self, nutrients: dict, key: str, servings: int) -> Optional[float]:
        entry = nutrients.get(key)
        if entry:
            return round(entry["quantity"] / servings, 1)
        return None

    def _score_recipe(
        self,
        recipe: Recipe,
        nutrition: NutritionInfo,
        profile: UserProfile,
    ) -> tuple[float, list[str], list[str]]:
        """
        Scoring logic — extensible rule engine.
        Returns (score 0–100, positive reasons, warnings).
        """
        score = 50.0
        reasons = []
        warnings = []
        macros = profile.macros

        # ── Calorie match ─────────────────────────────────────────────────────
        if nutrition.calories and macros.calories_per_day:
            meal_target = macros.calories_per_day / profile.meals_per_week
            cal_diff_pct = abs(nutrition.calories - meal_target) / meal_target
            if cal_diff_pct < 0.10:
                score += 15
                reasons.append("Calories are on target")
            elif cal_diff_pct < 0.20:
                score += 8
                reasons.append("Calories are close to target")
            else:
                score -= 10
                warnings.append(f"Calories ({nutrition.calories:.0f}) may be off your goal")

        # ── Protein match ─────────────────────────────────────────────────────
        if nutrition.protein_g and macros.protein_g:
            meal_protein = macros.protein_g / profile.meals_per_week
            if nutrition.protein_g >= meal_protein * 0.9:
                score += 15
                reasons.append("High protein — meets your goal")
            elif nutrition.protein_g >= meal_protein * 0.7:
                score += 7
                reasons.append("Decent protein content")

        # ── Cuisine preference ────────────────────────────────────────────────
        pref_names = [p.value for p in profile.cuisine_preferences]
        matching_tags = [t for t in recipe.tags if t in pref_names]
        if matching_tags:
            score += 10
            reasons.append(f"Matches your cuisine preferences: {', '.join(matching_tags)}")

        # ── Dietary restriction checks ────────────────────────────────────────
        restriction_tag_map = {
            DietaryRestriction.vegan: ["vegan"],
            DietaryRestriction.vegetarian: ["vegetarian", "vegan"],
            DietaryRestriction.gluten_free: ["gluten-free"],
        }
        for restriction in profile.dietary_restrictions:
            allowed_tags = restriction_tag_map.get(restriction, [])
            if allowed_tags and not any(t in recipe.tags for t in allowed_tags):
                score -= 30
                warnings.append(f"May not be {restriction.value}")

        # ── Budget check ──────────────────────────────────────────────────────
        if profile.weekly_budget_usd:
            per_meal_budget = profile.weekly_budget_usd / profile.meals_per_week
            # Rough estimate: $2/ingredient
            estimated_cost = len(recipe.ingredients) * 2
            if estimated_cost <= per_meal_budget:
                score += 5
                reasons.append("Within your weekly budget")

        # ── Flavor/note keyword match ─────────────────────────────────────────
        if profile.flavor_notes:
            notes_lower = profile.flavor_notes.lower()
            desc_lower = (recipe.description or "").lower()
            if any(word in desc_lower for word in notes_lower.split()):
                score += 5
                reasons.append("Matches your flavor preferences")

        score = max(0.0, min(100.0, score))
        return round(score, 1), reasons, warnings

    def _stub_nutrition(self, recipe: Recipe) -> NutritionInfo:
        """Deterministic stub based on recipe tag content."""
        base = {
            "calories": 520.0, "protein_g": 28.0,
            "carbs_g": 55.0, "fat_g": 18.0, "fiber_g": 6.0
        }
        if "high-protein" in recipe.tags:
            base["protein_g"] = 42.0
            base["calories"] = 480.0
        if "vegan" in recipe.tags or "vegetarian" in recipe.tags:
            base["protein_g"] = 16.0
            base["fiber_g"] = 12.0
        return NutritionInfo(**base)
