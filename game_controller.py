"""Turn-processing logic that connects Streamlit state, dice, NPC memory, and AI responses."""

import streamlit as st

from ai_service import detect_roll_request, get_ai_response
from dice import roll_d20
from prompts import build_ai_prompt
from response_parser import (
    apply_ai_response_to_game_state,
    format_ai_response_for_display,
    update_npc_memory_from_ai_response,
)
from session_manager import (
    get_conversation_history,
    is_duplicate_player_action,
    is_waiting_for_game_master,
)


def build_dice_text(should_roll: bool) -> str:
    """Return dice result text to send to the AI."""
    if should_roll:
        roll, outcome = roll_d20()
        return f"""
            Dice roll:
            {roll}

            Outcome:
            {outcome}
            """.strip()

    return """
        Dice roll:
        None

        Outcome:
        No dice roll
        """.strip()


def submit_player_action(player_action: str, should_roll: bool = False) -> None:
    """Submit the player's action, call the AI, and update game state."""

# DEBUG
    if player_action.strip() == "":
        st.warning("Please enter an action first.")
        return

    if handle_debug_code(player_action):
        return

    if is_duplicate_player_action(player_action):
        st.warning("This action was already submitted. Please wait for the Game Master response.")
        return
# DEBUG

    if player_action.strip() == "":
        st.warning("Please enter an action first.")
        return

    if is_duplicate_player_action(player_action):
        st.warning("This action was already submitted. Please wait for the Game Master response.")
        return

    st.session_state.game_state["messages"].append({
        "role": "player",
        "content": player_action
    })

    conversation_history = get_conversation_history()

    ai_prompt = build_ai_prompt(
        st.session_state.game_state,
        player_action,
        build_dice_text(should_roll)
    )

    ai_response = get_ai_response(conversation_history, ai_prompt)
    ai_response = format_ai_response_for_display(ai_response)

    st.session_state.game_state = apply_ai_response_to_game_state(
        st.session_state.game_state,
        ai_response
    )

    update_npc_memory_from_ai_response(
        st.session_state.game_state,
        ai_response
    )

    st.session_state.game_state["awaiting_roll"] = detect_roll_request(ai_response)

    st.session_state.game_state["messages"].append({
        "role": "game_master",
        "content": ai_response
    })


def queue_action(player_action: str, should_roll: bool = False) -> None:
    """Queue action so old UI disappears before the AI call starts."""
    if st.session_state.is_processing:
        return

    if st.session_state.pending_action is not None:
        return

    if is_waiting_for_game_master():
        return

    if player_action.strip() == "":
        st.warning("Please enter an action first.")
        return

    st.session_state.pending_action = {
        "player_action": player_action,
        "should_roll": should_roll
    }

    st.session_state.is_processing = True
    st.rerun()


def create_roll_resolution_action(roll_data: dict) -> str:
    """Create the action text that resolves a pending D20 roll."""
    roll, outcome = roll_d20()

    return f"""
        The player rolled a D20.

        Check Type: {roll_data['check_type']}
        Difficulty: {roll_data['difficulty']}
        Reason: {roll_data['reason']}
        Dice Roll: {roll}
        Outcome: {outcome}

        Narrate the result based on this dice roll.
        Do not ask for another roll immediately unless a new risky action happens after this result.
        """.strip()


#DEBUG FUNCTIONS
def handle_debug_code(player_action: str) -> bool:
    command = player_action.strip().lower()

    if command == "/debug win":
        st.session_state.game_state["game_completed"] = True
        st.session_state.game_state["ending"] = "Debug win condition triggered."
        return True

    if command == "/debug lose":
        st.session_state.game_state["health"] = 0
        st.session_state.game_state["ending"] = "Debug lose condition triggered."
        return True

    return False
