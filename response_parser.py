"""Helpers for cleaning and extracting structured data from AI responses."""

import re
from npc_memory import create_or_update_npc, add_npc_memory

RESPONSE_LABELS = [
    "Health:",
    "Inventory:",
    "Dice Roll:",
    "Result:",
    "Story:",
    "NPC_CREATED:",
    "NAME:",
    "ROLE:",
    "NPC_MEMORY_UPDATE:",
    "RELATIONSHIP_CHANGE:",
    "MEMORY:",
    "Objective:",
    "ROLL_REQUEST:",
    "CHECK_TYPE:",
    "DIFFICULTY:",
    "REASON:",
    "Choices:",
]

# NPC MEMORY AI RESPONSE
def update_npc_memory_from_ai_response(game_state, ai_response):
    if not ai_response:
        return

    if "npcs" not in game_state or not isinstance(game_state["npcs"], dict):
        game_state["npcs"] = {}

    created_blocks = re.findall(
        r"NPC_CREATED:\s*(.*?)(?=NPC_MEMORY_UPDATE:|Objective:|ROLL_REQUEST:|Choices:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL
    )

    for block in created_blocks:
        name_match = re.search(r"NAME:\s*(.*?)(?=\n|ROLE:|$)", block, re.IGNORECASE | re.DOTALL)
        role_match = re.search(r"ROLE:\s*(.*?)(?=\n|$)", block, re.IGNORECASE | re.DOTALL)

        if name_match:
            name = name_match.group(1).strip()
            role = role_match.group(1).strip() if role_match else "Unknown"

            if name and name != "...":
                create_or_update_npc(game_state, name, role)

    memory_blocks = re.findall(
        r"NPC_MEMORY_UPDATE:\s*(.*?)(?=NPC_CREATED:|Objective:|ROLL_REQUEST:|Choices:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL
    )

    for block in memory_blocks:
        name_match = re.search(r"NAME:\s*(.*?)(?=\n|RELATIONSHIP_CHANGE:|$)", block, re.IGNORECASE | re.DOTALL)
        change_match = re.search(r"RELATIONSHIP_CHANGE:\s*(-?\d+)", block, re.IGNORECASE)
        memory_match = re.search(r"MEMORY:\s*(.*?)(?=\n|$)", block, re.IGNORECASE | re.DOTALL)

        if name_match and memory_match:
            name = name_match.group(1).strip()
            memory = memory_match.group(1).strip()
            relationship_change = int(change_match.group(1)) if change_match else 0

            if name and name != "..." and memory and memory != "...":
                add_npc_memory(game_state, name, memory, relationship_change)


def format_ai_response_for_display(ai_response: str) -> str:
    """Ensure important response fields display on separate lines."""
    if not ai_response:
        return ai_response

    for label in RESPONSE_LABELS:
        ai_response = re.sub(rf"\s+{re.escape(label)}", f"\n{label}", ai_response)

    ai_response = re.sub(r"\nStory:", "\n\nStory:", ai_response)
    ai_response = re.sub(r"\nObjective:", "\n\nObjective:", ai_response)
    ai_response = re.sub(r"\nROLL_REQUEST:", "\n\nROLL_REQUEST:", ai_response)
    ai_response = re.sub(r"\nChoices:", "\n\nChoices:", ai_response)
    ai_response = re.sub(r"ROLL_REQUEST:\s*YES\s*CHECK_TYPE:", "ROLL_REQUEST: YES\nCHECK_TYPE:", ai_response)
    ai_response = re.sub(r"ROLL_REQUEST:\s*NO\s*Choices:", "ROLL_REQUEST: NO\n\nChoices:", ai_response)

    return ai_response.strip()


def apply_ai_response_to_game_state(game_state: dict, ai_response: str) -> dict:
    """Update game_state with Location, Health, Inventory, and Objective from AI text."""
    if not ai_response or ai_response.startswith("Error:"):
        return game_state
    
    completed_match = re.search(r"GAME_COMPLETED:\s*YES", ai_response, re.IGNORECASE)

    if completed_match:
        game_state["game_completed"] = True

    ending_match = re.search(r"ENDING:\s*(.*?)(?=\n|$)", ai_response, re.IGNORECASE)

    if ending_match:
        game_state["ending"] = ending_match.group(1).strip()

    location_match = re.search(
        r"Location:\s*(.*?)(?=\n|Health:|Inventory:|Dice Roll:|Result:|Story:|Objective:|ROLL_REQUEST:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL,
    )
    if location_match and location_match.group(1).strip():
        game_state["location"] = location_match.group(1).strip()

    health_match = re.search(r"Health:\s*(\d+)", ai_response, re.IGNORECASE)
    if health_match:
        game_state["health"] = int(health_match.group(1))

    inventory_match = re.search(
        r"Inventory:\s*(.*?)(?=\n|Dice Roll:|Result:|Story:|Objective:|ROLL_REQUEST:|Choices:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL,
    )
    if inventory_match:
        inventory_text = inventory_match.group(1).strip()
        inventory_items = [item.strip() for item in inventory_text.split(",") if item.strip()]
        if inventory_items:
            game_state["inventory"] = inventory_items

    objective_match = re.search(
        r"Objective:\s*(.*?)(?=\n\s*ROLL_REQUEST:|\n\s*Choices:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL,
    )
    if objective_match and objective_match.group(1).strip():
        game_state["objective"] = objective_match.group(1).strip()

    return game_state
