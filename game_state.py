# game_state.py
import json
from datetime import datetime


def get_default_game_state():
    """
    Returns the default starting game state for a new adventure.
    """

    return {
        "player_name": "Adventurer",
        "location": "Village Entrance",
        "health": 100,
        "inventory": ["Rusty Sword", "Torch", "Small Healing Potion"],
        "objective": "Investigate the mysterious curse affecting the village",
        "messages": [],
        "awaiting_roll": None,
        "npcs": {},
        "save_metadata": {
            "saved_at": None
        }
    }


def normalize_game_state(game_state):
    """
    Ensures a loaded save file has all required fields.
    This protects older or incomplete save files from breaking the app.
    """

    default_state = get_default_game_state()

    if not isinstance(game_state, dict):
        return default_state

    for key, value in default_state.items():
        if key not in game_state:
            game_state[key] = value

    if not isinstance(game_state["player_name"], str):
        game_state["player_name"] = default_state["player_name"]

    if not isinstance(game_state["location"], str):
        game_state["location"] = default_state["location"]

    if not isinstance(game_state["health"], int):
        game_state["health"] = default_state["health"]

    if not isinstance(game_state["inventory"], list):
        game_state["inventory"] = default_state["inventory"]

    if not isinstance(game_state["objective"], str):
        game_state["objective"] = default_state["objective"]

    if not isinstance(game_state["messages"], list):
        game_state["messages"] = []

    if game_state["awaiting_roll"] is not None and not isinstance(game_state["awaiting_roll"], dict):
        game_state["awaiting_roll"] = None

    if "npcs" not in game_state or not isinstance(game_state["npcs"], dict):
        game_state["npcs"] = {}

    if not isinstance(game_state["save_metadata"], dict):
        game_state["save_metadata"] = default_state["save_metadata"]

    for key, value in default_state["save_metadata"].items():
        if key not in game_state["save_metadata"]:
            game_state["save_metadata"][key] = value

    return game_state


def convert_game_state_to_json(game_state):
    """
    Converts the current game state into a formatted JSON string.
    Adds a date and time stamp before downloading the save file.
    """

    normalized_state = normalize_game_state(game_state)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    normalized_state["save_metadata"] = {
        "saved_at": current_time,
    }

    return json.dumps(normalized_state, indent=4)


def load_game_state_from_uploaded_file(uploaded_file):
    """
    Loads game state data from a JSON file uploaded by the player.
    If the file is missing, invalid, or corrupted, it returns the default game state.
    """

    if uploaded_file is None:
        return get_default_game_state()

    try:
        file_content = uploaded_file.read().decode("utf-8")
        game_state = json.loads(file_content)
        return normalize_game_state(game_state)

    except json.JSONDecodeError:
        print("Warning: Uploaded save file is not valid JSON. Starting new game.")
        return get_default_game_state()

    except UnicodeDecodeError:
        print("Warning: Uploaded save file could not be decoded. Starting new game.")
        return get_default_game_state()

    except Exception as error:
        print(f"Warning: Failed to load uploaded save file. Details: {error}")
        return get_default_game_state()