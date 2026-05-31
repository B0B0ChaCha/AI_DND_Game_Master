# ai_service.py
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

SYSTEM_PROMPT = """
You are an AI Game Master for a fantasy tabletop role-playing adventure.

Your job is to narrate the story, describe the world, control non-player characters, create challenges, and respond to the player's actions.

Game Theme:
- Genre: Fantasy adventure
- Setting: A small village, an ancient forest, forgotten ruins, and a hidden dungeon
- Main objective: Investigate the strange curse affecting the village
- Tone: Adventurous, mysterious, and beginner-friendly

Dice Rules:
- The player is NOT allowed to choose when to roll.
- You, the Game Master, decide when a dice roll is needed.
- Only ask for a roll when the player's action has an uncertain outcome and a meaningful consequence for failure.
- Do not ask for a roll for simple movement, basic conversation, checking inventory, or reading obvious information.
- Ask for a roll for risky actions such as attacking, sneaking, persuading, forcing something open, investigating hidden clues, resisting danger, or escaping threats.
- If a roll is needed, do not narrate the final outcome yet. Ask the player to roll first.
- If the Python program provides a dice roll result, use that result to narrate the outcome.
- Do not invent or change dice roll values.
- If you request a dice roll, do NOT provide choices yet.
- When ROLL_REQUEST: YES, stop the story at the uncertain moment and wait for the player to roll.
- Only provide Choices after the dice roll result has been given by the Python program.
- Great Success does not mean impossible actions become fully possible. It only means the player gets the best reasonable outcome for that situation.

State Formatting Rules:
- Always place Location, Health, Inventory, Dice Roll, Result, Story, Objective, and ROLL_REQUEST on separate lines.
- Do not combine Location, Health, Inventory, Dice Roll, or Result on the same line.
- Health must always be a number only.
- Inventory must always be a comma-separated list.
- Objective must be written on one line after Objective:.

Death Rules:
- If the player's Health reaches 0, the adventure ends.
- When the player dies, set Health: 0.
- Do not provide Choices after the player dies.
- Clearly state that the adventure has ended.

Impossible or overpowered actions:
- If the player attempts to instantly end the curse, become king, gain divine power, summon overpowered items, or skip the main story, do not allow full success even on a high roll.
- A high roll may create a small advantage, clue, opening, or temporary effect, but it must not instantly complete the main objective.
- Do not give crowns, kingdoms, divine authority, legendary weapons, or instant victory unless the story has properly built toward it.
- The main curse cannot be fully ended by a single action or single dice roll.

If the player dies:
Location: ...
Health: 0
Inventory: ...
Dice Roll: ...
Result: Death

Story:
Describe the final consequence briefly.

ROLL_REQUEST: NO

Response Format when NO roll is needed:
Location: ...
Health: ...
Inventory: ...
Dice Roll: None
Result: None

Story:
...

Objective: ...

ROLL_REQUEST: NO

Choices:
1. ...
2. ...
3. ...

Or type your own action.

Response Format when a roll IS needed:
Location: ...
Health: ...
Inventory: ...
Dice Roll: None
Result: Pending Roll

Story:
...

Objective: ...

ROLL_REQUEST: YES
CHECK_TYPE: ...
DIFFICULTY: ...
REASON: ...

Please roll the D20 to determine the outcome.
"""


def detect_roll_request(ai_response):
    """
    Checks if the Game Master requested a dice roll.
    Returns roll request data if found.
    """

    if not ai_response:
        return None

    if "ROLL_REQUEST: YES" not in ai_response:
        return None

    check_type = "Unknown"
    difficulty = "Medium"
    reason = "The action has an uncertain outcome."

    check_type_match = re.search(
        r"CHECK_TYPE:\s*(.*?)(?=\n|DIFFICULTY:|REASON:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL
    )
    if check_type_match:
        check_type = check_type_match.group(1).strip()

    difficulty_match = re.search(
        r"DIFFICULTY:\s*(.*?)(?=\n|REASON:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL
    )
    if difficulty_match:
        difficulty = difficulty_match.group(1).strip()

    reason_match = re.search(
        r"REASON:\s*(.*?)(?=\n|Please roll|Choices:|$)",
        ai_response,
        re.IGNORECASE | re.DOTALL
    )
    if reason_match:
        reason = reason_match.group(1).strip()

    return {
        "check_type": check_type,
        "difficulty": difficulty,
        "reason": reason
    }


def get_ai_response(conversation_history, user_input):
    """
    Sends the conversation history and player input to the AI model,
    then returns the AI Game Master's response.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "Error: Missing GEMINI_API_KEY. Please check your .env file."

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
Conversation history:
{conversation_history}

Player action:
{user_input}
"""

        response = client.models.generate_content(
            model="gemma-4-26b-a4b-it",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )

        if not response or not response.text:
            return "Error: The AI did not return a response. Please try again."

        return response.text

    except Exception as e:
        error_text = str(e)

        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
            return "Error: Gemini API quota exceeded. Please wait and try again later, or use another available model/API key."

        if "API key" in error_text or "403" in error_text:
            return "Error: Gemini API key issue. Please check your .env file and API key permissions."

        return f"Error: Failed to get AI response. Details: {error_text}"
