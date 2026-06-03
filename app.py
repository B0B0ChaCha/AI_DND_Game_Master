"""Main Streamlit entry point for the AI D&D-style adventure game.

This file intentionally stays small. Feature work should usually go into:
- ui_components.py for Streamlit UI sections
- game_controller.py for turn-processing logic
- session_manager.py for session state
- response_parser.py for AI response cleanup/parsing
- ai_service.py for model/API calls
- game_state.py for save data structure and JSON loading
"""

import streamlit as st

from constants import PAGE_ICON, PAGE_TITLE
from game_controller import submit_player_action
from session_manager import ensure_session_state, is_player_dead, is_waiting_for_game_master
from ui_components import (
    display_adventure_log,
    hide_interactive_ui,
    render_choice_buttons,
    render_game_over_screen,
    render_game_completed_screen,
    render_header,
    render_player_input_form,
    render_roll_ui,
    render_sidebar,
)


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")


def process_pending_action() -> None:
    """Process queued action before showing any clickable controls."""
    if st.session_state.pending_action is None:
        return

    hide_interactive_ui()
    pending_action = st.session_state.pending_action

    render_header()
    display_adventure_log()
    st.info("The Game Master is thinking. Please wait...")

    with st.spinner("Generating the next part of your adventure..."):
        submit_player_action(pending_action["player_action"], pending_action["should_roll"])

    st.session_state.pending_action = None
    st.session_state.is_processing = False
    st.rerun()


def stop_if_waiting_for_game_master() -> None:
    """Safety stop to prevent stale widgets from accepting more input."""
    if not is_waiting_for_game_master():
        return

    hide_interactive_ui()
    render_header()
    st.warning("The Game Master is still thinking. Please wait...")
    display_adventure_log()
    st.stop()


def main() -> None:
    """Run the Streamlit app."""
    configure_page()
    ensure_session_state()

    process_pending_action()
    stop_if_waiting_for_game_master()

    render_header()
    render_sidebar()

    if st.session_state.game_state.get("game_completed"):
        render_game_completed_screen()

    if is_player_dead():
        render_game_over_screen()

    display_adventure_log()

    if st.session_state.game_state.get("awaiting_roll") is not None:
        render_roll_ui()

    render_choice_buttons()
    render_player_input_form()


if __name__ == "__main__":
    main()
