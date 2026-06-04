import streamlit as st

from models.game_state import get_default_game_state, normalize_game_state
from prompts.adventure_prompts import create_resume_message, create_starting_message


def initialize_new_game() -> None:
    """Start a new game using the default state."""
    game_state = get_default_game_state()
    game_state["messages"].append({"role": "game_master", "content": create_starting_message(game_state)})

    st.session_state.game_state = game_state
    st.session_state.is_processing = False
    st.session_state.pending_action = None


def initialize_loaded_game(game_state: dict) -> None:
    """Load a normalized save into Streamlit session state."""
    game_state = normalize_game_state(game_state)

    if len(game_state["messages"]) == 0:
        game_state["messages"].append({"role": "game_master", "content": create_resume_message(game_state)})

    st.session_state.game_state = game_state
    st.session_state.is_processing = False
    st.session_state.pending_action = None


def ensure_session_state() -> None:
    """Create required Streamlit session keys once."""
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False

    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None

    if "game_state" not in st.session_state:
        initialize_new_game()


def get_conversation_history() -> str:
    """Convert message history into plain text for the AI prompt."""
    return "\n\n".join(
        f"{message['role']}: {message['content']}"
        for message in st.session_state.game_state["messages"]
    )


def is_player_dead() -> bool:
    """Return True when the player has no health remaining."""
    return st.session_state.game_state.get("health", 100) <= 0


def is_waiting_for_game_master() -> bool:
    """Return True if the latest stored message is from the player."""
    messages = st.session_state.game_state["messages"]
    return bool(messages) and messages[-1]["role"] == "player"


def is_duplicate_player_action(player_action: str) -> bool:
    """Prevent repeat submission before the Game Master replies."""
    messages = st.session_state.game_state["messages"]
    if not messages:
        return False

    last_message = messages[-1]
    return last_message["role"] == "player" and last_message["content"] == player_action
