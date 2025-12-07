import logging
import requests
import difflib
import asyncio
import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    CallbackQueryHandler, MessageHandler, filters
)

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN") 

# --- BOT IDs (FILL THESE IN) ---
HEXA_BOT_ID = 572621020
P_BOT_ID = 7955369039

# --- LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- GLOBAL CACHE ---
POKEMON_NAMES = []
TYPE_EMOJIS = {
    'normal': '🔘', 'fire': '🔥', 'water': '💧', 'electric': '⚡',
    'grass': '🌱', 'ice': '❄️', 'fighting': '🥊', 'poison': '☣',
    'ground': '⛰', 'flying': '🪽', 'psychic': '🔮', 'bug': '🪲',
    'rock': '🪨', 'ghost': '👁‍🗨', 'dragon': '🐉', 'dark': '🌑',
    'steel': '🔩', 'fairy': '🧚‍♀', 'stellar': '🪄'
}

# --- NATURE DATA ---
NATURE_DATA = {
    'hardy': {'up': 'None', 'down': 'None'},
    'lonely': {'up': 'Attack', 'down': 'Defense'},
    'brave': {'up': 'Attack', 'down': 'Speed'},
    'adamant': {'up': 'Attack', 'down': 'Sp. Atk'},
    'naughty': {'up': 'Attack', 'down': 'Sp. Def'},
    'bold': {'up': 'Defense', 'down': 'Attack'},
    'docile': {'up': 'None', 'down': 'None'},
    'relaxed': {'up': 'Defense', 'down': 'Speed'},
    'impish': {'up': 'Defense', 'down': 'Sp. Atk'},
    'lax': {'up': 'Defense', 'down': 'Sp. Def'},
    'timid': {'up': 'Speed', 'down': 'Attack'},
    'hasty': {'up': 'Speed', 'down': 'Defense'},
    'serious': {'up': 'None', 'down': 'None'},
    'jolly': {'up': 'Speed', 'down': 'Sp. Atk'},
    'naive': {'up': 'Speed', 'down': 'Sp. Def'},
    'modest': {'up': 'Sp. Atk', 'down': 'Attack'},
    'mild': {'up': 'Sp. Atk', 'down': 'Defense'},
    'quiet': {'up': 'Sp. Atk', 'down': 'Speed'},
    'bashful': {'up': 'None', 'down': 'None'},
    'rash': {'up': 'Sp. Atk', 'down': 'Sp. Def'},
    'calm': {'up': 'Sp. Def', 'down': 'Attack'},
    'gentle': {'up': 'Sp. Def', 'down': 'Defense'},
    'sassy': {'up': 'Sp. Def', 'down': 'Speed'},
    'careful': {'up': 'Sp. Def', 'down': 'Sp. Atk'},
    'quirky': {'up': 'None', 'down': 'None'}
}

# --- CUSTOM TM MAPPING (SCARLET & VIOLET) ---
CUSTOM_TM_MAP = {
    "Take Down": "001", "Charm": "002", "Fake Tears": "003", "Agility": "004",
    "Mud Slap": "005", "Scary Face": "006", "Protect": "007", "Fire Fang": "008",
    "Thunder Fang": "009", "Ice Fang": "010", "Water Pulse": "011", "Low Kick": "012",
    "Acid Spray": "013", "Acrobatics": "014", "Struggle Bug": "015", "Psybeam": "016",
    "Confuse Ray": "017", "Thief": "018", "Disarming Voice": "019", "Trailblaze": "020",
    "Pounce": "021", "Chilling Water": "022", "Charge Beam": "023", "Fire Spin": "024",
    "Facade": "025", "Poison Tail": "026", "Aerial Ace": "027", "Bulldoze": "028",
    "Hex": "029", "Snarl": "030", "Metal Claw": "031", "Swift": "032",
    "Magical Leaf": "033", "Icy Wind": "034", "Mud Shot": "035", "Rock Tomb": "036",
    "Draining Kiss": "037", "Flame Charge": "038", "Low Sweep": "039", "Air Cutter": "040",
    "Stored Power": "041", "Night Shade": "042", "Fling": "043", "Dragon Tail": "044",
    "Venoshock": "045", "Avalanche": "046", "Endure": "047", "Volt Switch": "048",
    "Sunny Day": "049", "Rain Dance": "050", "Sandstorm": "051", "Snowscape": "052",
    "Smart Strike": "053", "Psyshock": "054", "Dig": "055", "Bullet Seed": "056",
    "False Swipe": "057", "Brick Break": "058", "Zen Headbutt": "059", "U Turn": "060",
    "Shadow Claw": "061", "Foul Play": "062", "Psychic Fangs": "063", "Bulk Up": "064",
    "Air Slash": "065", "Body Slam": "066", "Fire Punch": "067", "Thunder Punch": "068",
    "Ice Punch": "069", "Sleep Talk": "070", "Seed Bomb": "071", "Electro Ball": "072",
    "Drain Punch": "073", "Reflect": "074", "Light Screen": "075", "Rock Blast": "076",
    "Waterfall": "077", "Dragon Claw": "078", "Dazzling Gleam": "079", "Metronome": "080",
    "Grass Knot": "081", "Thunder Wave": "082", "Poison Jab": "083", "Stomping Tantrum": "084",
    "Rest": "085", "Rock Slide": "086", "Taunt": "087", "Swords Dance": "088",
    "Body Press": "089", "Spikes": "090", "Toxic Spikes": "091", "Imprison": "092",
    "Flash Cannon": "093", "Dark Pulse": "094", "Leech Life": "095", "Eerie Impulse": "096",
    "Fly": "097", "Skill Swap": "098", "Iron Head": "099", "Dragon Dance": "100",
    "Power Gem": "101", "Gunk Shot": "102", "Substitute": "103", "Iron Defense": "104",
    "X Scissor": "105", "Drill Run": "106", "Will O Wisp": "107", "Crunch": "108",
    "Trick": "109", "Liquidation": "110", "Giga Drain": "111", "Aura Sphere": "112",
    "Tailwind": "113", "Shadow Ball": "114", "Dragon Pulse": "115", "Stealth Rock": "116",
    "Hyper Voice": "117", "Heat Wave": "118", "Energy Ball": "119", "Psychic": "120",
    "Heavy Slam": "121", "Encore": "122", "Surf": "123", "Ice Spinner": "124",
    "Flamethrower": "125", "Thunderbolt": "126", "Play Rough": "127", "Amnesia": "128",
    "Calm Mind": "129", "Helping Hand": "130", "Pollen Puff": "131", "Baton Pass": "132",
    "Earth Power": "133", "Reversal": "134", "Ice Beam": "135", "Electric Terrain": "136",
    "Grassy Terrain": "137", "Psychic Terrain": "138", "Misty Terrain": "139", "Nasty Plot": "140",
    "Fire Blast": "141", "Hydro Pump": "142", "Blizzard": "143", "Fire Pledge": "144",
    "Water Pledge": "145", "Grass Pledge": "146", "Wild Charge": "147", "Sludge Bomb": "148",
    "Earthquake": "149", "Stone Edge": "150", "Phantom Force": "151", "Giga Impact": "152",
    "Blast Burn": "153", "Hydro Cannon": "154", "Frenzy Plant": "155", "Outrage": "156",
    "Overheat": "157", "Focus Blast": "158", "Leaf Storm": "159", "Hurricane": "160",
    "Trick Room": "161", "Bug Buzz": "162", "Hyper Beam": "163", "Brave Bird": "164",
    "Flare Blitz": "165", "Thunder": "166", "Close Combat": "167", "Solar Beam": "168",
    "Draco Meteor": "169", "Steel Beam": "170", "Tera Blast": "171", "Roar": "172",
    "Charge": "173", "Haze": "174", "Toxic": "175", "Sand Tomb": "176",
    "Spite": "177", "Gravity": "178", "Smack Down": "179", "Gyro Ball": "180",
    "Knock Off": "181", "Bug Bite": "182", "Super Fang": "183", "Vacuum Wave": "184",
    "Lunge": "185", "High Horsepower": "186", "Icicle Spear": "187", "Scald": "188",
    "Heat Crash": "189", "Solar Blade": "190", "Uproar": "191", "Focus Punch": "192",
    "Weather Ball": "193", "Grassy Glide": "194", "Burning Jealousy": "195", "Flip Turn": "196",
    "Dual Wingbeat": "197", "Poltergeist": "198", "Lash Out": "199", "Scale Shot": "200",
    "Misty Explosion": "201", "Pain Split": "202", "Psych Up": "203", "Double Edge": "204",
    "Endeavor": "205", "Petal Blizzard": "206", "Temper Flare": "207", "Whirlpool": "208",
    "Muddy Water": "209", "Supercell Slam": "210", "Electroweb": "211", "Triple Axel": "212",
    "Coaching": "213", "Sludge Wave": "214", "Scorching Sands": "215", "Feather Dance": "216",
    "Future Sight": "217", "Expanding Force": "218", "Skitter Smack": "219", "Meteor Beam": "220",
    "Throat Chop": "221", "Breaking Swipe": "222", "Metal Sound": "223", "Curse": "224",
    "Hard Press": "225", "Dragon Cheer": "226", "Alluring Voice": "227", "Psychic Noise": "228",
    "Upper Hand": "229"
}

# --- VERSION PRIORITY LIST ---
VERSION_PRIORITY = [
    'scarlet-violet', 'sword-shield', 'brilliant-diamond-shining-pearl', 'legends-arceus',
    'ultra-sun-ultra-moon', 'sun-moon', 'omega-ruby-alpha-sapphire', 'x-y',
    'black-2-white-2', 'black-white', 'heartgold-soulsilver', 'platinum',
    'diamond-pearl', 'emerald', 'firered-leafgreen', 'ruby-sapphire',
    'crystal', 'gold-silver', 'yellow', 'red-blue'
]

# --- HELPERS ---
async def load_resources():
    print("⏳ Loading Pokedex Database...")
    try:
        url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
        response = requests.get(url)
        if response.status_code == 200:
            global POKEMON_NAMES
            data = response.json()
            POKEMON_NAMES = [entry['name'] for entry in data['results']]
            print(f"✅ Loaded {len(POKEMON_NAMES)} Pokemon!")
    except Exception as e:
        print(f"⚠️ Error: {e}")

def get_poke_data(name):
    try:
        r1 = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=5)
        if r1.status_code != 200: return None
        basic = r1.json()
        
        species_url = basic['species']['url']
        r2 = requests.get(species_url, timeout=5)
        species = r2.json() if r2.status_code == 200 else {}
        
        return {"basic": basic, "species": species}
    except Exception as e:
        print(f"API Error: {e}")
        return None

def generate_stat_bar(val):
    max_val = 180 
    filled = int((val / max_val) * 6)
    filled = max(1, min(6, filled))
    return "▰" * filled + "▱" * (6 - filled)

def calculate_stats_range(base, stat_name):
    if stat_name == 'hp':
        min_stat = (2 * base) + 110
        max_stat = (2 * base) + 204
    else:
        min_stat = int(((2 * base) + 5) * 0.9)
        max_stat = int(((2 * base) + 99) * 1.1)
    return min_stat, max_stat

def get_type_effectiveness(types):
    type_data = {}
    try:
        for t in types:
            r = requests.get(t['type']['url'])
            if r.status_code == 200:
                d = r.json()['damage_relations']
                for key in ['double_damage_from', 'half_damage_from', 'no_damage_from']:
                    for entry in d[key]:
                        name = entry['name']
                        factor = 2.0 if 'double' in key else (0.5 if 'half' in key else 0.0)
                        type_data[name] = type_data.get(name, 1.0) * factor
    except:
        pass
    return type_data

def roman_gen(gen_name):
    mapping = {
        'generation-i': 'I', 'generation-ii': 'II', 'generation-iii': 'III',
        'generation-iv': 'IV', 'generation-v': 'V', 'generation-vi': 'VI',
        'generation-vii': 'VII', 'generation-viii': 'VIII', 'generation-ix': 'IX'
    }
    return mapping.get(gen_name, '?')

# --- KEYBOARDS ---
def get_main_keyboard(name):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Moveset", callback_data=f"mov_menu|{name}"),
         InlineKeyboardButton("🛡️ Weakness", callback_data=f"weak|{name}")],
        [InlineKeyboardButton("🧬 Evolution", callback_data=f"evo|{name}"),
         InlineKeyboardButton("✨ Shiny", callback_data=f"shiny|{name}")]
    ])

def get_moves_menu_keyboard(name):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬆️ Level Up", callback_data=f"mov_show|{name}|level-up"),
         InlineKeyboardButton("🥚 Egg", callback_data=f"mov_show|{name}|egg")],
        [InlineKeyboardButton("💿 TMs", callback_data=f"mov_show|{name}|machine"),
         InlineKeyboardButton("👨‍🏫 Tutor", callback_data=f"mov_show|{name}|tutor")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"main|{name}")]
    ])

def get_suggestions_keyboard(suggestions):
    keyboard = []
    row = []
    for s in suggestions:
        row.append(InlineKeyboardButton(s.title(), callback_data=f"search|{s}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_pin_time_keyboard(msg_id, chat_id, user_id):
    # msg_id|chat_id|minutes|user_id
    base = f"setpin|{msg_id}|{chat_id}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("2m", callback_data=f"{base}|2|{user_id}"),
         InlineKeyboardButton("5m", callback_data=f"{base}|5|{user_id}"),
         InlineKeyboardButton("8m", callback_data=f"{base}|8|{user_id}"),
         InlineKeyboardButton("10m", callback_data=f"{base}|10|{user_id}")],
        [InlineKeyboardButton("12m", callback_data=f"{base}|12|{user_id}"),
         InlineKeyboardButton("15m", callback_data=f"{base}|15|{user_id}"),
         InlineKeyboardButton("18m", callback_data=f"{base}|18|{user_id}"),
         InlineKeyboardButton("20m", callback_data=f"{base}|20|{user_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_pin")]
    ])

# --- PINNING LOGIC (BACKGROUND TASK) ---
async def run_pin_timer(bot, chat_id, message_id, duration_sec, tag_text):
    """Waits in the background and unpins the message when time is up."""
    await asyncio.sleep(duration_sec)
    try:
        await bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
        await bot.send_message(
            chat_id=chat_id,
            text=f"⏰ <b>Time over! Message unpinned.</b> (cc: {tag_text})",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"Unpin Error: {e}")

async def request_pin_time(update: Update, context: ContextTypes.DEFAULT_TYPE, target_bot_id: int):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ <b>Reply to a message to pin it.</b>", parse_mode=ParseMode.HTML)
        return

    target_msg = update.message.reply_to_message
    
    if target_msg.from_user.id != target_bot_id:
        await update.message.reply_text("❌ <b>This is not the correct game bot.</b>", parse_mode=ParseMode.HTML)
        return

    user_id = update.message.from_user.id
    
    await update.message.reply_text(
        "📌 <b>Select Pin Duration:</b>",
        reply_markup=get_pin_time_keyboard(target_msg.message_id, update.message.chat_id, user_id),
        parse_mode=ParseMode.HTML
    )

async def hpin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await request_pin_time(update, context, HEXA_BOT_ID)

async def ppin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await request_pin_time(update, context, P_BOT_ID)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 <b>Pikadex Ready.</b>\nUsage: <code>/data name</code>", parse_mode=ParseMode.HTML)

# --- TEXT HANDLER FOR NATURES (NO SLASH COMMAND) ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore if message has no text
    if not update.message or not update.message.text:
        return

    # Clean the text: remove spaces and make lowercase
    text = update.message.text.strip().lower()

    if text in NATURE_DATA:
        data = NATURE_DATA[text]
        name_display = text.title()
        user = update.message.from_user
        user_tag = f"@{user.username}" if user.username else user.first_name
        
        # Determine stats text
        if data['up'] == 'None':
            stat_text = "⚖️ <b>Neutral Nature</b> (No changes)"
        else:
            stat_text = (
                f"📈 <b>Increases</b> : {data['up']} (+10%)\n"
                f"📉 <b>Decreases</b> : {data['down']} (-10%)"
            )

        msg = (
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<blockquote>"
            f"🌿 <b>Nature</b> : <b>{name_display}</b>\n\n"
            f"{stat_text}"
            f"</blockquote>\n"
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"👤 <i>Checked by</i> : {user_tag}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def send_main_profile(update: Update, name, user_tag="Unknown", is_callback=False, is_shiny=False):
    full_data = get_poke_data(name)
    if not full_data:
        if is_callback: await update.callback_query.answer("⚠️ Data load failed. Try again.")
        return

    basic = full_data['basic']
    species = full_data['species']
    
    # 1. Header Info
    p_id = basic['id']
    display_name = basic['name'].title()
    
    # 2. Types
    type_list = [f"{TYPE_EMOJIS.get(t['type']['name'], '❓')} {t['type']['name'].title()}" for t in basic['types']]
    type_str = ", ".join(type_list)
    
    # 3. Gen & Rarity
    gen = roman_gen(species.get('generation', {}).get('name', ''))
    rarity = "Mythical" if species.get('is_mythical') else ("Legendary" if species.get('is_legendary') else "Common")
    
    # Catch Rate
    raw_catch_rate = species.get('capture_rate', 0)
    catch_perc = (raw_catch_rate / 255) * 100
    catch_display = f"{raw_catch_rate} ({catch_perc:.2f}%)"
    
    # 4. Abilities
    abil_list = []
    hidden = "None"
    for a in basic['abilities']:
        aname = a['ability']['name'].replace('-', ' ').title()
        if a['is_hidden']: hidden = aname
        else: abil_list.append(aname)
    abil_str = ", ".join(abil_list)

    # 5. EV Yield
    evs = [f"{s['stat']['name'].title()} +{s['effort']}" for s in basic['stats'] if s['effort'] > 0]
    ev_str = ", ".join(evs) if evs else "None"

    # 6. Stats Block
    stat_text = ""
    s_map = {'hp': 'HP', 'attack': 'Atk', 'defense': 'Def', 'special-attack': 'Spa', 'special-defense': 'Spd', 'speed': 'Spe'}
    
    for s in basic['stats']:
        val = s['base_stat']
        name_short = s_map.get(s['stat']['name'], '???')
        min_v, max_v = calculate_stats_range(val, s['stat']['name'])
        bar = generate_stat_bar(val)
        stat_text += f"<b>{name_short}</b> : {val} ({min_v}-{max_v}) {bar}\n"

    # 7. Image Handling
    img_key = 'front_shiny' if is_shiny else 'front_default'
    artwork = basic['sprites']['other']['official-artwork'][img_key]
    sprite = basic['sprites'][img_key]
    img_url = artwork if artwork else sprite

    # 8. Message Construction (HTML)
    text = (
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<blockquote>"
        f"📌 <b>Pokemon</b> : <b>{display_name}</b>\n\n"
        f"🌍 <b>Region</b> : {gen}\n"
        f"🧬 <b>Types</b> : {type_str}\n"
        f"💎 <b>Rarity</b> : {rarity}\n"
        f"🎲 <b>Catch Rate</b> : {catch_display}\n\n"
        f"🔢 <b>Pokedex ID</b> : {p_id}\n"
        f"🛡️ <b>Ability</b> : {abil_str}\n"
        f"👁️ <b>Hidden Ability</b> : {hidden}\n"
        f"🏋️ <b>EV Yield</b> : {ev_str}\n\n"
        f"📊 <b>Base Stats</b>\n"
        f"{stat_text}"
        f"</blockquote>"
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"👤 <i>Checked by</i> : {user_tag}"
        f'<a href="{img_url}">&#8203;</a>'
    )

    keyboard = get_main_keyboard(name)

    if is_callback:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            await update.callback_query.message.delete()
            await update.callback_query.message.chat.send_message(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    
    data = query.data.split("|")
    action = data[0]
    user_tag = f"@{query.from_user.username}" if query.from_user.username else query.from_user.first_name

    # --- PINNING HANDLER ---
    if action == "setpin":
        msg_id = int(data[1])
        chat_id = int(data[2])
        mins = int(data[3])
        user_id = int(data[4])
        
        try:
            # Delete the menu message instantly
            await query.message.delete()
            
            # Pin the target message
            await context.bot.pin_chat_message(chat_id=chat_id, message_id=msg_id)
            
            # Get user info for tagging
            try:
                user = await context.bot.get_chat_member(chat_id, user_id)
                tag = f'<a href="tg://user?id={user_id}">{user.user.first_name}</a>'
            except:
                tag = "User"

            # Send PIN confirmation
            confirm_msg = await context.bot.send_message(
                chat_id=chat_id, 
                text=f"📌 <b>Message pinned for {mins}m by {tag}.</b>",
                parse_mode=ParseMode.HTML
            )
            
            # --- NON-BLOCKING WAIT ---
            asyncio.create_task(run_pin_timer(context.bot, chat_id, msg_id, mins * 60, tag))
            
        except Exception as e:
            print(f"Pin Error: {e}")
            await context.bot.send_message(chat_id=chat_id, text="⚠️ <b>Failed to pin. Make sure I am Admin!</b>", parse_mode=ParseMode.HTML)
        return

    elif action == "cancel_pin":
        await query.message.delete()
        return

    # --- POKEMON HANDLERS ---
    name = data[1] # For pokemon actions

    # --- MAIN PROFILE ---
    if action == "main" or action == "search":
        await send_main_profile(update, name, user_tag, is_callback=True)

    # --- SHINY TOGGLE ---
    elif action == "shiny":
        await send_main_profile(update, name, user_tag, is_callback=True, is_shiny=True)

    # --- MOVES MENU ---
    elif action == "mov_menu":
        await query.message.edit_text(
            f"⚔️ <b>Moveset : {name.title()}</b>\n\nSelect a category to view moves:",
            reply_markup=get_moves_menu_keyboard(name), parse_mode=ParseMode.HTML
        )

    # --- MOVES LIST (HTML + ROBUST TUTOR) ---
    elif action == "mov_show":
        cat = data[2]
        full_data = get_poke_data(name)
        
        if not full_data or 'moves' not in full_data['basic']:
            await query.message.edit_text("⚠️ Moves data unavailable.", reply_markup=get_main_keyboard(name))
            return

        all_moves = full_data['basic']['moves']
        
        target_version = None
        
        if cat == 'tutor':
            moves = []
            seen_moves = set()
            for m in all_moves:
                mname = m['move']['name'].replace('-', ' ').title()
                if mname in seen_moves: continue
                is_tutor = False
                for d in m['version_group_details']:
                    if d['move_learn_method']['name'] == 'tutor':
                        is_tutor = True
                        break
                if is_tutor:
                    moves.append((0, mname))
                    seen_moves.add(mname)
            target_version = "All Generations"
        else:
            available_versions = set()
            for m in all_moves:
                for d in m['version_group_details']:
                    available_versions.add(d['version_group']['name'])
            
            current_best_idx = 999
            for i, v in enumerate(VERSION_PRIORITY):
                if v in available_versions:
                    target_version = v
                    current_best_idx = i
                    break
            
            if current_best_idx > 0:
                species_name = full_data['basic']['species']['name']
                if species_name != name:
                    species_data = get_poke_data(species_name)
                    if species_data and 'moves' in species_data['basic']:
                        s_moves = species_data['basic']['moves']
                        s_versions = set()
                        for m in s_moves:
                            for d in m['version_group_details']:
                                s_versions.add(d['version_group']['name'])
                        for i, v in enumerate(VERSION_PRIORITY):
                            if v in s_versions:
                                if i < current_best_idx:
                                    target_version = v
                                    all_moves = s_moves
                                break
            if not target_version and available_versions:
                target_version = list(available_versions)[0]

            moves = []
            if target_version:
                for m in all_moves:
                    details = next(
                        (d for d in m['version_group_details'] 
                         if d['version_group']['name'] == target_version 
                         and d['move_learn_method']['name'] == cat), 
                        None
                    )
                    if details:
                        lvl = details['level_learned_at']
                        # Standardize move name to Title Case with Spaces (matches TM Map keys)
                        mname = m['move']['name'].replace('-', ' ').title()
                        moves.append((lvl, mname))

        if cat == 'level-up': moves.sort(key=lambda x: x[0])
        else: moves.sort(key=lambda x: x[1])

        lines = []
        for m in moves:
            if cat == 'level-up':
                lines.append(f"<code>Lv.{m[0]:02}</code> ➜ <b>{m[1]}</b>")
            elif cat == 'machine':
                tm_num = CUSTOM_TM_MAP.get(m[1], "") 
                tm_str = f"TM{tm_num}" if tm_num else "TM"
                lines.append(f"💿 {tm_str} ➜ <b>{m[1]}</b>")
            elif cat == 'tutor':
                lines.append(f"👨‍🏫 <b>{m[1]}</b>")
            else:
                lines.append(f"🥚 <b>{m[1]}</b> <i>(egg)</i>")
        
        version_display = target_version.replace('-', ' ').title() if target_version else "Unknown"
        if not lines: 
            lines = [f"<i>No {cat.replace('-', ' ')} moves found.</i>"]
        
        content = "\n".join(lines)
        if len(content) > 3000: content = content[:3000] + "\n\n...(truncated)"
        
        cat_title = cat.replace('-', ' ').title()
        if cat_title == "Machine": cat_title = "TM / HM"

        msg = (
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<blockquote>"
            f"⚔️ <b>Category</b> : <i>{cat_title}</i>\n"
            f"🎮 <b>Version</b> : <i>{version_display}</i>\n"
            f"📌 <b>Pokemon</b> : <b>{name.title()}</b>"
            f"</blockquote>\n"
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"{content}\n\n"
            f"👤 <i>Checked by</i> : {user_tag}"
        )
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"main|{name}")]])
        await query.message.edit_text(msg, reply_markup=back_kb, parse_mode=ParseMode.HTML)

    # --- WEAKNESS ---
    elif action == "weak":
        full_data = get_poke_data(name)
        if not full_data: return
        eff = get_type_effectiveness(full_data['basic']['types'])
        msg = f"🛡️ <b>Weakness : {name.title()}</b>\n━━━━━━━━━━━━━━━━━━\n"
        grouped = {}
        for t, mult in eff.items():
            if mult != 1.0:
                grouped.setdefault(mult, []).append(t.title())
        
        found = False
        for mult in sorted(grouped.keys(), reverse=True):
            found = True
            types = ", ".join(grouped[mult])
            if mult == 4.0: icon = "💀 <b>4x Fatal</b>"
            elif mult == 2.0: icon = "🥵 <b>2x Weak</b>"
            elif mult == 0.5: icon = "🛡️ <b>0.5x Resist</b>"
            elif mult == 0.25: icon = "🧱 <b>0.25x Tank</b>"
            elif mult == 0.0: icon = "👻 <b>0x Immune</b>"
            else: icon = f"<b>{mult}x</b>"
            msg += f"{icon}\n➡️ {types}\n\n"
            
        if not found: msg += "<i>No specific weaknesses or resistances (Neutral).</i>"
        msg += f"\n👤 <i>Checked by</i> : {user_tag}"
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"main|{name}")]])
        await query.message.edit_text(msg, reply_markup=back_kb, parse_mode=ParseMode.HTML)

    # --- EVOLUTION ---
    elif action == "evo":
        full_data = get_poke_data(name)
        species = full_data.get('species', {})
        chain_url = species.get('evolution_chain', {}).get('url')
        
        if not chain_url:
            await query.message.edit_text("🧬 <b>Evolution</b>\n\n<i>No evolution data.</i>", reply_markup=get_main_keyboard(name), parse_mode=ParseMode.HTML)
            return

        try:
            r = requests.get(chain_url)
            chain_data = r.json()
            chain = chain_data['chain']
            
            species_urls = []
            def traverse(node):
                species_urls.append(node['species']['url'])
                for child in node['evolves_to']: traverse(child)
            traverse(chain)
            
            all_forms = []
            for s_url in species_urls:
                s_r = requests.get(s_url)
                if s_r.status_code == 200:
                    s_data = s_r.json()
                    for v in s_data['varieties']:
                        all_forms.append(v['pokemon']['name'])
            
            buttons = []
            row = []
            for form_name in all_forms:
                label = form_name.replace('-', ' ').title()
                row.append(InlineKeyboardButton(label, callback_data=f"search|{form_name}"))
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            if row: buttons.append(row)
            
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"main|{name}")])
            
            await query.message.edit_text(
                f"🧬 <b>Evolution & Forms :</b>\nSelect a form to view:",
                reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Evo Error: {e}")
            await query.message.edit_text(
                "⚠️ Error loading evolution data.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"main|{name}")]])
            )

async def data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: <code>/data name</code>", parse_mode=ParseMode.HTML)
        return

    query = context.args[0].lower()
    user = update.message.from_user
    user_tag = f"@{user.username}" if user.username else user.first_name

    if query in POKEMON_NAMES:
        await send_main_profile(update, query, user_tag)
        return

    matches = difflib.get_close_matches(query, POKEMON_NAMES, n=12, cutoff=0.4)
    if matches:
        msg = f"🤔 <b>Pokemon not found.</b>\n\n👤 <i>Requested by</i> : {user_tag}\n\nDid you mean one of these?"
        kb = get_suggestions_keyboard(matches)
        await update.message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ No Pokémon found with that name.", parse_mode=ParseMode.HTML)

# --- WEB SERVER FOR RENDER (KEEPS BOT ALIVE) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    # Render assigns a port via the PORT environment variable
    port = int(os.environ.get("PORT", 5000)) 
    flask_app.run(host='0.0.0.0', port=port)

# --- MAIN EXECUTION ---
async def post_init(application):
    await load_resources()

if __name__ == '__main__':
    t = Thread(target=run_flask)
    t.start()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('data', data_command))
    app.add_handler(CommandHandler('hpin', hpin_command))
    app.add_handler(CommandHandler('ppin', ppin_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    print("Bot is running...")
    app.run_polling()
