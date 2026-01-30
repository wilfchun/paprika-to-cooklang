#!/usr/bin/env python3
import argparse
import concurrent.futures
import gzip
import json
import os
import re
import sys
import time
import zipfile

from google import genai
from google.genai import types

# --- CONFIGURATION ---
MODEL_NAME = "gemini-3-flash-preview"
MAX_WORKERS = 20


def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "-", name)
    return name.strip()


def get_client():
    # api_key = os.environ.get("GEMINI_API_KEY")
    api_key = "AIzaSyBUNuwI1iQvE9j9nsaM4jx3bFEXJoo_6kk"
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found.", file=sys.stderr)
        sys.exit(1)
    return genai.Client(api_key=api_key)


def convert_single_recipe(recipe_data, output_dir, client):
    name = recipe_data.get("name", "Untitled")
    safe_name = sanitize_filename(name)
    output_path = os.path.join(output_dir, f"{safe_name}.cook")

    # DEFINE PROMPT
    prompt_text = f"""
    You are a Cooklang converter. Convert this Paprika recipe JSON into a valid .cook file.

    RULES:
    1. OUTPUT ONLY the raw Cooklang text. No markdown fences.
    2. INGREDIENTS: Integrate ingredients INLINE (e.g., "Add @flour{{1%cup}}").
       If not in directions, list them in a block at the end.
    3. METADATA: Include >> source, >> prep time, >> cook time, >> servings.
    4. DATA:
    {json.dumps(recipe_data, indent=2)}
    """

    # CALL API (With Retry)
    for attempt in range(10):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    response_mime_type="text/plain", temperature=0.3
                ),
            )

            # Clean up potential markdown fences
            cook_content = (
                response.text.replace("```cook", "").replace("```", "").strip()
            )

            # SAVE ALWAYS
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cook_content)

            return f"✅ Converted: {safe_name}"

        except Exception as e:
            if "429" in str(e) or "503" in str(e):
                time.sleep(2 * (attempt + 1))
            else:
                return f"❌ Failed ({name}): {e}"

    return f"❌ Failed ({name}): Max retries reached"


def load_recipes_from_zip(input_file):
    recipes = []
    try:
        with zipfile.ZipFile(input_file, "r") as z:
            for filename in z.namelist():
                if filename.endswith(".paprikarecipe"):
                    with z.open(filename) as compressed_file:
                        with gzip.open(compressed_file, "rb") as gz:
                            data = json.load(gz)
                            recipes.append(data)
    except Exception as e:
        print(f"Error reading zip: {e}")
        sys.exit(1)
    return recipes


def main():
    parser = argparse.ArgumentParser(description="Turbo Cooklang Converter (No Cache)")
    parser.add_argument("input_file", help="Path to .paprikarecipes file")
    parser.add_argument(
        "-o", "--output", default="cook_recipes", help="Output directory"
    )
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    client = get_client()

    print(f"📂 Reading archive: {args.input_file}...")
    recipes = load_recipes_from_zip(args.input_file)
    print(f"🚀 Starting Turbo Mode: {len(recipes)} recipes found.")
    print(f"⚡ Model: {MODEL_NAME} | Workers: {MAX_WORKERS}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tasks (removed force flag)
        futures = {
            executor.submit(convert_single_recipe, recipe, args.output, client): recipe
            for recipe in recipes
        }

        completed = 0
        total = len(recipes)

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            completed += 1
            print(f"[{completed}/{total}] {result}")

    print("\n✅ Batch Complete.")


if __name__ == "__main__":
    main()
