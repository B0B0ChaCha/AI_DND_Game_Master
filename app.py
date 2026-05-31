import random
import re
import streamlit as st
from ai_service import get_ai_response, detect_roll_request
from game_state import (
    get_default_game_state,
    save_game_state,
    load_game_state,
    delete_save_file
)


# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI D&D-Style Game Master",
    page_icon="🎲",
    layout="centered"
)


# ---------------------------------------------------------
# Dice Logic
# ---------------------------------------------------------
def roll_d20():
    """
    Rolls a 20-sided dice and returns both the dice value
    and the outcome category.
    """

    roll = random.randint(1, 20)

    if roll <= 5:
        outcome = "Failure"
    elif roll <= 10:
        outcome = "Partial Success"
    elif roll <= 15:
        outcome = "Success"
    else:
        outcome = "Great Success"

    return roll, outcome

# ---------------------------------------------------------
# Check if player is dead
# ---------------------------------------------------------

def is_player_dead():
    """
    Returns True if the player's health is 0 or below.
    """

    return st.session_state.game_state.get("health", 100) <= 0


# ---------------------------------------------------------
# Game State Setup
# ---------------------------------------------------------
def create_starting_message(game_state):
    """
    Creates the first Game Master message using the current game state.
    """

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
"""


def initialize_new_game():
    """
    Starts a new game using the default game state.
    """

    game_state = get_default_game_state()
    starting_message = create_starting_message(game_state)

    game_state["messages"].append({
        "role": "game_master",
        "content": starting_message
    })

    st.session_state.game_state = game_state
    st.session_state.is_processing = False
    st.session_state.pending_action = None


def load_saved_game():
    """
    Loads the saved game state from save_data.json.
    If no save file exists, it loads the default game state.
    """

    game_state = load_game_state()

    if "messages" not in game_state:
        game_state["messages"] = []

    if "awaiting_roll" not in game_state:
        game_state["awaiting_roll"] = None

    if len(game_state["messages"]) == 0:
        starting_message = create_starting_message(game_state)
        game_state["messages"].append({
            "role": "game_master",
            "content": starting_message
        })

    st.session_state.game_state = game_state
    st.session_state.is_processing = False
    st.session_state.pending_action = None


def get_conversation_history():
    """
    Converts the current message history into a readable text format
    that can be sent to the AI model.
    """

    history = ""

    for message in st.session_state.game_state["messages"]:
        role = message["role"]
        content = message["content"]
        history += f"{role}: {content}\n\n"

    return history


def is_waiting_for_game_master():
    """
    Returns True if the latest message is from the player.
    This means the app is waiting for the Game Master response.
    """

    messages = st.session_state.game_state["messages"]

    if len(messages) == 0:
        return False

    return messages[-1]["role"] == "player"


def is_duplicate_player_action(player_action):
    """
    Checks whether the player is trying to submit the same action twice
    before the Game Master has responded.
    """

    messages = st.session_state.game_state["messages"]

    if len(messages) == 0:
        return False

    last_message = messages[-1]

    return (
        last_message["role"] == "player"
        and last_message["content"] == player_action
    )


def format_ai_response_for_display(ai_response):
    """
    Cleans up the AI response so important fields display on separate lines.
    This helps when the model compresses labels into one line.
    """

    if not ai_response:
        return ai_response

    # Put main state fields on separate lines if compressed.
    labels = [
        "Health:",
        "Inventory:",
        "Dice Roll:",
        "Result:",
        "Story:",
        "Objective:",
        "ROLL_REQUEST:",
        "CHECK_TYPE:",
        "DIFFICULTY:",
        "REASON:",
        "Choices:"
    ]

    for label in labels:
        ai_response = re.sub(rf"\s+{re.escape(label)}", f"\n{label}", ai_response)

    # Add a blank line before major sections.
    ai_response = re.sub(r"\nStory:", "\n\nStory:", ai_response)
    ai_response = re.sub(r"\nObjective:", "\n\nObjective:", ai_response)
    ai_response = re.sub(r"\nROLL_REQUEST:", "\n\nROLL_REQUEST:", ai_response)
    ai_response = re.sub(r"\nChoices:", "\n\nChoices:", ai_response)

    # Fix common compressed roll request blocks.
    ai_response = re.sub(
        r"ROLL_REQUEST:\s*YES\s*CHECK_TYPE:",
        "ROLL_REQUEST: YES\nCHECK_TYPE:",
        ai_response
    )
    ai_response = re.sub(
        r"ROLL_REQUEST:\s*NO\s*Choices:",
        "ROLL_REQUEST: NO\n\nChoices:",
        ai_response
    )

    return ai_response.strip()


def update_game_state_from_ai_response(ai_response):
    """
    Extracts Location, Health, Inventory, and Objective from the AI response
    and updates the stored game state used by the sidebar and save file.
    """

    if not ai_response or ai_response.startswith("Error:"):
        return

    # Location - stop if another label appears on the same line.
    location_match = re.search(
        r"Location:\s*(.*?)(?=\n|Health:|Inventory:|Dice Roll:|Result:|Story:|Objective:|ROLL_REQUEST:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL
    )
    if location_match:
        location = location_match.group(1).strip()
        if location:
            st.session_state.game_state["location"] = location

    # Health
    health_match = re.search(r"Health:\s*(\d+)", ai_response, re.IGNORECASE)
    if health_match:
        st.session_state.game_state["health"] = int(health_match.group(1))

    # Inventory - stop before next label.
    inventory_match = re.search(
        r"Inventory:\s*(.*?)(?=\n|Dice Roll:|Result:|Story:|Objective:|ROLL_REQUEST:|Choices:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL
    )
    if inventory_match:
        inventory_text = inventory_match.group(1).strip()
        if inventory_text:
            inventory_items = [
                item.strip()
                for item in inventory_text.split(",")
                if item.strip()
            ]

            if inventory_items:
                st.session_state.game_state["inventory"] = inventory_items

    # Objective - stop before roll request or choices.
    objective_match = re.search(
        r"Objective:\s*(.*?)(?=\n\s*ROLL_REQUEST:|\n\s*Choices:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL
    )
    if objective_match:
        objective = objective_match.group(1).strip()
        if objective:
            st.session_state.game_state["objective"] = objective


def submit_player_action(player_action, should_roll=False):
    """
    Handles the player's submitted action.
    If should_roll is True, the app rolls a D20 and sends the dice result to the AI.
    If should_roll is False, the action is treated as a normal story action.
    """

    if player_action.strip() == "":
        st.warning("Please enter an action first.")
        return

    if is_duplicate_player_action(player_action):
        st.warning("This action was already submitted. Please wait for the Game Master response.")
        return

    if should_roll:
        roll, outcome = roll_d20()
        dice_text = f"""
Dice roll:
{roll}

Outcome:
{outcome}
"""
    else:
        dice_text = """
Dice roll:
None

Outcome:
No dice roll
"""

    st.session_state.game_state["messages"].append({
        "role": "player",
        "content": player_action
    })

    conversation_history = get_conversation_history()

    ai_prompt = f"""
Player action:
{player_action}

{dice_text}

Current game state:
Player Name: {st.session_state.game_state["player_name"]}
Location: {st.session_state.game_state["location"]}
Health: {st.session_state.game_state["health"]}
Inventory: {", ".join(st.session_state.game_state["inventory"])}
Objective: {st.session_state.game_state["objective"]}

Instruction:
If Dice roll is None, narrate the action normally.
If the action has uncertain outcome and meaningful failure consequence, request a roll using ROLL_REQUEST: YES.
If the action does not need a roll, use ROLL_REQUEST: NO and provide choices.
If a dice roll is provided, narrate the result based on the dice roll and outcome.
Do not invent or change dice roll values.
Do not ignore the dice result when a dice roll is provided.
Always place Location, Health, Inventory, Dice Roll, Result, Story, Objective, and ROLL_REQUEST on separate lines.
"""

    ai_response = get_ai_response(conversation_history, ai_prompt)
    ai_response = format_ai_response_for_display(ai_response)

    update_game_state_from_ai_response(ai_response)

    roll_request = detect_roll_request(ai_response)
    st.session_state.game_state["awaiting_roll"] = roll_request

    st.session_state.game_state["messages"].append({
        "role": "game_master",
        "content": ai_response
    })


def queue_action(player_action, should_roll=False):
    """
    Stores the player's action and reruns the app immediately.
    The next rerun hides all choices and input before the AI call starts.
    """

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


def display_adventure_log():
    """
    Displays the full adventure log.
    """

    st.subheader("Adventure Log")

    for message in st.session_state.game_state["messages"]:
        if message["role"] == "player":
            st.markdown(f"**You:** {message['content']}")
        else:
            st.markdown("**Game Master:**")
            st.markdown(message["content"].replace("\n", "  \n"))

        st.divider()


def hide_interactive_ui():
    """
    Hides old buttons/forms while the Game Master is thinking.
    This prevents the player from clicking old greyed-out widgets during processing.
    """

    st.markdown(
        """
        <style>
        div.stButton {
            display: none !important;
        }

        div[data-testid="stForm"] {
            display: none !important;
        }

        div[data-testid="stTextInput"] {
            display: none !important;
        }

        div[data-testid="stCheckbox"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# Initialize Session State
# ---------------------------------------------------------
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

if "game_state" not in st.session_state:
    load_saved_game()


# ---------------------------------------------------------
# Process Pending Action Before Showing Any Interactive UI
# ---------------------------------------------------------
if st.session_state.pending_action is not None:
    hide_interactive_ui()

    pending_action = st.session_state.pending_action

    st.title("🎲 AI D&D-Style Game Master")
    st.write(
        "Type your action and let the AI Game Master decide when a dice roll is needed."
    )

    display_adventure_log()

    

    st.info("The Game Master is thinking. Please wait...")

    with st.spinner("Generating the next part of your adventure..."):
        submit_player_action(
            pending_action["player_action"],
            pending_action["should_roll"]
        )

    st.session_state.pending_action = None
    st.session_state.is_processing = False
    st.rerun()


# ---------------------------------------------------------
# Safety Stop If Waiting For Game Master
# ---------------------------------------------------------
if is_waiting_for_game_master():
    hide_interactive_ui()

    st.title("🎲 AI D&D-Style Game Master")
    st.warning("The Game Master is still thinking. Please wait...")

    display_adventure_log()

    st.stop()


# ---------------------------------------------------------
# App Title
# ---------------------------------------------------------
st.title("🎲 AI D&D-Style Game Master")
st.write(
    "Type your action and let the AI Game Master decide when a dice roll is needed."
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.header("Game Info")
    st.write("**Genre:** Fantasy tabletop adventure")
    st.write("**Role:** AI Game Master")
    st.write("**Dice System:** D20")
    st.write("**Goal:** Investigate the mysterious curse affecting the village")

    st.divider()

    st.subheader("Current Game State")
    st.write(f"**Player:** {st.session_state.game_state['player_name']}")
    st.write(f"**Location:** {st.session_state.game_state['location']}")
    st.write(f"**Health:** {st.session_state.game_state['health']}")
    st.write(f"**Inventory:** {', '.join(st.session_state.game_state['inventory'])}")
    st.write(f"**Objective:** {st.session_state.game_state['objective']}")

    st.divider()

    st.subheader("Dice Outcome Rules")
    st.write("1–5: Failure")
    st.write("6–10: Partial Success")
    st.write("11–15: Success")
    st.write("16–20: Great Success")

    st.divider()

    if st.session_state.game_state.get("awaiting_roll") is None:
        if st.button("Save Game"):
            save_game_state(st.session_state.game_state)
            st.success("Game saved successfully.")

        if st.button("Load Game"):
            load_saved_game()
            st.success("Game loaded successfully.")
            st.rerun()

        if st.button("Restart Game"):
            initialize_new_game()
            st.rerun()

        if st.button("Delete Save File"):
            delete_save_file()
            initialize_new_game()
            st.warning("Save file deleted. New game started.")
            st.rerun()
    else:
        st.info("Resolve the dice roll before using save/load controls.")

# ---------------------------------------------------------
# Game Over Screen
# ---------------------------------------------------------
if is_player_dead():
    st.error("💀 Game Over")
    st.write("Your health has reached 0. Your adventure has ended.")

    if st.button("Restart Adventure"):
        initialize_new_game()
        st.rerun()

    st.stop()

# ---------------------------------------------------------
# Display Conversation
# ---------------------------------------------------------
display_adventure_log()


# ---------------------------------------------------------
# Roll Button UI
# ---------------------------------------------------------
if st.session_state.game_state.get("awaiting_roll") is not None:
    roll_data = st.session_state.game_state["awaiting_roll"]

    st.subheader("🎲 Dice Roll Required")
    st.write("The Game Master has requested a D20 roll for this action.")

    st.write(f"**Check Type:** {roll_data['check_type']}")
    st.write(f"**Difficulty:** {roll_data['difficulty']}")
    st.write(f"**Reason:** {roll_data['reason']}")

    if st.button("Roll D20"):
        roll, outcome = roll_d20()

        roll_action = f"""
The player rolled a D20.

Check Type: {roll_data['check_type']}
Difficulty: {roll_data['difficulty']}
Reason: {roll_data['reason']}
Dice Roll: {roll}
Outcome: {outcome}

Narrate the result based on this dice roll.
Do not ask for another roll immediately unless a new risky action happens after this result.
"""

        st.session_state.game_state["awaiting_roll"] = None
        queue_action(roll_action, should_roll=False)

    st.stop()


# ---------------------------------------------------------
# Choice Buttons
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Custom Player Input
# ---------------------------------------------------------
st.subheader("Your Action")

with st.form("player_action_form"):
    user_input = st.text_input(
        "What do you want to do?",
        placeholder="Example: I try to persuade the guard to let me enter."
    )

    submitted = st.form_submit_button("Submit Action")

    if submitted:
        queue_action(user_input, should_roll=False)
