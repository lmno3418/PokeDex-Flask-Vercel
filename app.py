from flask import Flask, render_template, request, jsonify
import json
import os
import ast  # Added to safely parse Python literals

app = Flask(__name__)

# Global variables to store both raw and transformed data
raw_pokemon_data = []
pokemon_data = []

# Load Pokemon data
data_path = os.path.join(os.path.dirname(__file__), "static/data/PokemonData2.json")
try:
    # Use relative path from the application root
    with open(data_path, "r") as f:
        raw_pokemon_data = json.load(f)

    # Transform data to match expected format
    pokemon_data = []
    for pokemon in raw_pokemon_data:
        # Properly parse the sprites string
        sprite_data = {}
        try:
            # Convert Python string representation to actual dictionary
            if isinstance(pokemon["sprites"], str):
                sprite_data = ast.literal_eval(pokemon["sprites"])
            else:
                sprite_data = pokemon["sprites"]
        except Exception as e:
            print(f"Error parsing sprites for {pokemon['Name']}: {str(e)}")
            sprite_data = {"normal": "", "animated": ""}

        transformed_pokemon = {
            "id": pokemon["#"],
            "name": pokemon["Name"],
            "type1": pokemon["Type 1"],
            "type2": pokemon["Type 2"] if pokemon["Type 2"] != "Normal" else "",
            "hp": pokemon["HP"],
            "attack": pokemon["Attack"],
            "defense": pokemon["Defense"],
            "sp_atk": pokemon["Sp. Atk"],
            "sp_def": pokemon["Sp. Def"],
            "speed": pokemon["Speed"],
            "generation": pokemon["Generation"],
            "legendary": pokemon["Legendary"],
            "height": pokemon["height"],
            "weight": pokemon["weight"],
            "base_experience": pokemon["base_experience"],
            "sprites": sprite_data,  # Use the parsed dictionary instead of the string
        }
        pokemon_data.append(transformed_pokemon)

    print(
        f"Successfully loaded and transformed {len(pokemon_data)} Pokemon from {data_path}"
    )
except FileNotFoundError:
    # Fallback for debugging
    print(f"ERROR: Could not find file at {data_path}")
    pokemon_data = []
except json.JSONDecodeError:
    print(f"ERROR: Invalid JSON data in {data_path}")
    pokemon_data = []
except Exception as e:
    print(f"ERROR: Unexpected error loading Pokemon data: {str(e)}")
    pokemon_data = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/pokemon")
def get_pokemon():
    search_query = request.args.get("search", "").lower()

    # Standard filters
    filters = {
        "height": request.args.get("height"),
        "weight": request.args.get("weight"),
        "base_experience": request.args.get("base_experience"),
        "type1": request.args.get("type1"),
        "type2": request.args.get("type2"),
        "generation": request.args.get("generation"),
        "legendary": request.args.get("legendary"),
    }

    # Range filters
    range_filters = {
        "hp": {
            "min": request.args.get("hp_min"),
            "max": request.args.get("hp_max"),
        },
        "attack": {
            "min": request.args.get("attack_min"),
            "max": request.args.get("attack_max"),
        },
        "defense": {
            "min": request.args.get("defense_min"),
            "max": request.args.get("defense_max"),
        },
        "sp_atk": {
            "min": request.args.get("sp_atk_min"),
            "max": request.args.get("sp_atk_max"),
        },
        "sp_def": {
            "min": request.args.get("sp_def_min"),
            "max": request.args.get("sp_def_max"),
        },
        "speed": {
            "min": request.args.get("speed_min"),
            "max": request.args.get("speed_max"),
        },
    }

    def matches_filters(pokemon):
        # Check standard filters
        for key, value in filters.items():
            if value is not None and value != "":
                if key == "legendary":
                    # Handle boolean values
                    pokemon_value = pokemon.get(key, False)
                    filter_value = value.lower() == "true"
                    if pokemon_value != filter_value:
                        return False
                # Handle null/None type2
                elif key == "type2" and value.lower() == "none":
                    if (
                        pokemon.get(key, None) is not None
                        and pokemon.get(key, "") != ""
                    ):
                        return False
                elif str(pokemon.get(key, "")).lower() != value.lower():
                    return False

        # Check range filters
        for stat, range_values in range_filters.items():
            min_val = range_values["min"]
            max_val = range_values["max"]

            if min_val is not None and min_val != "":
                try:
                    if int(pokemon.get(stat, 0)) < int(min_val):
                        return False
                except ValueError:
                    pass

            if max_val is not None and max_val != "":
                try:
                    if int(pokemon.get(stat, 0)) > int(max_val):
                        return False
                except ValueError:
                    pass

        return True

    if search_query:
        filtered_pokemon = [
            pokemon
            for pokemon in pokemon_data
            if search_query in pokemon.get("name", "").lower()
            and matches_filters(pokemon)
        ]
    else:
        filtered_pokemon = [
            pokemon for pokemon in pokemon_data if matches_filters(pokemon)
        ]

    return jsonify(filtered_pokemon)


@app.route("/api/pokemon/<pokemon_id>")
def get_pokemon_by_id(pokemon_id):
    for pokemon in pokemon_data:
        if pokemon.get("id") == pokemon_id:
            return jsonify(pokemon)

    return jsonify({"error": "Pokemon not found"}), 404


@app.route("/api/debug")
def debug_info():
    return jsonify(
        {
            "pokemon_count": len(pokemon_data),
            "first_pokemon_transformed": pokemon_data[0] if pokemon_data else None,
            "file_exists": os.path.exists(data_path),
            "transformation_keys": {
                "original": [
                    "#",
                    "Name",
                    "Type 1",
                    "Type 2",
                    "HP",
                    "Attack",
                    "Defense",
                    "Sp. Atk",
                    "Sp. Def",
                    "Speed",
                ],
                "transformed": [
                    "id",
                    "name",
                    "type1",
                    "type2",
                    "hp",
                    "attack",
                    "defense",
                    "sp_atk",
                    "sp_def",
                    "speed",
                ],
            },
        }
    )


@app.route("/api/debug/sprites")
def debug_sprites():
    if len(pokemon_data) > 0:
        first_pokemon = pokemon_data[0]
        return jsonify(
            {
                "pokemon_name": first_pokemon["name"],
                "sprites_raw": raw_pokemon_data[0]["sprites"]
                if "sprites" in raw_pokemon_data[0]
                else None,
                "sprites_transformed": first_pokemon["sprites"],
                "is_string": isinstance(first_pokemon["sprites"], str),
            }
        )
    return jsonify({"error": "No Pokemon data available"})


if __name__ == "__main__":
    app.run(debug=True)
