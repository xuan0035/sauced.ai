import os
import requests
from uagents import Agent, Context
from browser_use import Browser
from openai import OpenAI

# --- CONFIG ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USDA_API_KEY = os.getenv("USDA_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

agent = Agent(
    name="scraper_agent",
    seed="scraper_seed",
    port=8001,
    endpoints=["http://localhost:8001/submit"]
)

# -------------------------------
# 🧠 LLM: Extract recipe + ingredients
# -------------------------------
def extract_recipe(text):
    prompt = f"""
    Determine if this text contains a recipe.

    If YES, return JSON:
    {{
      "is_recipe": true,
      "title": "",
      "ingredients": ["..."]
    }}

    If NO:
    {{
      "is_recipe": false
    }}

    ტექსტ:
    {text[:3000]}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return eval(response.choices[0].message.content)
    except:
        return {"is_recipe": False}


# -------------------------------
# 🌐 Browser Use: scrape Substack
# -------------------------------
async def scrape_substack(url):
    browser = Browser()

    page = await browser.open(url)
    links = await page.get_links()

    post_links = [l for l in links if "/p/" in l][:5]

    recipes = []

    for link in post_links:
        post = await browser.open(link)
        text = await post.get_text()

        parsed = extract_recipe(text)

        if parsed.get("is_recipe"):
            recipes.append(parsed)

    return recipes


# -------------------------------
# 🥗 USDA: search food
# -------------------------------
def search_usda(food_name):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"

    params = {
        "query": food_name,
        "api_key": USDA_API_KEY
    }

    res = requests.get(url, params=params).json()

    if not res.get("foods"):
        return None

    for food in res["foods"]:
        if food["dataType"] in ["Foundation", "SR Legacy"]:
            return food

    return res["foods"][0]


# -------------------------------
# ⚖️ Convert to grams (LLM shortcut)
# -------------------------------
def estimate_grams(ingredient):
    prompt = f"""
    Convert this ingredient into grams. Return ONLY a number.

    {ingredient}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return float(response.choices[0].message.content.strip())
    except:
        return 100.0


# -------------------------------
# ➕ Compute nutrition
# -------------------------------
def compute_nutrition(ingredients):
    total = {
        "calories": 0,
        "protein": 0,
        "fat": 0,
        "carbs": 0
    }

    for ing in ingredients:
        grams = estimate_grams(ing)
        food = search_usda(ing)

        if not food:
            continue

        nutrients = {n["nutrientName"]: n["value"] for n in food.get("foodNutrients", [])}

        factor = grams / 100

        total["calories"] += nutrients.get("Energy", 0) * factor
        total["protein"] += nutrients.get("Protein", 0) * factor
        total["fat"] += nutrients.get("Total lipid (fat)", 0) * factor
        total["carbs"] += nutrients.get("Carbohydrate, by difference", 0) * factor

    return total


# -------------------------------
# 🤖 MAIN AGENT HANDLER
# -------------------------------
@agent.on_message(model=str)
async def handle(ctx: Context, sender: str, msg: str):
    url = msg.strip()

    ctx.logger.info(f"Scraping: {url}")

    recipes = await scrape_substack(url)

    results = []

    for r in recipes:
        nutrition = compute_nutrition(r["ingredients"])

        results.append({
            "title": r["title"],
            "ingredients": r["ingredients"],
            "nutrition": nutrition
        })

    ctx.logger.info(results)


# -------------------------------
# ▶️ RUN
# -------------------------------
if __name__ == "__main__":
    agent.run()