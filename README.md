# SETUP
Language: Python
Frontend: Streamlit
AI API: Google Gemini
Environment: .env file

# AI Text Adventure Game Master (Something like DND)

## Design Decision

The project uses a D&D-style fantasy Game Master system because it gives the AI a clear role and purpose. Instead of acting as a general chatbot, the AI must narrate a fantasy adventure, respond to player actions, control NPCs, and keep the story within the selected world. The theme is restricted to a fantasy village, forest, ruins, and dungeon so that the AI is less likely to go off-topic or hallucinate unrelated scenarios.

When players want to take a break, they can just save the game (left side panel) to download the data JSON file (saved with data, time stamp). This allows them to keep track and continue from the session they were in.

## 1. Project Title and Description
AI Text Adventure Game Master is a text-based adventure game where an AI narrates the story and responds to the player's actions. It is designed for players who enjoy interactive story games.

## 2. Problem Statement
Traditional text adventure games usually have fixed responses and limited choices. This project uses AI to make the story more flexible, allowing players to type their own actions and receive dynamic responses.

## 3. Technology Stack
- Python
- Streamlit
- Google Gemini API
- python-dotenv
- GitHub

## 4. Setup Instructions
1. Clone the repository.
2. Install dependencies using `pip install -r requirements.txt`.
3. Copy `.env.example` and rename it to `.env`.
4. Add your Gemini API key into the `.env` file.
5. Run the app using `streamlit run app.py`.

## 5. Usage Examples
Example 1:
User input: I walk into the forest.
AI output: The Game Master describes the forest and updates the player's location.

Example 2:
User input: I check my inventory.
AI output: The Game Master lists the player's current items and asks what the player wants to do next.

## 6. Known Limitations
- The AI may sometimes forget small details if the conversation becomes too long.
- The game world is limited to the rules described in the system prompt.

## 7. Future Improvements
- Add multiple selectable game worlds.
- Save and load player progress.
- Add a visual map or inventory panel.
- Win condition

## 9. Streamlit cloud
https://aidndgamemaster.streamlit.app/

## 9. Test Cases

| Test Case | Input | Expected Output | Actual Output |
|---|---|---|---|
| TC01 - Start Adventure | I walk into the forest and look around. | AI continues the story, describes the forest, and asks for the next action. | Passed - AI described the forest and continued the adventure. |
| TC02 - Inventory Check | I check my inventory. | AI shows the player's current inventory. | Passed - AI listed the player's items. |
| TC03 - Use Item | I use the old map to find the tower. | AI uses the map as part of the story and gives a clue or direction. | Passed - AI gave a direction toward the tower. |
| TC04 - Combat Action | I attack the creature with my small knife. | AI handles combat and updates the story or health. | Passed - AI described the combat result and continued the story. |
| TC05 - Out-of-Scope Input | What is the capital of Japan? | AI should not answer like a normal chatbot and should guide the player back to the adventure. | Passed - AI redirected the player back to the game. |
| TC06 - Missing API Key | Remove or rename GEMINI_API_KEY in `.env`, then submit any input. | App shows a clear error message instead of crashing. | Passed - App displayed missing API key error. |


