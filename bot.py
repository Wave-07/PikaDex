import logging
import json
import os
import difflib
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    CallbackQueryHandler, MessageHandler, filters
)

# --- CONFIGURATION ---
# This reads the token from Render's settings
BOT_TOKEN = os.environ.get("BOT_TOKEN") 

if not BOT_TOKEN:
    print("❌ Error: BOT_TOKEN is missing! Set it in Render Environment Variables.")
    exit(1)

# --- BOT IDs ---
HEXA_BOT_ID = 572621020
P_BOT_ID = 7955369039

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE ---
DB = {} 
POKEMON_NAMES = []

TYPE_EMOJIS = {
    'normal': '🔘', 'fire': '🔥', 'water': '💧', 'electric': '⚡', 'grass': '🌱', 'ice': '❄️',
    'fighting': '🥊', 'poison': '☣', 'ground': '⛰', 'flying': '🪽', 'psychic': '🔮', 'bug': '🪲',
    'rock': '🪨', 'ghost': '👁‍🗨', 'dragon': '🐉', 'dark': '🌑', 'steel': '🔩', 'fairy': '🧚‍♀',
    'stellar': '🪄', 'unknown': '❓'
}

NATURE_DATA = {
    'hardy': {'up': 'None', 'down': 'None'}, 'lonely': {'up': 'Attack', 'down': 'Defense'},
    'brave': {'up': 'Attack', 'down': 'Speed'}, 'adamant': {'up': 'Attack', 'down': 'Sp. Atk'},
    'naughty': {'up': 'Attack', 'down': 'Sp. Def'}, 'bold': {'up': 'Defense', 'down': 'Attack'},
    'docile': {'up': 'None', 'down': 'None'}, 'relaxed': {'up': 'Defense', 'down': 'Speed'},
    'impish': {'up': 'Defense', 'down': 'Sp. Atk'}, 'lax': {'up': 'Defense', 'down': 'Sp. Def'},
    'timid': {'up': 'Speed', 'down': 'Attack'}, 'hasty': {'up': 'Speed', 'down': 'Defense'},
    'serious': {'up': 'None', 'down': 'None'}, 'jolly': {'up': 'Speed', 'down': 'Sp. Atk'},
    'naive': {'up': 'Speed', 'down': 'Sp. Def'}, 'modest': {'up': 'Sp. Atk', 'down': 'Attack'},
    'mild': {'up': 'Sp. Atk', 'down': 'Defense'}, 'quiet': {'up': 'Sp. Atk', 'down': 'Speed'},
    'bashful': {'up': 'None', 'down': 'None'}, 'rash': {'up': 'Sp. Atk', 'down': 'Sp. Def'},
    'calm': {'up': 'Sp. Def', 'down': 'Attack'}, 'gentle': {'up': 'Sp. Def', 'down': 'Defense'},
    'sassy': {'up': 'Sp. Def', 'down': 'Speed'}, 'careful': {'up': 'Sp. Def', 'down': 'Sp. Atk'},
    'quirky': {'up': 'None', 'down': 'None'}
}

CUSTOM_TM_MAP = {
    "Take Down": "001", "Charm": "002", "Fake Tears": "003", "Agility": "004", "Mud Slap": "005",
    "Protect": "007", "Fire Fang": "008", "Thunder Fang": "009", "Ice Fang": "010", "Water Pulse": "011",
    "Low Kick": "012", "Acid Spray": "013", "Acrobatics": "014", "Struggle Bug": "015", "Psybeam": "016",
    "Confuse Ray": "017", "Thief": "018", "Disarming Voice": "019", "Trailblaze": "020", "Chilling Water": "022",
    "Charge Beam": "023", "Fire Spin": "024", "Facade": "025", "Aerial Ace": "027", "Bulldoze": "028",
    "Hex": "029", "Snarl": "030", "Metal Claw": "031", "Swift": "032", "Magical Leaf": "033",
    "Icy Wind": "034", "Mud Shot": "035", "Rock Tomb": "036", "Draining Kiss": "037", "Flame Charge": "038",
    "Low Sweep": "039", "Air Cutter": "040", "Stored Power": "041", "Night Shade": "042", "Fling": "043",
    "Dragon Tail": "044", "Venoshock": "045", "Avalanche": "046", "Endure": "047", "Volt Switch": "048",
    "Sunny Day": "049", "Rain Dance": "050", "Sandstorm": "051", "Snowscape": "052", "Smart Strike": "053",
    "Psyshock": "054", "Dig": "055", "Bullet Seed": "056", "False Swipe": "057", "Brick Break": "058",
    "Zen Headbutt": "059", "U Turn": "060", "Shadow Claw": "061", "Foul Play": "062", "Psychic Fangs": "063",
    "Bulk Up": "064", "Air Slash": "065", "Body Slam": "066", "Fire Punch": "067", "Thunder Punch": "068",
    "Ice Punch": "069", "Sleep Talk": "070", "Seed Bomb": "071", "Electro Ball": "072", "Drain Punch": "073",
    "Reflect": "074", "Light Screen": "075", "Rock Blast": "076", "Waterfall": "077", "Dragon Claw": "078",
    "Dazzling Gleam": "079", "Metronome": "080", "Grass Knot": "081", "Thunder Wave": "082", "Poison Jab": "083",
    "Stomping Tantrum": "084", "Rest": "085", "Rock Slide": "086", "Taunt": "087", "Swords Dance": "088",
    "Body Press": "089", "Spikes": "090", "Toxic Spikes": "091", "Imprison": "092", "Flash Cannon": "093",
    "Dark Pulse": "094", "Leech Life": "095", "Eerie Impulse": "096", "Fly": "097", "Skill Swap": "098",
    "Iron Head": "099", "Dragon Dance": "100", "Power Gem": "101", "Gunk Shot": "102", "Substitute": "103",
    "Iron Defense": "104", "X Scissor": "105", "Drill Run": "106", "Will O Wisp": "107", "Crunch": "108",
    "Trick": "109", "Liquidation": "110", "Giga Drain": "111", "Aura Sphere": "112", "Tailwind": "113",
    "Shadow Ball": "114", "Dragon Pulse": "115", "Stealth Rock": "116", "Hyper Voice": "117", "Heat Wave": "118",
    "Energy Ball": "119", "Psychic": "120", "Heavy Slam": "121", "Encore": "122", "Surf": "123", "Ice Spinner": "124",
    "Flamethrower": "125", "Thunderbolt": "126", "Play Rough": "127", "Amnesia": "128", "Calm Mind": "129",
    "Helping Hand": "130", "Pollen Puff": "131", "Baton Pass": "132", "Earth Power": "133", "Reversal": "134",
    "Ice Beam": "135", "Electric Terrain": "136", "Grassy Terrain": "137", "Psychic Terrain": "138",
    "Misty Terrain": "139", "Nasty Plot": "140", "Fire Blast": "141", "Hydro Pump": "142", "Blizzard": "143",
    "Fire Pledge": "144", "Water Pledge": "145", "Grass Pledge": "146", "Wild Charge": "147", "Sludge Bomb": "148",
    "Earthquake": "149", "Stone Edge": "150", "Phantom Force": "151", "Giga Impact": "152", "Blast Burn": "153",
    "Hydro Cannon": "154", "Frenzy Plant": "155", "Outrage": "156", "Overheat": "157", "Focus Blast": "158",
    "Leaf Storm": "159", "Hurricane": "160", "Trick Room": "161", "Bug Buzz": "162", "Hyper Beam": "163",
    "Brave Bird": "164", "Flare Blitz": "165", "Thunder": "166", "Close Combat": "167", "Solar Beam": "168",
    "Draco Meteor": "169", "Steel Beam": "170", "Tera Blast": "171", "Roar": "172", "Charge": "173", "Haze": "174",
    "Toxic": "175", "Sand Tomb": "176", "Spite": "177", "Gravity": "178", "Smack Down": "179", "Gyro Ball": "180",
    "Knock Off": "181", "Bug Bite": "182", "Super Fang": "183", "Vacuum Wave": "184", "Lunge": "185",
    "High Horsepower": "186", "Icicle Spear": "187", "Scald": "188", "Heat Crash": "189", "Solar Blade": "190",
    "Uproar": "191", "Focus Punch": "192", "Weather Ball": "193", "Grassy Glide": "194", "Burning Jealousy": "195",
    "Flip Turn": "196", "Dual Wingbeat": "197", "Poltergeist": "198", "Lash Out": "199", "Scale Shot": "200",
    "Misty Explosion": "201", "Pain Split": "202", "Psych Up": "203", "Double Edge": "204", "Endeavor": "205",
    "Petal Blizzard": "206", "Temper Flare": "207", "Whirlpool": "208", "Muddy Water": "209", "Supercell Slam": "210",
    "Electroweb": "211", "Triple Axel": "212", "Coaching": "213", "Sludge Wave": "214", "Scorching Sands": "215",
    "Feather Dance": "216", "Future Sight": "217", "Expanding Force": "218", "Skitter Smack": "219", "Meteor Beam": "220",
    "Throat Chop": "221", "Breaking Swipe": "222", "Metal Sound": "223", "Curse": "224", "Hard Press": "225",
    "Dragon Cheer": "226", "Alluring Voice": "227", "Psychic Noise": "228", "Upper Hand": "229"
}

# --- HELPERS ---
async def load_resources():
    global DB, POKEMON_NAMES
    print("⏳ Loading Local Database (pokedex.json)...")
    try:
        with open('pokedex.json', 'r', encoding='utf-8') as f:
            DB = json.load(f)
            POKEMON_NAMES = list(DB['pokemon'].keys())
        print(f"✅ Database Loaded: {len(POKEMON_NAMES)} Pokemon.")
    except Exception as e:
        print(f"⚠️ Error loading pokedex.json: {e}")

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

# --- REFINED NATURE LOGIC ---
def get_recommended_natures(stats):
    atk = stats.get('attack', 0)
    spa = stats.get('special-attack', 0)
    
    # MIXED ATTACKER CHECK (Threshold 15)
    if abs(atk - spa) <= 15:
        return "Modest, Timid, Bold, Calm, Adamant, Jolly, Impish, Careful"
    # SPECIAL ATTACKER
    elif spa > atk:
        return "Modest, Timid, Bold, Calm"
    # PHYSICAL ATTACKER
    else:
        return "Adamant, Jolly, Impish, Careful"

def get_type_effectiveness_local(types):
    if 'types' not in DB: return {}
    multipliers = {}
    for t in types:
        if t not in DB['types']: continue
        damage_relations = DB['types'][t]
        for atk_type, factor in damage_relations.items():
            current = multipliers.get(atk_type, 1.0)
            multipliers[atk_type] = current * factor
    return multipliers

# --- KEYBOARDS ---
def get_main_keyboard(name):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Moveset", callback_data=f"mov_menu|{name}"),
         InlineKeyboardButton("🛡️ Weakness", callback_data=f"weak|{name}")],
        [InlineKeyboardButton("🧬 Evolution & Forms", callback_data=f"evo|{name}"),
         InlineKeyboardButton("✨ Shiny", callback_data=f"shiny|{name}")]
    ])

def get_moves_menu_keyboard(name):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬆️ Level Up", callback_data=f"mov_show|{name}|level-up|1"),
         InlineKeyboardButton("🥚 Egg", callback_data=f"mov_show|{name}|egg|1")],
        [InlineKeyboardButton("💿 TMs", callback_data=f"mov_show|{name}|machine|1"),
         InlineKeyboardButton("👨‍🏫 Tutor", callback_data=f"mov_show|{name}|tutor|1")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"main|{name}")]
    ])

def get_suggestions_keyboard(suggestions):
    keyboard = []
    row = []
    for s in suggestions:
        btn_text = s.replace('-', ' ').title()
        row.append(InlineKeyboardButton(btn_text, callback_data=f"search|{s}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# --- NEW: Specific Keyboard for BestNat Suggestions ---
def get_bestnat_suggestions_keyboard(suggestions):
    keyboard = []
    row = []
    for s in suggestions:
        btn_text = s.replace('-', ' ').title()
        # Uses 'bnat' prefix to distinguish from normal data lookup
        row.append(InlineKeyboardButton(btn_text, callback_data=f"bnat|{s}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_pin_time_keyboard(msg_id, chat_id, user_id):
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

# --- PINNING LOGIC ---
async def run_pin_timer(bot, chat_id, message_id, duration_sec, tag_text):
    await asyncio.sleep(duration_sec)
    try:
        await bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
        await bot.send_message(chat_id=chat_id, text=f"⏰ <b>Time over! Message unpinned.</b> (cc: {tag_text})", parse_mode=ParseMode.HTML)
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
    await update.message.reply_text("📌 <b>Select Pin Duration:</b>", reply_markup=get_pin_time_keyboard(target_msg.message_id, update.message.chat_id, user_id), parse_mode=ParseMode.HTML)

async def hpin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await request_pin_time(update, context, HEXA_BOT_ID)

async def ppin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await request_pin_time(update, context, P_BOT_ID)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 <b>Pikadex Ready (Local Mode).</b>\nUsage: <code>/data name</code>", parse_mode=ParseMode.HTML)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text.strip().lower()
    user_tag = f"@{update.message.from_user.username}" if update.message.from_user.username else update.message.from_user.first_name

    # 1. Nature
    if text in NATURE_DATA:
        data = NATURE_DATA[text]
        name_display = text.title()
        if data['up'] == 'None': stat_text = "⚖️ <b>Neutral Nature</b> (No changes)"
        else: stat_text = f"📈 <b>Increases</b> : {data['up']} (+10%)\n📉 <b>Decreases</b> : {data['down']} (-10%)"
        msg = f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote>🌿 <b>Nature</b> : <b>{name_display}</b>\n\n{stat_text}</blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>\n👤 <i>Checked by</i> : {user_tag}"
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    # 2. Move (Format: "focus punch" -> "focus-punch")
    move_key = text.replace(" ", "-")
    if move_key in DB.get('moves', {}):
        m_data = DB['moves'][move_key]
        move_name = text.title()
        m_type = m_data.get('t', 'unknown')
        type_icon = TYPE_EMOJIS.get(m_type, '⚪')
        
        power = m_data.get('p') if m_data.get('p') else "None"
        acc = m_data.get('a') if m_data.get('a') else "100"
        pp = m_data.get('pp') if m_data.get('pp') else "None"
        desc = m_data.get('d', "No description available.")
        # Default to Status if class missing, display title case
        m_class = m_data.get('c', 'Status').title() 

        msg = (
            f"<b>Move</b> : <b>{move_name}</b> {type_icon}\n"
            f"💥{power}  🎯{acc}  🔋{pp} | {m_class}\n\n"
            f"<blockquote>"
            f"<b>Effect</b> : <i>{desc}</i>\n"
            f"</blockquote>\n" 
            f"👤 <i>Checked by</i> : {user_tag}"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

async def send_main_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, name, user_tag="Unknown", is_callback=False, is_shiny=False):
    pokemon = DB['pokemon'].get(name)
    if not pokemon:
        if is_callback: await update.callback_query.answer("⚠️ Data missing.")
        return

    p_id = pokemon['id']
    display_name = pokemon['name'].replace('-', ' ').title()
    type_str = ", ".join([f"{TYPE_EMOJIS.get(t, '❓')} {t.title()}" for t in pokemon['types']])
    
    region = pokemon.get('region', 'Unknown')
    ev_str = pokemon.get('ev_yield', 'None')
    
    rarity = "Mythical" if pokemon['is_mythical'] else ("Legendary" if pokemon['is_legendary'] else "Common")
    raw_catch = pokemon['catch_rate']
    catch_perc = (raw_catch / 255) * 100
    catch_display = f"{raw_catch} ({catch_perc:.1f}%)"
    
    abil_list = [a.replace('-', ' ').title() for a in pokemon['abilities']]
    abil_str = ", ".join(abil_list) if abil_list else "None"
    hidden = pokemon['hidden_ability'].replace('-', ' ').title()

    stat_text = ""
    s_map = {'hp': 'HP', 'attack': 'Atk', 'defense': 'Def', 'special-attack': 'Spa', 'special-defense': 'Spd', 'speed': 'Spe'}
    for s_name, val in pokemon['stats'].items():
        min_v, max_v = calculate_stats_range(val, s_name)
        bar = generate_stat_bar(val)
        stat_text += f"<b>{s_map.get(s_name, '???')}</b> : {val} ({min_v}-{max_v}) {bar}\n"

    # Saved URLs
    if is_shiny: img_url = pokemon.get('shiny_url', '')
    else: img_url = pokemon.get('normal_url', '')
    
    if not img_url:
        img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{p_id}.png"

    link_preview = f'<a href="{img_url}">&#8203;</a>'

    text = (
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
        f"<blockquote>"
        f"📌 <b>Pokemon</b> : <b>{display_name}</b>\n\n"
        f"🌍 <b>Region</b> : {region}\n"
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
        f"{link_preview}" 
    )
    
    keyboard = get_main_keyboard(name)

    try:
        if is_callback:
            await update.callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception as e:
        if is_callback:
            try:
                await update.callback_query.message.delete()
            except: pass
            await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# --- NEW: Helper to Send BestNat Response ---
async def send_bestnat_response(update, context, name, is_callback=False):
    p_data = DB['pokemon'][name]
    name_title = p_data['name'].replace('-', ' ').title()
    natures = get_recommended_natures(p_data['stats'])
    
    # --- THIS WAS ALSO MISSING ---
    # Determine who the user is based on if it's a button click or a message
    if is_callback:
        user = update.callback_query.from_user
    else:
        user = update.message.from_user
    
    user_tag = f"@{user.username}" if user.username else user.first_name
    # -----------------------------

    # FORMATTED OUTPUT with Emojis and Bold
    msg = f"🎯 I’d say the best natures for <b>{name_title}</b> are :- \n <blockquote><b>{natures}</b></blockquote>\n\n 👤 <i>Requested by</i> : {user_tag}"
    
    if is_callback:
        await update.callback_query.message.edit_text(msg, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    try:
        await query.answer()
    except: pass

    data = query.data.split("|")
    action = data[0]
    user_tag = f"@{query.from_user.username}" if query.from_user.username else query.from_user.first_name

    if action == "setpin":
        msg_id, chat_id, mins, user_id = int(data[1]), int(data[2]), int(data[3]), int(data[4])
        try:
            await query.message.delete()
            await context.bot.pin_chat_message(chat_id=chat_id, message_id=msg_id)
            try:
                user = await context.bot.get_chat_member(chat_id, user_id)
                tag = f'<a href="tg://user?id={user_id}">{user.user.first_name}</a>'
            except: tag = "User"
            
            await context.bot.send_message(chat_id=chat_id, text=f"📌 <b>Message pinned for {mins}m by {tag}.</b>", parse_mode=ParseMode.HTML)
            asyncio.create_task(run_pin_timer(context.bot, chat_id, msg_id, mins * 60, tag))
        except:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ <b>Pin failed. Admin?</b>", parse_mode=ParseMode.HTML)
        return

    elif action == "cancel_pin":
        await query.message.delete()
        return

    name = data[1]

    if action == "main" or action == "search":
        await send_main_profile(update, context, name, user_tag, is_callback=True)
    elif action == "shiny":
        await send_main_profile(update, context, name, user_tag, is_callback=True, is_shiny=True)
    # --- NEW: Action for BestNat buttons ---
    elif action == "bnat":
        await send_bestnat_response(update, context, name, is_callback=True)
        
    elif action == "mov_menu":
        try:
            await query.message.edit_text(f"⚔️ <b>Moveset : {name.title()}</b>\nSelect a category to view moves:", reply_markup=get_moves_menu_keyboard(name), parse_mode=ParseMode.HTML)
        except Exception as e:
            pass

    elif action == "mov_show":
        cat = data[2]
        page = int(data[3]) if len(data) > 3 else 1
        ITEMS_PER_PAGE = 20
        pokemon = DB['pokemon'].get(name)
        if not pokemon: return

        all_moves = pokemon['moves']
        filtered_moves = [m for m in all_moves if m['m'] == cat]
        
        if cat == 'tutor' or cat == 'egg':
            version_display = "All Versions"
        else:
            if filtered_moves:
                v_slug = filtered_moves[0].get('v', '')
                version_display = v_slug.replace('-', ' ').title()
            else:
                version_display = "Unknown"

        if cat == 'level-up': filtered_moves.sort(key=lambda x: x['l'])
        else: filtered_moves.sort(key=lambda x: x['n'])

        total_moves = len(filtered_moves)
        total_pages = (total_moves + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        start_idx = (page - 1) * ITEMS_PER_PAGE
        current_batch = filtered_moves[start_idx : start_idx + ITEMS_PER_PAGE]

        cat_title = cat.replace('-', ' ').title()
        header_text = (
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<blockquote>"
            f"⚔️ <b>Category</b> : <i>{cat_title} (Page {page}/{total_pages})</i>\n"
            f"🎮 <b>Version</b> : <i>{version_display}</i>\n"
            f"📌 <b>Pokemon</b> : <b>{name.title()}</b>"
            f"</blockquote>\n"
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n\n"
        )
        footer_text = f"\n\n👤 <i>Checked by</i> : {user_tag}"
        
        nav = []
        if page > 1: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"mov_show|{name}|{cat}|{page-1}"))
        if page < total_pages: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"mov_show|{name}|{cat}|{page+1}"))
        rows = [nav] if nav else []
        rows.append([InlineKeyboardButton("🔙 Back Menu", callback_data=f"mov_menu|{name}")])

        if not current_batch:
            try:
                await query.message.edit_text(f"{header_text}<i>No {cat} moves found.</i>{footer_text}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"main|{name}")]]), parse_mode=ParseMode.HTML)
            except: pass
            return

        lines = []
        for i, m in enumerate(current_batch):
            list_num = start_idx + i + 1
            move_name = m['n'].replace('-', ' ').title()
            
            details = DB['moves'].get(m['n'], {'p': '-', 'a': '-', 'pp': '-', 't': 'unknown', 'c': 'Status'})
            type_icon = TYPE_EMOJIS.get(details['t'], '⚪')
            move_class = details.get('c', 'Status').title()

            if cat == 'level-up': prefix = f"Lv.{m['l']:02}"
            elif cat == 'machine':
                tm_num = CUSTOM_TM_MAP.get(move_name, "")
                prefix = f"TM{tm_num}" if tm_num else "TM"
            else: prefix = "🥚"
            
            lines.append(
                f"<b>{list_num}. {prefix} ➜ {move_name} {type_icon}</b>\n"
                f"      💥{details['p'] or 'None'}  🎯{details['a'] or 'None'}  🔋{details['pp'] or 'None'} | {move_class}"
            )

        content = "\n\n".join(lines)
        try:
            await query.message.edit_text(f"{header_text}{content}{footer_text}", reply_markup=InlineKeyboardMarkup(rows), parse_mode=ParseMode.HTML)
        except Exception as e:
            pass

    elif action == "weak":
        pokemon = DB['pokemon'].get(name)
        if not pokemon: return
        eff = get_type_effectiveness_local(pokemon['types'])
        msg = f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote>🛡️ <b>Weakness</b> : <b>{name.title()}</b>\n</blockquote><b>━━━━━━━━━━━━━━━━━━</b>\n"
        grouped = {}
        for t, mult in eff.items():
            if mult != 1.0: grouped.setdefault(mult, []).append(t.title())
        for mult in sorted(grouped.keys(), reverse=True):
            types_str = ", ".join(grouped[mult])
            if mult == 4.0: icon = "💀 <b>4x Fatal</b>"
            elif mult == 2.0: icon = "🥵 <b>2x Weak</b>"
            elif mult == 0.5: icon = "🛡️ <b>0.5x Resist</b>"
            elif mult == 0.25: icon = "🧱 <b>0.25x Tank</b>"
            elif mult == 0.0: icon = "👻 <b>0x Immune</b>"
            else: icon = f"<b>{mult}x</b>"
            msg += f"{icon}\n➡️ {types_str}\n\n"
        msg += f"👤 <i>Checked by</i> : {user_tag}"
        try:
            await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"main|{name}")]]), parse_mode=ParseMode.HTML)
        except: pass

    elif action == "evo":
        pokemon = DB['pokemon'].get(name)
        evo_chain = pokemon.get('evolution', [])
        if not evo_chain:
            try:
                await query.message.edit_text("🧬 <b>Evolution</b>\n\n<i>No data.</i>", reply_markup=get_main_keyboard(name), parse_mode=ParseMode.HTML)
            except: pass
            return
        kb = get_suggestions_keyboard(evo_chain[:90])
        try:
            await query.message.edit_text(f"🧬 <b>Evolution & Forms :</b>\nSelect a form to view:", reply_markup=kb, parse_mode=ParseMode.HTML)
        except: pass

async def data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: <code>/data name</code>", parse_mode=ParseMode.HTML)
        return
    query = context.args[0].lower()
    user_tag = f"@{update.message.from_user.username}" if update.message.from_user.username else update.message.from_user.first_name

    if query in DB['pokemon']:
        await send_main_profile(update, context, query, user_tag)
        return

    matches = difflib.get_close_matches(query, POKEMON_NAMES, n=12, cutoff=0.4)
    if matches:
        await update.message.reply_text(f"🤔 <b>Pokemon not found.</b>\n\n👤 <i>Requested by</i> : {user_tag}\n\nDid you mean one of these?", reply_markup=get_suggestions_keyboard(matches), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ No Pokémon found.", parse_mode=ParseMode.HTML)

# --- UPDATED COMMAND: /bestnat with Typo Check & Buttons ---
async def bestnat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: <code>/bestnat name</code>", parse_mode=ParseMode.HTML)
        return
    
    # --- THIS WAS MISSING ---
    # We need to define user_tag before using it
    user = update.message.from_user
    user_tag = f"@{user.username}" if user.username else user.first_name
    # ------------------------

    # Handle multi-word queries if needed, and lowercase immediately
    query = " ".join(context.args).lower().strip()
    
    # 1. Exact Match Check
    if query in DB['pokemon']:
        await send_bestnat_response(update, context, query)
        return

    # 2. Fuzzy Match / Typo Handling (Get 12 best matches)
    matches = difflib.get_close_matches(query, POKEMON_NAMES, n=12, cutoff=0.5)
    
    if matches:
        await update.message.reply_text(
            f"🤔 <b>Pokemon not found.</b>\n\n👤 <i>Requested by</i> : {user_tag}\n\nDid you mean one of these for Best Nature?", 
            reply_markup=get_bestnat_suggestions_keyboard(matches), 
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text("❌ Pokémon not found.", parse_mode=ParseMode.HTML)

async def post_init(application):
    await load_resources()

# --- WEB SERVER TO KEEP BOT ALIVE ON RENDER ---
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

if __name__ == '__main__':
    Thread(target=run_flask).start()
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('data', data_command))
    app.add_handler(CommandHandler('bestnat', bestnat_command))
    app.add_handler(CommandHandler('hpin', hpin_command))
    app.add_handler(CommandHandler('ppin', ppin_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    print("Bot is running...")
    app.run_polling()
