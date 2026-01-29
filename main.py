#!/usr/bin/env python3
import argparse
import gzip
import json
import os
import re
import sys
import zipfile


def sanitize_filename(name):
    """Sanitize recipe names for file system usage."""
    # Replace slashes and other illegal chars with hyphens
    name = re.sub(r'[\\/*?:"<>|]', "-", name)
    return name.strip()


def format_cooklang(recipe):
    """Transform Paprika JSON structure to Cooklang text format."""
    lines = []

    # -- Metadata --
    meta_fields = {
        "servings": "servings",
        "source": "source",
        "total_time": "total time",
        "prep_time": "prep time",
        "cook_time": "cook time",
        "created": "created",
    }

    for json_key, cook_key in meta_fields.items():
        if val := recipe.get(json_key):
            lines.append(f">> {cook_key}: {val}")

    lines.append("")

    # -- Ingredients --
    lines.append("-- Ingredients --")
    if ingredients := recipe.get("ingredients"):
        for line in ingredients.split("\n"):
            line = line.strip()
            if line:
                # Paprika stores ingredients as unstructured text.
                # We output raw text; user must manually tag (e.g., @flour{1%cup}).
                lines.append(line)
    lines.append("")

    # -- Directions --
    lines.append("-- Directions --")
    if directions := recipe.get("directions"):
        lines.append(directions.strip())

    return "\n".join(lines)


def convert_recipes(input_file, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    print(f"Processing '{input_file}'...")
    count = 0

    try:
        with zipfile.ZipFile(input_file, "r") as z:
            for filename in z.namelist():
                if filename.endswith(".paprikarecipe"):
                    try:
                        with z.open(filename) as compressed_file:
                            with gzip.open(compressed_file, "rb") as gz:
                                json_data = json.loads(gz.read().decode("utf-8"))
                                cook_content = format_cooklang(json_data)

                                safe_name = sanitize_filename(
                                    json_data.get("name", "Untitled")
                                )
                                output_path = os.path.join(
                                    output_dir, f"{safe_name}.cook"
                                )

                                with open(output_path, "w", encoding="utf-8") as f:
                                    f.write(cook_content)

                                count += 1

                    except Exception as e:
                        print(
                            f"Warning: Failed to process {filename}: {e}",
                            file=sys.stderr,
                        )

            print(f"\nSuccess! Converted {count} recipes to '{output_dir}/'")

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except zipfile.BadZipFile:
        print(
            f"Error: '{input_file}' is not a valid Paprika export (Zip archive).",
            file=sys.stderr,
        )
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert Paprika 3 exports (.paprikarecipes) to Cooklang (.cook) files."
    )
    parser.add_argument("input_file", help="Path to the .paprikarecipes export file")
    parser.add_argument(
        "-o",
        "--output",
        default="cook_recipes",
        help="Output directory (default: cook_recipes)",
    )

    args = parser.parse_args()
    convert_recipes(args.input_file, args.output)


if __name__ == "__main__":
    main()
