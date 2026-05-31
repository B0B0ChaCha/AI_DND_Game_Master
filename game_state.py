# game_state.py
import json
import os

SAVE_FILE = "save_data.json"


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
        "awaiting_roll": None
    }


def normalize_game_state(game_state):
    """
    Ensures a loaded save file has all required fields.
    This protects older save files from breaking the app after updates.
    """

    default_state = get_default_game_state()

    if not isinstance(game_state, dict):
        return default_state

    for key, value in default_state.items():
        if key not in game_state:
            game_state[key] = value

    if not isinstance(game_state["inventory"], list):
        game_state["inventory"] = default_state["inventory"]

    if not isinstance(game_state["messages"], list):
        game_state["messages"] = []

    return game_state


def save_game_state(game_state):
    """
    Saves the current game state into a JSON file.
    """

    with open(SAVE_FILE, "w", encoding="utf-8") as file:
        json.dump(game_state, file, indent=4)


def load_game_state():
    """
    Loads the game state from a JSON file.
    If no save file exists, or if the save is empty/corrupted,
    it returns the default game state.
    """

    if not os.path.exists(SAVE_FILE):
        return get_default_game_state()

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            game_state = json.load(file)

        return normalize_game_state(game_state)

    except json.JSONDecodeError:
        print("Warning: save_data.json is empty or corrupted. Starting new game.")
        return get_default_game_state()

    except OSError:
        print("Warning: save_data.json could not be read. Starting new game.")
        return get_default_game_state()


def delete_save_file():
    """
    Deletes the saved game file if it exists.
    """

    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
