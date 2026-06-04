def get_attitude_from_relationship(relationship):
    if relationship <= -30:
        return "hostile"
    elif relationship >= 30:
        return "friendly"
    return "neutral"


def create_or_update_npc(game_state, name, role="Unknown"):
    npcs = game_state.setdefault("npcs", {})

    if name not in npcs:
        npcs[name] = {
            "name": name,
            "role": role,
            "relationship": 0,
            "attitude": "neutral",
            "memories": []
        }

    if role != "Unknown":
        npcs[name]["role"] = role


def add_npc_memory(game_state, name, memory, relationship_change=0, role="Unknown"):
    create_or_update_npc(game_state, name, role)

    npc = game_state["npcs"][name]
    npc["relationship"] += relationship_change
    npc["attitude"] = get_attitude_from_relationship(npc["relationship"])

    if memory and memory not in npc["memories"]:
        npc["memories"].append(memory)


def format_npc_memory_for_prompt(game_state):
    npcs = game_state.get("npcs", {})

    if not npcs:
        return "No known NPCs yet."

    text = ""

    for npc in npcs.values():
        text += f"""
NPC: {npc['name']}
Role: {npc['role']}
Relationship: {npc['relationship']}
Attitude: {npc['attitude']}
Memories:
"""

        for memory in npc["memories"][-5:]:
            text += f"- {memory}\n"

        text += "\n"

    return text.strip()