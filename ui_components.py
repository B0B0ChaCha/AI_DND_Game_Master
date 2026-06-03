"""Reusable Streamlit UI sections for the adventure app."""

from datetime import datetime

import streamlit as st

from constants import APP_DESCRIPTION, APP_TITLE, DICE_OUTCOME_RULES
from game_controller import create_roll_resolution_action, queue_action
from game_state import convert_game_state_to_json, load_game_state_from_uploaded_file
from session_manager import initialize_loaded_game, initialize_new_game


def render_header() -> None:
    """Render the app title and description."""
    st.title(APP_TITLE)
    st.write(APP_DESCRIPTION)


def display_adventure_log() -> None:
    """Display the full adventure log."""
    st.subheader("Adventure Log")

    for message in st.session_state.game_state["messages"]:
        if message["role"] == "player":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown("**Game Master:**")
            st.markdown(message["content"].replace("\n", "  \n"))

        st.divider()


def hide_interactive_ui() -> None:
    """Hide interactive widgets while the Game Master is processing."""
    st.markdown(
        """
        <style>
        div.stButton,
        div.stDownloadButton,
        div[data-testid="stForm"],
        div[data-testid="stTextInput"],
        div[data-testid="stCheckbox"],
        div[data-testid="stFileUploader"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Render game info, state summary, save/load, and restart controls."""
    game_state = st.session_state.game_state

    with st.sidebar:
        st.header("Game Info")
        st.write("**Genre:** Fantasy tabletop adventure")
        st.write("**Role:** AI Game Master")
        st.write("**Dice System:** D20")
        st.write("**Goal:** Investigate the mysterious curse affecting the village")

        st.divider()
        st.subheader("Current Game State")
        st.write(f"**Player:** {game_state['player_name']}")
        st.write(f"**Location:** {game_state['location']}")
        st.write(f"**Health:** {game_state['health']}")
        st.write(f"**Inventory:** {', '.join(game_state['inventory'])}")
        st.write(f"**Objective:** {game_state['objective']}")

        save_metadata = game_state.get("save_metadata", {})
        if save_metadata.get("saved_at"):
            st.write(f"**Loaded Save Time:** {save_metadata['saved_at']}")

        st.divider()
        st.subheader("Dice Outcome Rules")
        for rule in DICE_OUTCOME_RULES:
            st.write(rule)

        st.divider()
        render_save_load_controls()


def render_save_load_controls() -> None:
    """Render save/load controls only when no dice roll is pending."""
    game_state = st.session_state.game_state

    if game_state.get("awaiting_roll") is not None:
        st.info("Resolve the dice roll before using save/load controls.")
        return

    save_json = convert_game_state_to_json(game_state)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_location = game_state["location"].replace(" ", "_").replace("/", "_")

    st.download_button(
        label="Download Save File",
        data=save_json,
        file_name=f"ai_dnd_save_{safe_location}_{timestamp}.json",
        mime="application/json",
    )

    uploaded_save_file = st.file_uploader("Choose Save File", type=["json"], key="save_file_uploader")

    if uploaded_save_file is not None and st.button("Load Selected Save File"):
        loaded_game_state = load_game_state_from_uploaded_file(uploaded_save_file)
        message_count = len(loaded_game_state.get("messages", []))
        initialize_loaded_game(loaded_game_state)
        st.success(f"Save file loaded successfully. Restored {message_count} story messages.")
        st.rerun()

    if st.button("Restart Game"):
        initialize_new_game()
        st.rerun()


def render_game_over_screen() -> None:
    """Render final game-over controls."""
    st.error("💀 Game Over")
    st.write("Your health has reached 0. Your adventure has ended.")

    if st.button("Restart Adventure"):
        initialize_new_game()
        st.rerun()

    st.stop()


def render_roll_ui() -> None:
    """Render the required D20 roll UI."""
    roll_data = st.session_state.game_state["awaiting_roll"]

    st.subheader("🎲 Dice Roll Required")
    st.write("The Game Master has requested a D20 roll for this action.")
    st.write(f"**Check Type:** {roll_data['check_type']}")
    st.write(f"**Difficulty:** {roll_data['difficulty']}")
    st.write(f"**Reason:** {roll_data['reason']}")

    if st.button("Roll D20"):
        st.session_state.game_state["awaiting_roll"] = None
        queue_action(create_roll_resolution_action(roll_data), should_roll=False)

    st.stop()


def render_choice_buttons() -> None:
    """Render the three generic latest-choice buttons."""
    st.subheader("Choose from the latest Game Master options")

    choice_col1, choice_col2, choice_col3 = st.columns(3)

    with choice_col1:
        if st.button("Choice 1"):
            queue_action("I choose option 1.", should_roll=False)

    with choice_col2:
        if st.button("Choice 2"):
            queue_action("I choose option 2.", should_roll=False)

    with choice_col3:
        if st.button("Choice 3"):
            queue_action("I choose option 3.", should_roll=False)


def render_player_input_form() -> None:
    """Render custom player action input."""
    st.subheader("Your Action")

    with st.form("player_action_form"):
        user_input = st.text_input(
            "What do you want to do?",
            placeholder="Example: I try to persuade the guard to let me enter.",
        )

        submitted = st.form_submit_button("Submit Action")
        if submitted:
            queue_action(user_input, should_roll=False)
