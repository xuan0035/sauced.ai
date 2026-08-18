# sauced.ai 🍳

An agentic meal prep assistant that scrapes Substack recipe newsletters, generates nutritional information, and ranks recipes based on your personal goals — all through natural language.

## What It Does

Paste a Substack newsletter URL and tell sauced.ai about your nutritional goals, budget, or taste preferences. The agent will:

1. Scrape the newsletter for recipe posts using Browser Use
2. Extract ingredients from each recipe using GPT-4o-mini
3. Look up nutritional data for each ingredient via the USDA FoodData Central API
4. Compute total calories, protein, fat, and carbs per recipe
5. Rank and return recipes based on your criteria
6. Scale ingredients for your meal prep batch size and generate a grocery list

## Tech Stack

- **Agent framework:** uAgents (Fetch.ai)
- **Web scraping:** Browser Use
- **LLM:** OpenAI GPT-4o-mini (recipe extraction, unit conversion)
- **Nutrition data:** USDA FoodData Central API
- **Language:** Python

## How It Works

The core pipeline runs as a uAgent that listens for incoming messages containing a Substack URL. On receiving a URL it:

1. Opens the newsletter page with Browser Use and collects post links
2. Visits each post and extracts text content
3. Passes the text to GPT-4o-mini to determine if it contains a recipe and extract ingredients
4. For each ingredient, estimates gram weight via LLM and queries the USDA API for nutritional data
5. Aggregates macros across all ingredients and returns structured recipe results

## Setup

1. Clone the repo
2. Install dependencies:
```
pip install uagents browser-use openai requests
```
3. Set environment variables:
```
export OPENAI_API_KEY=your_key
export USDA_API_KEY=your_key
```
4. Run the agent:
```
python agent.py
```

## Built At

UCSD Hackathon 2026
