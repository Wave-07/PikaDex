# ⚡ PikaDex Bot

**PikaDex** is a feature-rich, interactive Telegram bot designed for Pokémon enthusiasts and community groups. Built with `python-telegram-bot`, it provides deep insights into Pokémon stats, movesets, weaknesses, and natures, alongside built-in moderation tools like temporary message pinning. 

It also includes a lightweight Flask web server, making it perfectly optimized for deployment on platforms like Render or Heroku.

## ✨ Features

* 📖 **Comprehensive Pokédex (`/data`)**: Get detailed stats, EV yields, catch rates, hidden abilities, and shiny sprites for any Pokémon.
* ⚔️ **Interactive Movesets**: Browse a Pokémon's moveset filtered by Level-Up, Egg, TMs, or Tutor moves using intuitive inline pagination.
* 🧬 **Evolutions & Weaknesses**: Easily check type weaknesses, multipliers (e.g., 4x fatal, immune), and explore evolutionary lines.
* 🎯 **Smart Nature Suggestions (`/bestnat`)**: Calculates and recommends the best Natures for a Pokémon based on its base stats.
* 🔍 **Fuzzy Search**: Misspelled a Pokémon's name? PikaDex will provide clickable suggestions.
* 📖 **Quick Move & Nature Lookup**: Simply type a move name (e.g., "Thunderbolt") or a nature (e.g., "Adamant") in the chat to instantly get its stats and effects.
* 📌 **Timed Auto-Pinning (`/hpin`, `/ppin`, `/spin`)**: Reply to specific game-bot messages to pin them for a set duration (2-20 minutes). PikaDex will automatically unpin them when the timer ends.
* ♻️ **Auto-Restart**: Automatically saves sessions and restarts every 12 hours to manage memory efficiently.

---

## 🛠️ Commands

| Command | Description |
| :--- | :--- |
| `/start` | Check if the bot is alive and get basic usage instructions. |
| `/data <pokemon>` | Fetch full Pokédex entry for a specific Pokémon. |
| `/bestnat <pokemon>`| Get the best recommended natures for a Pokémon. |
| `/hpin` | Reply to Hexa bot to temporarily pin the message. |
| `/ppin` | Reply to P-Bot to temporarily pin the message. |
| `/spin` | Reply to Sexa bot to temporarily pin the message. |

*Note: You can also send the name of any Move or Nature as a standard text message to get its details.*

---

## 🚀 Setup & Installation

### 1. Prerequisites
* Python 3.8 or higher.
* A Telegram Bot Token from [@BotFather](https://t.me/BotFather).
* A `pokedex.json` file containing the Pokémon data in the root directory.

### 2. Clone the Repository
```bash
git clone [https://github.com/yourusername/PikaDex.git](https://github.com/yourusername/PikaDex.git)
cd PikaDex

3. Install Dependencies
Create a requirements.txt file containing the following:
python-telegram-bot[job-queue]
flask

Then install them via pip:
pip install -r requirements.txt

4. Environment Variables
You must set your Telegram Bot Token as an environment variable before running the bot.
Windows (CMD):
set BOT_TOKEN=your_bot_token_here

Linux/Mac:
export BOT_TOKEN="your_bot_token_here"

5. Run the Bot
python bot.py

(Note: Rename your main script to bot.py or adjust the command accordingly).
☁️ Deployment (Render / Heroku)
This bot includes a background Flask server (0.0.0.0:$PORT), making it incredibly easy to host on cloud platforms that require web-service port binding (like Render) to keep the application alive.
 * Create a new Web Service on Render.
 * Set your Build Command to: pip install -r requirements.txt
 * Set your Start Command to: python bot.py
 * In the Environment Variables section on your dashboard, add:
   * BOT_TOKEN = your_telegram_bot_token
📂 Required Database Structure
To function properly, the bot expects a pokedex.json file in the root directory with the following structure:
{
  "pokemon": {
    "pikachu": {
      "id": 25,
      "name": "pikachu",
      "types": ["electric"],
      "abilities": ["static"],
      "hidden_ability": "lightning-rod",
      "stats": {"hp": 35, "attack": 55, "defense": 40, "special-attack": 50, "special-defense": 50, "speed": 90},
      "moves": [{"n": "thunder-shock", "m": "level-up", "l": 1}],
      "evolution": ["pichu", "pikachu", "raichu"]
    }
  },
  "moves": {
    "thunder-shock": {
      "t": "electric",
      "p": 40,
      "a": 100,
      "pp": 30,
      "d": "A jolt of electricity crashes down on the target to inflict damage.",
      "c": "special"
    }
  },
  "types": {
    "electric": {
      "ground": 0.0,
      "water": 2.0
    }
  }
}

👨‍💻 Author
PikaDex by @WaveAce on Telegram.

