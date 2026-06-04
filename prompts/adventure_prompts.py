from services.npc_memory import format_npc_memory_for_prompt

def create_starting_message(game_state: dict) -> str:
    """Create the first Game Master message for a new adventure."""
    inventory_text = ", ".join(game_state["inventory"])

    return f"""
Location: {game_state["location"]}
Health: {game_state["health"]}
Inventory: {inventory_text}
Dice Roll: None
Result: None

Story:
You arrive at the entrance of a quiet village surrounded by mist. The village feels strangely empty, and a cold wind moves through the trees. In the distance, you see an old notice board, a narrow forest path, and a small stone house with candlelight glowing inside.

Objective:
{game_state["objective"]}

ROLL_REQUEST: NO

Choices:
1. Walk to the stone house.
2. Inspect the notice board.
3. Follow the forest path.

Or type your own action.
""".strip()


def create_resume_message(game_state: dict) -> str:
    """Create a safe message when an older save has no story log."""
    return f"""
Location: {game_state["location"]}
Health: {game_state["health"]}
Inventory: {", ".join(game_state["inventory"])}
Dice Roll: None
Result: Loaded Save

Story:
Your saved adventure has been loaded, but this save file does not contain the previous story log.

Objective:
{game_state["objective"]}

ROLL_REQUEST: NO

Choices:
1. Continue exploring the area.
2. Check your surroundings.
3. Review your objective.

Or type your own action.
""".strip()


def build_ai_prompt(game_state: dict, player_action: str, dice_text: str) -> str:
    """Build the current turn prompt sent to the AI service."""

    npc_memory_text = format_npc_memory_for_prompt(game_state)
    return f"""
Player action:
{player_action}

{dice_text}

Current game state:
Player Name: {game_state["player_name"]}
Location: {game_state["location"]}
Health: {game_state["health"]}
Inventory: {", ".join(game_state["inventory"])}
Objective: {game_state["objective"]}

Known NPC Memory:
{npc_memory_text}

Instruction:
Use the dice result if one is provided.
If Dice roll is None, decide whether the action needs a roll.
Use Known NPC Memory when the player meets or talks to an existing NPC.

NPC OUTPUT REQUIREMENT:
If the player talks to, greets, meets, trades with, attacks, helps, threatens, or steals from any person, you MUST include NPC_CREATED if that NPC is not already in Known NPC Memory.

If the interaction changes the NPC's opinion of the player, you MUST include NPC_MEMORY_UPDATE.

For this turn, the player interacted with:
{player_action}

Do not skip NPC_CREATED for shopkeepers, guards, merchants, villagers, elders, strangers, or named characters.
""".strip()
