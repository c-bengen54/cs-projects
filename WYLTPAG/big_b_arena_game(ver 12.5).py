'''
Author: Christopher Bengen

Date: 11/25/25

Program Name: Big B's Arcade Mystery

Description: A game about trying to escape a haunted arcade and save your friends
from an evil soul eating wizard named Tobias. You do this by defeating Tobias,
solving puzzles and finding clues, defeating Tobias's three bosses.

Citations:

(time.sleep)
Title: time - Time across access and conversions
Author: Python Software Foundation
Date: Oct. 21, 2025
Availability: https://docs.python.org/3/library/time.html#time.sleep

(ANSI character terminal codes)
Title: ANSI escape code
Author: Wikipedia
Date: Oct. 21, 2025
Availability: https://en.wikipedia.org/wiki/ANSI_escape_code

(Random Characters in Glitch Text)
Title: random - Generate pseudo-random numbers
Author: Python Software Foundation
Date: Oct. 21, 2025
Availability: https://docs.python.org/3/library/random.html

(flush)
Title: Built-in functions
Author: Python Software Foundation
Date: Oct. 21, 2025
Availability: https://docs.python.org/3/library/functions.html#print

(Unicode Characters to build map walls)
Title: List of Unicode characters
Author: Wikipedia
Date: Nov. 4, 2025
Availability: https://en.wikipedia.org/wiki/List_of_Unicode_characters#Unicode_symbols

(Nested Dictionaries)
Title: Built-in Types
Author: Python Software Foundation
Date: Nov. 10, 2025
Availability: https://docs.python.org/3/library/stdtypes.html#mapping-types-dict

(Regular Expression Import)
Title: re — Regular expression operations
Author: Python Software Foundation
Date: Nov. 10, 2025
Availability: https://docs.python.org/3/library/re.html#module-re

(List And Dict Manipulation Methodology)
Title: Data Structures
Author: Python Software Foundation
Date: Nov. 10, 2025
Availability: https://docs.python.org/3/tutorial/datastructures.html
'''

#Imports
import random
import time
import sys
import re
import traceback
import os
import json
import tempfile

#========= Ensure save game area has a directory =========
if not os.path.exists("saves"):
    os.makedirs("saves")
#----------------------------------

#========= Encryption =========
from cryptography.fernet import Fernet
MASTER_ENCRYPTION_KEY = b"Ew7wpmjWm7Qf3V0ZzCxw0zMefAAJz6EyK41ee0c2Mns="

fernet = Fernet(MASTER_ENCRYPTION_KEY)

#Decrypt the players given save key for dev usage
def reveal_save_key(filename):
    """
    Decrypt the save key for developer usage 
    """
    filename = _sanitize_filename(filename)
    filename = _ensure_json_extension(filename)
    filepath = _filepath_for(filename)

    if not os.path.exists(filepath):
        print("\n[DEV] Save file not found.\n")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    encrypted = data.get("auth", {}).get("encrypted_key")
    if not encrypted:
        print("\n[DEV] No encrypted key stored.\n")
        return

    try:
        key_plain = fernet.decrypt(encrypted.encode()).decode()
        print(f"\n[DEV] Save key for {filename}: {key_plain}\n")
    except:
        print("\n[DEV] Could not decrypt key (wrong master key?).\n")
#----------------------------------

# ========= Config =========
SAVE_DIR = "saves"
DEV_LEDGER = "dev_saves.txt"
SAVE_VERSION = 12.5    # Bump if the save format changes

#Ensure save directory exists
os.makedirs(SAVE_DIR, exist_ok=True)
#----------------------------

# ========= File Helpers =========
def _sanitize_filename(name: str) -> str:
    """Allow only letters, numbers, dash, underscore, and dot. Replace others with underscore."""
    name = name.strip()
    # remove path separators and collapse spaces
    name = name.replace(os.sep, "_").replace("/", "_")
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name

def _ensure_json_extension(name: str) -> str:
    if not name.lower().endswith(".json"):
        name += ".json"
    return name

def _filepath_for(name: str) -> str:
    return os.path.join(SAVE_DIR, name)

def _atomic_write_json(filepath: str, data: dict):
    """Write JSON atomically: write to a temp file then move/rename into place."""
    dirpath = os.path.dirname(filepath) or "."
    fd, temp_path = tempfile.mkstemp(prefix="tmp_save_", dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, filepath)
    except Exception:
        try:
            os.remove(temp_path)
        except Exception:
            pass
        raise

def _update_ledger(filename, encrypted_key, timestamp, player_name):
    """Replace existing ledger entry for filename or add a new one."""
    lines = []
    if os.path.exists(DEV_LEDGER):
        with open(DEV_LEDGER, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated = False
    new_lines = []

    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2 and parts[1] == filename:
            # Replace old entry
            new_lines.append(f"{player_name} | {filename} | {encrypted_key} | {timestamp}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{player_name} | {filename} | {encrypted_key} | {timestamp}\n")

    with open(DEV_LEDGER, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def migrate_save(state: dict):
    """
    Upgrade old save files to the current SAVE_VERSION.
    """

    old_version = state.get("version", 0)

    if old_version < 2:
        # Ensure new player fields exist
        p = state.get("player", {})
        p.setdefault("visited_rooms", [])
        p.setdefault("joined_tobias", False)
        p.setdefault("bosses_spared", 0)
        p.setdefault("bosses_defeated", 0)
        p.setdefault("attack", 1)
        p.setdefault("health", 20)
        state["player"] = p

        # Ensure flags exist
        flags = state.setdefault("flags", {})
        flags.setdefault("scene1_completed", False)
        flags.setdefault("scene2_completed", False)
        flags.setdefault("gameplay_started", False)
        flags.setdefault("opening_sequence_completed", False)
        state["flags"] = flags

        # Ensure locations exist as a dict
        state.setdefault("locations", {})

    if old_version < 3:
        for _, locdata in state.get("locations", {}).items():
            locdata.setdefault("is_locked", False)
            locdata.setdefault("items", [])
            locdata.setdefault("objects", {})

    state["version"] = SAVE_VERSION
    return state
#-----------------------------------

# ========= State extraction & patching =========
def _collect_save_state():
    """
    Return a compact, JSON-serializable dict representing dynamic game state.
    Convert non-serializable types (like set) to lists.
    """
    # Collect player core fields (only dynamic ones)
    player_state = {
        "name": player.get("name"),
        "location": player.get("location"),
        "inventory": list(player.get("inventory", [])),
        "bosses_defeated": player.get("bosses_defeated"),
        "bosses_spared": player.get("bosses_spared"),
        "alive": player.get("alive"),
        "joined_tobias": player.get("joined_tobias"),
        "visited_rooms": list(player.get("visited_rooms", [])),
        "health": player.get("health"),
        "attack": player.get("attack"),
    }

    # Minimal bosses state (alive + health). You can expand if needed.
    bosses_state = {
        name: {"alive": data.get("alive"), "health": data.get("health")}
        for name, data in bosses.items()
    }

    # Collect flags explicitly (only the flags you use)
    flags_state = {
        "tobias_isSummoned": tobias_isSummoned,
        "loop_broken": loop_broken,
        "power_on": power_on,
        "quitter": quitter,
        "first_boss_triggered": first_boss_triggered,
        "second_boss_triggered": second_boss_triggered,
        "third_boss_triggered": third_boss_triggered,
        "ticket_is_claimed": ticket_is_claimed,
        "keycard_is_claimed": keycard_is_claimed,
        "opening_sequence_completed": opening_sequence_completed,
        "scene1_completed": scene1_completed,
        "gameplay_started": gameplay_started,
        "scene2_completed": scene2_completed
    }

    # Dynamic parts of locations: locks and mutable object states
    locations_state = {}

    for loc_name, loc in locations.items():
        entry = {}

        # Always save lock state
        entry["is_locked"] = bool(loc.get("is_locked", False))

        # Save items
        entry["items"] = list(loc.get("items", []))

        # Save object state
        obj_states = {}
        for obj_key, obj in loc.get("objects", {}).items():
            obj_entry = {}
            for k in ("puzzle_solved", "opened", "hit_counter"):
                obj_entry[k] = obj.get(k, None)
            obj_entry["items"] = list(obj.get("items", []))
            obj_states[obj_key] = obj_entry
        entry["objects"] = obj_states

        locations_state[loc_name] = entry



    return {
        "version": SAVE_VERSION,
        "player": player_state,
        "bosses": bosses_state,
        "flags": flags_state,
        "locations": locations_state,
        "metadata": {
            "saved_at": time.ctime()
        }
    }

def _apply_save_state(state: dict):
    """
    Apply saved state *to the existing in-memory structures* (do not replace them).
    This avoids wiping code-defined defaults and new content.
    """
    # Player
    p = state.get("player", {})
    if p:
        player["name"] = p.get("name", player.get("name"))
        player["location"] = p.get("location", player.get("location"))
        player["inventory"] = p.get("inventory", list(player.get("inventory", [])))
        player["bosses_defeated"] = p.get("bosses_defeated", player.get("bosses_defeated"))
        player["bosses_spared"] = p.get("bosses_spared", player.get("bosses_spared"))
        player["alive"] = p.get("alive", player.get("alive"))
        player["joined_tobias"] = p.get("joined_tobias", player.get("joined_tobias"))
        player["visited_rooms"] = set(p.get("visited_rooms", list(player.get("visited_rooms", []))))
        player["health"] = p.get("health", player.get("health"))
        player["attack"] = p.get("attack", player.get("attack"))

    # Bosses
    bs = state.get("bosses", {})
    for name, data in bs.items():
        if name in bosses:
            if "alive" in data:
                bosses[name]["alive"] = data["alive"]
            if "health" in data:
                bosses[name]["health"] = data["health"]

    # Flags
    fl = state.get("flags", {})
    if fl:
        global tobias_isSummoned, loop_broken, power_on, quitter
        global first_boss_triggered, second_boss_triggered, third_boss_triggered
        global ticket_is_claimed, keycard_is_claimed
        global opening_sequence_completed, scene1_completed, gameplay_started, scene2_completed

        tobias_isSummoned = fl.get("tobias_isSummoned", tobias_isSummoned)
        loop_broken = fl.get("loop_broken", loop_broken)
        power_on = fl.get("power_on", power_on)
        quitter = fl.get("quitter", quitter)
        first_boss_triggered = fl.get("first_boss_triggered", first_boss_triggered)
        second_boss_triggered = fl.get("second_boss_triggered", second_boss_triggered)
        third_boss_triggered = fl.get("third_boss_triggered", third_boss_triggered)
        ticket_is_claimed = fl.get("ticket_is_claimed", ticket_is_claimed)
        keycard_is_claimed = fl.get("keycard_is_claimed", keycard_is_claimed)
        opening_sequence_completed = fl.get("opening_sequence_completed", opening_sequence_completed)
        scene1_completed = fl.get("scene1_completed", scene1_completed)
        gameplay_started = fl.get("gameplay_started", gameplay_started)
        scene2_completed = fl.get("scene2_completed", scene2_completed)

    # Locations (patch only dynamic parts)
    locs = state.get("locations", {})
    for loc_name, loc_state in locs.items():
        if loc_name not in locations:
            # ignore unknown rooms (keeps compatibility)
            continue
        loc = locations[loc_name]
        if "is_locked" in loc_state:
            loc["is_locked"] = loc_state["is_locked"]
        if "items" in loc_state:
            loc["items"] = loc_state["items"]
        if "objects" in loc_state:
            for obj_key, obj_state in loc_state["objects"].items():
                if "objects" not in loc or obj_key not in loc["objects"]:
                    # skip unknown objects
                    continue
                obj = loc["objects"][obj_key]
                for k, v in obj_state.items():
                    obj[k] = v
#------------------------------------------------

# ========= Public API: save / load / list / delete =========
def save_game(filename: str):
    filename = _sanitize_filename(filename)
    filename = _ensure_json_extension(filename)
    filepath = _filepath_for(filename)

    save_key = input("Set a save key for this file (remember it!): ").strip()
    if not save_key:
        slowprint(color_text("Save cancelled: empty key.", "yellow"))
        return False

    encrypted_key = fernet.encrypt(save_key.encode()).decode()

    save_state = _collect_save_state()
    save_state["auth"] = {"encrypted_key": encrypted_key}

    try:
        _atomic_write_json(filepath, save_state)
    except Exception as e:
        slowprint(color_text(f"\nFailed to write save: {e}", "red"))
        return False

    # ledger update
    try:
        _update_ledger(filename, encrypted_key, save_state["metadata"]["saved_at"], player.get("name"))
    except Exception:
        slowprint(color_text("\nWarning: could not update developer ledger.", "yellow"))

    slowprint(color_text(f"\nSaved to {filename}. Keep your save key safe!", "green"))
    return True

def load_game(filename: str):
    """
    Load a save file — sanity-check and then patch existing in-memory state.
    Requires the correct save key (hashed match).
    """
    filename = _sanitize_filename(filename)
    filename = _ensure_json_extension(filename)
    filepath = _filepath_for(filename)

    if not os.path.exists(filepath):
        slowprint(color_text("\nThat save file does not exist.", "red"))
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            save_state = json.load(f)
    except Exception as e:
        slowprint(color_text(f"\nFailed to read save: {e}", "red"))
        return False

    encrypted_key = save_state.get("auth", {}).get("encrypted_key")
    if not encrypted_key:
        slowprint(color_text("\nSave file missing encrypted key; cannot load.", "red"))
        return False

    entered = input("Enter save key: ").strip()

    try:
        real_key = fernet.decrypt(encrypted_key.encode()).decode()
    except:
        slowprint(color_text("\nSave file is corrupted or unreadable.", "red"))
        return False

    if entered != real_key:
        slowprint(color_text("\nIncorrect save key!", "red"))
        return False



    # Optional: check save version compatibility
    version = save_state.get("version", 0)
    if version != SAVE_VERSION:
        slowprint(color_text(f"\nMigrating save (v{version} → v{SAVE_VERSION})...", "yellow"))
        save_state = migrate_save(save_state)

    # Apply the saved dynamic state
    try:
        _apply_save_state(save_state)
    except Exception as e:
        slowprint(color_text(f"\nFailed to apply save data: {e}", "red"))
        return False

    slowprint(color_text(f"\nSave file '{filename}' loaded successfully!", "green"))
    return True

def list_all_saves():
    """List all files in the SAVE_DIR sorted."""
    try:
        files = sorted(os.listdir(SAVE_DIR))
    except Exception:
        slowprint("\nNo save files found.", 0.02)
        return

    if not files:
        slowprint("\nNo save files found.", 0.02)
        return

    slowprint("\nAvailable save files:", 0.02)
    for f in files:
        slowprint("- " + f, 0.02)

def delete_save(filename: str):
    """
    Delete a save only if the user provides the correct save key.
    Also removes the ledger entry for that exact filename.
    """
    filename = _sanitize_filename(filename)
    filename = _ensure_json_extension(filename)
    filepath = _filepath_for(filename)

    if not os.path.exists(filepath):
        slowprint(color_text("That save file does not exist.", "red"))
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            save_state = json.load(f)
    except Exception as e:
        slowprint(color_text(f"Could not read save file: {e}", "red"))
        return False

    encrypted_key = save_state.get("auth", {}).get("encrypted_key")
    if not encrypted_key:
        slowprint(color_text("Save file missing encryption info; cannot delete.", "red"))
        return False


    entered = input("Enter the save key to delete this file: ").strip()
    try:
        real_key = fernet.decrypt(encrypted_key.encode()).decode()
    except:
        slowprint("Save file corrupted or unreadable.", "red")
        return False

    if entered != real_key:
        slowprint("Incorrect save key!", "red")
        return False


    confirm = input(f"Are you SURE you want to permanently delete '{filename}'? (yes/no): ").strip().lower()
    if confirm != "yes":
        slowprint(color_text("Deletion cancelled.", "yellow"))
        return False

    try:
        os.remove(filepath)
    except Exception as e:
        slowprint(color_text(f"Failed to remove save file: {e}", "red"))
        return False

    # Remove exact filename lines from the ledger (safe removal)
    if os.path.exists(DEV_LEDGER):
        try:
            with open(DEV_LEDGER, "r", encoding="utf-8") as devfile:
                lines = devfile.readlines()
            with open(DEV_LEDGER, "w", encoding="utf-8") as devfile:
                for line in lines:
                    # ledger format: player | filename | hash | timestamp
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 2 and parts[1] == filename:
                        # skip this line (delete)
                        continue
                    devfile.write(line)
        except Exception:
            slowprint(color_text("Warning: could not fully update developer ledger.", "yellow"))

    slowprint(color_text(f"Save file '{filename}' deleted.", "green"))
    return True
#------------------------------------------------------------

#========= Game Play Area =========
#World Locations
locations = {
    "lobby": {
        "description": "\nA dust filled lobby filled with broken ticket machines, tattered posters of arcade heroes, and a battered prize counter",
        "connected": ["backroom", "arcade room floor", "cafeteria"],
        "items": [],
        "is_locked": False,
        "required_item": None,
        "requires_power": False
        },

    "backroom": {
        "description": "\nA room filled with tangled bunches of wires, old cleaning supplies, and an unhealthy amount of cobwebs",
        "connected":["lobby", "control room"],
        "items": [],
        "is_locked": True,
        "required_item": "key",
        "requires_power": False
        },

    "control room":{
        "description": "\nRows upon rows of abandoned and ignored CRT machines with one displaying broken code..",
        "connected": ["backroom", "guard room"],
        "items": [],
        "is_locked": True,
        "required_item": "keycard",
        "requires_power": True
        },

    "guard room":{
        "description": "\nA room filled with empty rusted lockers and floors littered with tattered uniforms",
        "connected": ["control room"],
        "items": [],
        "is_locked": True,
        "required_item": "level 2 keycard",
        "requires_power": False
    },

    "arcade room floor":{
        "description": "\nArcade machines and abandoned table games line the dust and cable covered floor",
        "connected": ["lobby", "big b arena", "cafeteria"],
        "items": [],
        "is_locked": True,
        "required_item": None,
        "requires_power": True
        },

    "big b arena": {
        "description": "\nAn arena with walls built by abandoned arcade machines and broken tables",
        "connected": ["arcade room floor", "maze"],
        "items": [],
        "is_locked": True,
        "required_item": "arena token",
        "requires_power": False
        },
    
    "maze": {
        "description": "\nYou stand at the entrance of a massive, old kids play maze. Just looking at it makes you feel light-headed.",
        "connected": ["big b arena", "throne room"],
        "items": [],
        "is_locked": True,
        "required_item": "maze key",
        "requires_power": False
        },

    "cafeteria": {
        "description": "\nAn old cafeteria with broken tables and chairs scattered around.",
        "connected": ["arcade room floor", "lobby"],
        "items": [],
        "is_locked": False,
        "required_item": None,
        "requires_power": False
        },
    
    "throne room": {
        "description": "\nA dark room with a large throne made of arcade machines and broken tables, and the pixelated souls of those who once were",
        "connected": ["maze"],
        "items": [],
        "is_locked": True,
        "required_item": "throne key",
        "requires_power": False
    },
}

locations["lobby"]["objects"] = {
    "ticket machine": {
        "description": "\nAn old ticket machine, it seems to be broken but maybe you can fix it.",
        "interactable": True,
        "puzzle": None,
        "items": ["ticket"]
        },
        
    "prize counter": {
        "description": "\nA dusty prize counter with a few tattered prizes left on the shelves.",
        "interactable": True,
        "puzzle": None,
        "items": ["key"]
        },

    "cleaning cart": {
        "description": "\nAn old cleaning cart with some supplies on it and a sticky note on the side. It says 'Remember to set the fuses to equal 100 V - Robert'",
        "interactable": True,
        "puzzle": None
        }
}

locations["control room"]["objects"] = {
    "terminal": {
        "description": "\nAn old green terminal, it seems to be flickering some text..",
        "interactable": True,
        "puzzle": "file_restore",
        "puzzle_solved": False
        },

    "monitor": {
        "description": "\nA flickering CRT monitor displays some broken code.",
        "interactable": True,
        "puzzle": "syntax",
        "puzzle_solved": False
        },

    "dispenser": {
        "description": "\nAn old soda dispenser, it seems to be out of order. There's another sticky note that says, 'Remember to fix token dispensing terminal, ''power restored successfully'' - Robert'",
        "interactable": True,
        "puzzle": None,
        "items": ["purified_water"]
        },
} 

locations["backroom"]["objects"] = {
    "generator": {
        "description": "\nAn old, dingy generator sits in the corner of the storage closet.",
        "interactable": True,
        "puzzle": "generator",
        "puzzle_solved": False
        },
}

locations["cafeteria"]["objects"] = {
    "cafeteria table": {
        "description": "\nA broken cafeteria table with some old food crumbs, and a keycard on it.",
        "interactable": True,
        "puzzle": None
        },
    
    "dispenser": {
        "description": "\nAn old soda dispenser, it seems to be out of order. Theres a sticky note that says, 'Remember to fix water dispenser, terminal is left behind one of the arcade machines by the arcade floor - Robert'",
        "interactable": True,
        "items": ["purified_water"]
        },
}

locations["arcade room floor"]["objects"] = {
    "arcade machine": {
        "description": "\nAn old arcade machine with a token slot. It seems to be broken.",
        "interactable": True,
        "puzzle": "bootloader",
        "puzzle_solved": False
        },
    
    "dispenser": {
        "description": "\nAn old soda dispenser, it seems to be out of order. Right under it is an old PC terminal flashing a message. 'EOF - Terminate Connection by sending EOF signal'",
        "interactable": True,
        "puzzle": "eof_input",
        "puzzle_solved": False,
        "items": ["purified_water"]
        },
    
    "maze entrance": {
        "description": "\nThe entrance to a massive kids play maze. It looks dark and foreboding.",
        "interactable": True,
        "puzzle": "signal_interrupt",
        "puzzle_solved": False
        }
}

locations["big b arena"]["objects"] = {
    "observation deck":{
        "description": "An observation deck looking out over the arena, looks like something the security guards would be in to look over everyone...",
        "interactable": True,
        "puzzle": None,
        "items": ["level 2 keycard"]
    },
}

locations["guard room"]["objects"] = {
    "guard locker": {
        "description": "An old and beat up green metal locker, by the looks of it, you see something shiny through the cracks of the metal door",
        "interactable": True,
        "puzzle": None,
        "items": ["throne key"],
        "hit_counter": 0,
        "opened": False
    }
}

#Define Bosses
bosses = {
    "Road-Boxer": {
        "area": "arcade room floor", 
        "alive": True, 
        "type": "fighter_ai", 
        "health": 300, 
        "attack": 38},

    "Angry-Monkey": {
        "area": "big b arena", 
        "alive": True, 
        "type": "barrel_mech",
        "health": 400, 
        "attack": 40},

    "Pack-Dude": {
        "area": "maze", 
        "alive": True, 
        "type": "maze_ghost", 
        "health": 350, 
        "attack": 30},

    "Tobias the Wizard": {
        "area": "throne room", 
        "alive": True, 
        "type": "final_boss", 
        "health": 500,
        "attack": 52},
}

#Define boss option patterns and individual weights
boss_patterns = {
    "Road-Boxer": {"hit": 0.5, "heal": 0.3, "dodge": 0.2},
    "Angry-Monkey": {"hit": 0.6, "heal": 0.2, "dodge": 0.1},
    "Pack-Dude": {"hit": 0.4, "heal": 0.3, "dodge": 0.3},
}

#Define Player Stats
player = {
    "name": None,
    "location": "lobby",
    "inventory": [],
    "bosses_defeated": 0,
    "bosses_spared": 0,
    "alive": True,
    "joined_tobias": False,
    "visited_rooms": {"lobby"},
    "health": 150,
    "attack": 65
    }

#=========== Global Flag Initializations ===========
#General Gameplay Flags
tobias_isSummoned = False
loop_broken = False
power_on = False
quitter = False
first_boss_triggered = False
second_boss_triggered = False
third_boss_triggered = False
ticket_is_claimed = False
keycard_is_claimed = False

#Dialogue Sequencing Flags
opening_sequence_completed = False
scene1_completed = False
gameplay_started = False
scene2_completed = False
#---------------------------------------------------

# ========= Define Helper Functions =========
#Utility: Simulate a Dice Roll
def dice_roll():
    """Simulate a dice roll"""
    return random.randint(1, 20)

#Utility: Separator Line
def sep():
    """Print a separator line"""
    print("\n" + "-" * 60 + "\n")

#Utility: Short Pause
def pause(sec = 0.6):
    """Pause the code from running temporarily"""
    time.sleep(sec)

#Utility: Typewriter Style Printing
def slowprint(text, delay = 0.02):
    """Simulate typewriter style printing"""
    for ch in text:
        print(ch, end = "", flush = True)
        time.sleep(delay)
    print()

#Utility: Glitched Typewriter Style Printing
def slowprint_glitch(text, color = "end", delay = 0.02, intensity = 0.02):
    """Typewriter style printing with glitched characters"""
    for ch in text:
        if random.random() < intensity and ch.isalpha():
            print(color_text(random.choice(["@", "#", "$", "%", "&", "*"]), color), end = "", flush  = True)
        else:
            print(color_text(ch, color), end = "", flush = True)
        time.sleep(delay)
    print()

#Utility: Glitched Text Printer
def glitch_text(text, intensity = 0.02): #REMEMBER TO SURROUND BY A PRINT STATEMENT BECAUSE OF RETURN
    """Print text with some characters replaced by symbols to emulate corruption"""
    glitched = ""
    for ch in text:
        if random.random() < intensity and ch.isalpha():
            glitched += random.choice(["@", "#", "$", "%", "&", "*"])
        else:
            glitched += ch
    return glitched

#Utility: Flickering Text
def flicker_text(text, times = 5, delay = 0.2):
    """Print text and clear the screen to emulate flickering text"""
    for i in range(times):
        print("\033c", end = "", flush = True)
        time.sleep(delay/2)
        print(text, flush = True)
        time.sleep(delay/2)
    print()

#Utility: Fake Glitch Sequence
def fake_glitch_sequence():
    """Simulate a fake glitch sequence for immersion"""
    slowprint(color_text(">>> SYSTEM REBOOTING <<<", "red"), 0.04)
    pause()
    for i in range(4):
        print(glitch_text("LOADING MEMORY MODULE...", 0.4))
        time.sleep(0.4)
    flicker_text(color_text(">>> SYSTEM REBOOTED <<<", "green"), 5, 0.25)

#Utility: ANSI Color Helper
def color_text(text, color = "end"):
    """Return a colorized string of text"""
    colors = {
        "bold": "\033[1m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "italic": "\033[3m",
        "end": "\033[0m"
        }
    return f"{colors.get(color, '')}{text}{colors['end']}"

# Utility: Normalize Object Names
def normalize_obj_name(name: str) -> str:
    """Return multiple normalized variants (underscore, no-space) to match keys."""
    name = name.strip().lower()
    return name.replace(" ", "_"), name.replace(" ", ""), name.replace("_", " ")

#Utility: Check if Player has Item
def has_item(item):
    """Check if the player has an item in their inventory"""
    global player
    return item in player["inventory"]

#Utility: Unlock a Room
def unlock_room(room_name):
    """Check if the player has unlocked a room by matching room key names to their respective dictionaries"""
    global locations
    #Normalize spaces and undescorse
    if room_name in locations:
        locations[room_name]["is_locked"] = False
        return
    alt = room_name.replace("_", " ")
    if alt in locations:
        locations[alt]["is_locked"] = False
        return
    alt2 = room_name.replace(" ", "_")
    if alt2 in locations:
        locations[alt2]["is_locked"] = False
        return
    #Fallback: no-op if name not found (prevents KeyError)
    slowprint(color_text(f"DEBUG: unlock_room could not find '{room_name}'", "red"), 0.01)
#-------------------------------------

# ========= Dev Console =========
#Act as a seperator for player inputs
def get_player_input(prompt="> "):
    while True:
        cmd = input(prompt).strip()
        if cmd.startswith("/"):
            run_dev_command(cmd[1:])
            # <-- stay in the loop, re-prompt safely
            continue
        return cmd

def run_dev_command(cmd):
    parts = cmd.split()
    if not parts:
        print("\n[DEV] Empty command.\n")
        return

    op = parts[0].lower()
    args = parts[1:]

    # Helper: Usage printer
    def usage(msg):
        print(f"\n[DEV] {msg}")
        return

    # Command: help
    if op == "help":
        print("\n[DEV] Available commands:")
        print("  /help")
        print("  /tp <room>")
        print("  /give <item>")
        print("  /hp <number>")
        print("  /flag <flag_name> <true/false>")
        print("  /map")
        print("  /revealkey <filename>")
        print("  /bs <boss_condition> <value>")
        return

    # Command: tp (teleport)
    elif op == "tp":
        if len(args) < 1:
            return usage("Usage: /tp <room_name>\n")
        room = " ".join(args)
        if room in locations:
            player["location"] = room
            print(f"\n[DEV] Teleported to {room}\n")
        else:
            print("\n[DEV] Unknown room.\n")
        return

    # Command: give item
    elif op == "give":
        if len(args) < 1:
            return usage("Usage: /give <item_name>\n")
        item = " ".join(args)
        player["inventory"].append(item)
        print(f"\n[DEV] Added item: {item}\n")
        return

    # Command: hp
    elif op == "hp":
        if len(args) < 1:
            return usage("Usage: /hp <amount>\n")
        try:
            new_hp = int(args[0])
            player["health"] = new_hp
            print(f"\n[DEV] Player HP set to {new_hp}\n")
        except ValueError:
            print("\n[DEV] HP must be a number.\n")
        return

    elif op == "attack":
        if len(args) < 1:
            return usage("Usage: /attack <amount> \n")
        try:
            new_attack = int(args[0])
            player["attack"] = new_attack
            print(f"\n[DEV] Player Attack set to {new_attack}\n")
        except ValueError:
            print("\n[DEV] Attack must be a number\n")
        return

    # Command: flag
    elif op == "flag":
        if len(args) < 2:
            return usage("Usage: /flag <flag_name> <true/false>\n")

        flag_name = args[0]
        val = args[1].lower()

        if val not in ("true", "false"):
            return usage("Value must be true or false.\n")

        bool_val = (val == "true")

        if flag_name not in globals():
            print(f"\n[DEV] Warning: Flag '{flag_name}' does not exist. Creating it.\n")
        
        globals()[flag_name] = bool_val
        print(f"\n[DEV] Set flag {flag_name} = {bool_val}\n")
        return
    
    elif op == "bs":
        if len(args) < 2:
            return usage("Usage: /boss_set <boss condition> <number>\n")
        
        boss_flag = args[0]
        raw_val = args[1]

        try:
            val = int(raw_val)
        except ValueError:
            return usage("\nValue mmust be an integer\n")
        
        

        if val < 0 or val > 3:
            return usage("\nValue must be a reasonable number (0-3)\n")
        
        if boss_flag not in player:
            print(f"\n[DEV] '{boss_flag}' is not a valid player boss field.\n")
            print("\nValid fields: bosses_defeated, bosses_spared\n")
            return
        
        player[boss_flag] = val
        print(f"\n[DEV] Set player {boss_flag} to {val}\n")
        return
    
    # Command: map
    elif op == "map":
        draw_bigb_map(player, locations, bosses, power_on)
        return

    # Command: revealkey
    elif op == "revealkey":
        if len(args) < 1:
            return usage("Usage: /revealkey <filename>\n")
        reveal_save_key(args[0])
        return

    # Unknown command
    else:
        print(f"\n[DEV] Unknown command '{op}'. Type /help for a list.\n")
        return
#--------------------------------

# ========= Build the Game Map ========
#Create the map markers
def _mark(room_key, player, locations, bosses, power_on):
    """Return a combined marker string showing multiple room states."""
    room = locations.get(room_key, {})
    markers = []

    #If the room requires power append marker "*" to it
    if room.get("requires_power") and not power_on:
        return "*"

    # If the room has the players position in it, append marker P to it
    if player["location"] == room_key:
        markers.append("P")

    # If the room has a boss presence, append marker B to it
    if any(bosses[b]["area"] == room_key and bosses[b]["alive"] for b in bosses):
        markers.append("B")

    # If the room has a locked door, append marker "X" to it
    if room.get("is_locked"):
        markers.append("X")

    # If a room has an unsolved puzzle, append "?"
    if "objects" in room:
        unsolved_puzzles = any(
            obj.get("puzzle") and not obj.get("puzzle_solved", False)
            for obj in room["objects"].values()
        )
        if unsolved_puzzles:
            markers.append("?")

    # If a room or its objects have unclaimed items, append "$"
    has_unclaimed_items = False

    # Room-level items
    if "items" in room:
        for item in room["items"]:
            if item not in player["inventory"]:
                has_unclaimed_items = True
                break

    # Object-level items
    if not has_unclaimed_items and "objects" in room:
        for obj in room["objects"].values():
            if "items" in obj:
                for item in obj["items"]:
                    if item not in player["inventory"]:
                        has_unclaimed_items = True
                        break
                if has_unclaimed_items:
                    break

    if has_unclaimed_items:
        markers.append("$")


    #If the player has visited the room, append marker "·" to it
    if room_key in player.get("visited_rooms", set()) and "P" not in markers:
        markers.append("·")

    #Return the joined marker if any of the above apply, else return a blank string
    return "".join(markers) if markers else " "

#Build map markers
def draw_bigb_map(player, locations, bosses, power_on=False, use_color=True):
    """
    Print a boxed ASCII map with the following:
    - player: player dict
    - locations: locations dict
    - bosses: bosses dict
    - power_on: bool
    - use_color: if True and color_text exists, uses it for highlights
    """
    
    #Safe color text wrapper
    def col(text, c):
        try:
            if use_color:
                return color_text(text, c)
        except Exception:
            return text
        return text

    #Define map markers
    m_control = _mark("control room", player, locations, bosses, power_on)
    m_backroom = _mark("backroom", player, locations, bosses, power_on)
    m_lobby = _mark("lobby", player, locations, bosses, power_on)
    m_arcade = _mark("arcade room floor", player, locations, bosses, power_on)
    m_arena = _mark("big b arena", player, locations, bosses, power_on)
    m_cafe = _mark("cafeteria", player, locations, bosses, power_on)
    m_maze = _mark("maze", player, locations, bosses, power_on)
    m_throne = _mark("throne room", player, locations, bosses, power_on)
    m_guard = _mark("guard room", player, locations, bosses, power_on)

    #Build each line of the boxed map
    lines = []
   
    lines.append("  ┌────────────────────────────────────┐")
   
    lines.append(f"  │CONTROL ROOM[{m_control:>3}]───BACKROOM[{m_backroom:>3}]   │")
   
    lines.append(f"  │    │                  │            │")
   
    lines.append(f"  │ GUARD ROOM[{m_guard:>3}]       │            │")
   
    lines.append(f"  │                       │            │")   

    lines.append(f"  │ CAFETERIA[{m_cafe:>3}]────────LOBBY[{m_lobby:>3}]   │")
   
    lines.append(f"  │    │                  │            │")

    lines.append(f"  │    │                  │            │")
   
    lines.append(f"  │    └─ARCADE ROOM FLOOR[{m_arcade:>3}]        │")

    lines.append(f"  │       ┌────┘                       │")

    lines.append(f"  │       │                            │")
   
    lines.append(f"  │ BIG B ARENA[{m_arena:>3}]──MAZE[{m_maze:>3}]        │")
   
    lines.append(f"  │           ┌────────┘               │")

    lines.append(f"  │           │                        │")

    lines.append(f"  │           │                        │")

    lines.append(f"  │        THRONE ROOM[{m_throne:>3}]            │")

    lines.append(f"  │                                    │")

    lines.append("  └────────────────────────────────────┘")
    
    #Colors for markers
    color_map = {
        "P": "cyan",
        "B": "red",
        "X": "yellow",
        "*": "blue",
        "?": "magenta",
        "$": "green",
        "·": "white",
    }

    #Print lines with optional coloring for markers
    def colorize_marker_block(match):
        content = match.group(1)
        colored = ""
        for ch in content:
            if ch in color_map:
                colored += color_text(ch, color_map[ch])
            else:
                colored += ch
        return f"[{colored}]"

    for line in lines:
        if use_color:
            line = re.sub(r"\[([^\]]+)\]", colorize_marker_block, line)
        print(line)

    #Legend
    print()
    print("\nLegend: \nP = player  \n· = visited  \nX = locked  \nB = boss alive  \n* = power required \n? = unsolved puzzle \n$ = contains item")
#-------------------------------------

# ========= Movement and Lock Logic =========
def move_to_room(current_room, target_room, inventory):
    """Move the player to a room, tracking what's in their inventory, current room they're in, and the target room in their movement"""
    global player, locations, power_on

    # Check if the room exists
    if target_room not in locations:
        slowprint("\nThat room doesn't exist.", 0.02)
        return current_room

    # Check if the room is connected
    if target_room not in locations[current_room]["connected"]:
        slowprint("\nYou can't go from here to there.", 0.02)
        return current_room

    room_data = locations[target_room]

    # Check power requirement
    if room_data.get("requires_power") and not power_on:
        slowprint("\nThe power is out, you can't go there yet.", 0.02)
        return current_room

    # Check lock status
    if room_data["is_locked"]:
        required_item = room_data.get("required_item")
        if required_item and required_item in inventory:
            slowprint(color_text(f"\nYou use the {required_item} to unlock the door.", "magenta"), 0.02)
            room_data["is_locked"] = False
            #Consume required item upon use
            inventory.remove(required_item)
            slowprint("\nThe door creaks open. You can now enter.", 0.02)
        else:
            slowprint(color_text("\nThe door is locked. You need something to open it.", "red"), 0.02)
            return current_room

    # Move player
    player["location"] = current_room = target_room
    if current_room not in player["visited_rooms"]:
        player["visited_rooms"].add(current_room)
        slowprint(color_text(f"\nYou feel a chill as you enter the, {current_room.upper()}, for the first time", "blue"), 0.04)
    else:
        slowprint(f"\nYou enter the {current_room}.", 0.02)
    slowprint(room_data["description"], 0.02)
    #Return target_room
    return target_room
#--------------------------------------------

# ========= Define boss encounter and fight logic =========
#Check for boss encounter
def check_for_boss(current_room):
    """Check for a boss in a given room"""
    for boss_name, boss_data in bosses.items():
        if boss_name == "Tobias the Wizard":
            continue  
        if boss_data["area"] == current_room and boss_data["alive"]:
            run_boss_encounter(boss_name, boss_data)
            break

#Define boss attack patterns using weights for a more interactive system
def boss_move_pattern(boss_name, boss_health, player_health):
    pattern = boss_patterns.get(boss_name, {"hit": 0.5, "heal": 0.2, "dodge": 0.1})
    if boss_health > 150:
        pattern["heal"] -= 0.1
        pattern["hit"] += 0.2
        pattern["dodge"] += 0.1
    if boss_health < 50:
        pattern["heal"] += 0.5
        pattern["dodge"] += 0.2
        pattern["hit"] -= 0.3
    if player_health < 70:
        pattern["heal"] -= 0.5
        pattern["dodge"] -= 0.2
        pattern["hit"] += 0.5
        
    total = sum(pattern.values())
    choices, weights = zip(*[(k, v / total) for k, v in pattern.items()])

    return random.choices(choices, weights = weights, k=1)[0]

#Boss Encounter Logic
def run_boss_encounter(name, data):
    """Run the boss encounter for the given boss with their personalized flavor text"""
    global first_boss_triggered, second_boss_triggered, third_boss_triggered, player_name
    pause()

    # First boss special dialogue
    if not first_boss_triggered and name == "Road-Boxer":
        first_boss_triggered = True
        sep()
        slowprint(color_text("you see a distorted figure approaching you...\n", "italic"), 0.02)
        pause()
        slowprint(color_text("you see Tobias, holding someone in his hands...\n", "italic"), 0.02)
        slowprint(color_text("you run towards them in an attempt to help the figure in his grasp...", "italic"), 0.04)
        sep()
        slowprint(color_text("STOP!! LEAVE HIM ALONE!!", "blue"), 0.04)
        slowprint_glitch("YAY!!! ANOTHER FRIEND TO PLAY WITH!!", "cyan", 0.02, 0.03)
        slowprint_glitch("HERE, LET ME SHOW YOU HOW MUCH FUN WE CAN HAVE!!", "cyan", 0.02, 0.03)
        slowprint(color_text("you hear a familiar voice beneath the distortion...", "italic"), 0.02)
        pause()
        slowprint(color_text(f"{player['name']}...? Is that you?", "yellow"), 0.02)
        pause()
        slowprint(color_text("CHAD?? WHAT HAPPENED TO YOU...", "blue"), 0.02)
        pause()
        slowprint(color_text("Tobias... he... he changed me...", "yellow"), 0.02)
        pause()
        slowprint_glitch("Help me... please... it hurts so bad...", "yellow", 0.02, 0.03)
        sep()
        slowprint(color_text("Chad completely pixelates and becomes...\n", "italic"), 0.02)
        slowprint(color_text(f"{name}", "red"), 0.1)
        sep()
        slowprint_glitch("HOPE YOU TOO HAVE FUN TOGETHER!! I HAVE MORE FRIENDS TO MAKE!!", "cyan", 0.04, 0.03)
        slowprint(color_text("\nTobias runs away for now...", "italic"), 0.04)
    
    if not second_boss_triggered and name == "Angry-Monkey":
        second_boss_triggered = True
        sep()
        slowprint(color_text("As you enter the arena, you see Brad posing atop a platform...", "italic"), 0.04)
        sep()
        slowprint(color_text("Brad? Is that you up there?", "blue"), 0.02)
        pause()
        slowprint_glitch("Yeah, it's me.", "red", 0.02, 0.03)
        slowprint_glitch("I guess you found me...", "red", 0.02, 0.02)
        slowprint(color_text("The heck you mean by that?", "blue"), 0.02)
        slowprint_glitch("Tobias... he changed me...", "red", 0.02, 0.03)
        slowprint_glitch("And to be honest? I like it.", "red", 0.02, 0.03)
        sep()
        slowprint(color_text("\nBrad leaps down from the platform, now fully transformed into Angry-Monkey.\n", "italic"), 0.02)
        sep()
        slowprint_glitch("Because now I get to show you just how strong I really am.", "red", 0.02, 0.03)
        sep()
        slowprint(color_text("you brace yourself for the fight ahead...", "italic"), 0.04)
        slowprint(color_text("As Brad becomes...\n", "italic"), 0.04)
        slowprint(color_text(f"{name}", "red"), 0.1)
    
    if not third_boss_triggered and name == "Pack-Dude":
        third_boss_triggered = True
        sep()
        slowprint(color_text("you enter the center of the maze to find your final friend curled in a ball...", "italic"), 0.04)
        sep()
        slowprint(color_text("Arthur? Is that you?", "blue"), 0.02)
        pause()
        slowprint_glitch("Huh? Who's there?", "green", 0.02, 0.03)
        slowprint_glitch("Oh... it's you...", "green", 0.02, 0.02)
        slowprint(color_text("Arthur, it's me. Our friends are... gone... because of Tobias...", "blue"), 0.02)
        slowprint_glitch("I know...", "green", 0.02, 0.03)
        slowprint_glitch("Tobias he... he promised me that if I came with him, I'd be safe...", "green", 0.02, 0.03)
        slowprint_glitch("But now... I don't know...", "green", 0.02, 0.02)
        slowprint_glitch("I just want this to end...he never told me it would hurt this badly...", "green", 0.02, 0.02)
        slowprint_glitch("Please... don't let me go...", "green", 0.02, 0.03)
        sep()
        slowprint(color_text("As he says that... Arthur slowly transforms into...\n", "italic"), 0.04)
        slowprint(color_text(f"{name}", "red"), 0.1)

    # Begin combat
    original_boss_health = data["health"]
    boss_health = original_boss_health
    player_health = player["health"]

    while boss_health > 0 and player_health > 0:
        sep()
        slowprint(color_text(f"Your HP: {player_health} | {name}'s HP: {boss_health}", "yellow"))
        action = (get_player_input("\nChoose your action (attack / dodge / run/ use item / heal): ") or "").strip().lower()

        if action == "attack":
            roll = dice_roll()
            damage = max(1, player["attack"] + random.randint(0, roll))
            slowprint(f"\nYou strike for {damage} damage!")
            boss_health -= damage

        elif action == "use item":
            #Set up purification for true route
            if "purified_water" in player["inventory"] and boss_health <= 80:
                confirm = input("\nYou have purified water. Would you like to use it to purify the soul? (yes/no): ").strip().lower()
                if confirm == "yes":
                    slowprint(color_text(f"\nYou hold out the purified water... {name} begins to shimmer.", "green"))
                    puri_result = dice_roll()
                    if puri_result >= 8:
                        slowprint(color_text(f"\n{name} has been purified. Their soul is set free.", "bold"))
                        #Mark boss dead and adjust player counts
                        data_name = name
                        #Find matching key in bosses dict and update alive flag
                        for bname in bosses:
                            if bname == name or bname.startswith(name.split()[0]):
                                bosses[bname]["alive"] = False
                                break
                        player["bosses_spared"] += 1
                        if name == "Road-Boxer":
                            slowprint(color_text("\nYou hear Chad's spirit thank you in a whisper...", "bold"))
                        elif name == "Angry-Monkey":
                            slowprint(color_text("\nYou hear Brad's spirit apologize for everything...", "bold"))
                        elif name == "Pack-Dude":
                            slowprint(color_text("\nYou wish you could comfort the last spirit as it moves on...", "bold"))

                        slowprint(color_text("\nYou run out of purified water", "yellow"))
                        player["inventory"].remove("purified_water")
                        # set boss_health to 0 to exit
                        boss_health = 0
                        break
                    else:
                        #If player fails purification, boss health increases but cap it to avoid runaway
                        slowprint(color_text(f"\nThe purification fails! {name} remains hostile.", "red"))
                        boss_health = min(int(boss_health * 1.5), original_boss_health * 2)
                        #Continue to next iteration (boss will attack)
                else:
                    slowprint(color_text("\nYou decide not to use the purified water.", "yellow"))
            else:
                slowprint("\nThe boss is not weak enough to purify or you have no water.", 0.02)
                
        elif action == "heal":
            player_heal_amount = random.randint(40, 85)
            player_health  = min(player_health + player_heal_amount, player["health"])
            slowprint(color_text(f"\nYou heal for {player_heal_amount} HP!", "green"))

        elif action == "dodge":
            roll = dice_roll()
            if roll >= 12:
                slowprint("\nYou dodge the attack!")
                player_health = player_health  # no change
                #Skip boss attack this round
                continue
            else:
                slowprint("\nYou fail to dodge...")

        elif action == "run":
            slowprint("\nYou flee the battle. The boss remains undefeated.")
            return

        # Boss makes a move (only if still alive)
        if boss_health > 0:
            boss_action = boss_move_pattern(name, boss_health, player_health)          
            if boss_action == "hit":
                damage = max(1, data["attack"] + random.randint(0, dice_roll()))
                slowprint(f"\n{name} attacks for {damage} damage!")
                player_health -= damage

            elif boss_action == "heal":
                heal_amount = random.randint(15, 40)
                boss_health = min(boss_health + heal_amount, data["health"])
                slowprint(color_text(f"\n{name} heals for {heal_amount} HP!", "green"))

            elif boss_action == "dodge":
                slowprint(color_text(f"\n{name} dodges!", "cyan"))
                boss_health += damage

        # Check player death
        if player_health <= 0:
            slowprint(color_text("\nYou were defeated...", "red"))
            player["alive"] = False
            sep()
            slowprint(color_text("This isn't how the story goes and you know it. Stick to the script.", "red"), 0.04)
            sep()

            choice = input("Retry the boss fight? (yes/no): ").strip().lower()
            if choice == "yes":
                #Reset both player and boss health and continue loop
                player["alive"] = True
                player["health"] = 150
                player_health = 150
                boss_health = original_boss_health
                fake_glitch_sequence()
                continue
            else:
                slowprint(color_text("Coward.", "red"))
                return
        else:
            # Player still alive and boss dead
            if boss_health <= 0:
                slowprint(color_text(f"\nYou defeated {name}!", "green"))
                slowprint(color_text("A part of your wishes you could've saved them instead of this...", "red"))
                # mark the boss as dead in the main bosses dict
                for bname in bosses:
                    # match by area/name fuzzily
                    if bname == name or bname.startswith(name.split()[0]):
                        bosses[bname]["alive"] = False
                        break
                player["bosses_defeated"] += 1
                # sync player HP back to main player state
                player["health"] = player_health
                break

#Final Boss Fight
def run_final_tobias_encounter():
    """Run the Tobias encounter with the given ending based on the players actions"""
    sep()
    slowprint(color_text("You finally step into the Tobias's throne room... the air thick with sorrow and exhaustion.", "italic"), 0.04)
    pause()
    slowprint_glitch("YOU'VE COME SO FAR FRIEND...", "cyan", 0.04, 0.03)
    slowprint_glitch("BUT IM AFRAID THIS IS WHERE PLAYTIME ENDS.", "red", 0.04, 0.05)
    pause()
    sep()
    slowprint(color_text("Tobias raises his hands, dark energy crackling around him.", "red"), 0.04)
    sep()
    slowprint(color_text("WHAT MORE DO YOU WANT FROM ME...?", "blue"), 0.04)
    slowprint_glitch("I JUST WANTED FRIENDS... IS THAT SO WRONG?", "cyan", 0.04, 0.05)
    slowprint(color_text("YOU'VE TAKEN MY FRIENDS, MY SANITY, MY SENSE OF NORMALCY...", "blue"), 0.04)
    slowprint(color_text("AND NOW... YOU WANT TO TAKE ME TOO?", "blue"), 0.04)
    pause(0.9)
    slowprint(color_text("I shall make sure I get to enjoy...every...last...moment I get to spend RENDING YOU APART.", "blue"), 0.1)
    sep()
    slowprint(color_text("The final battle begins...\n", "italic"), 0.04)

    spared = player["bosses_spared"]
    defeated = player["bosses_defeated"]
    inventory = player["inventory"]

    # TRUE ENDING
    if spared == 3:
        slowprint(color_text("Three glowing silhouettes appear behind you — the souls of your friends, restored.", "bold"), 0.04)
        slowprint(color_text("Together, you face Tobias as one.", "bold"), 0.04)
        slowprint_glitch("NO... NOT THIS...NOT LIKE THIS!", "red", 0.04, 0.05)
        slowprint(color_text(f"{player['name']} and their friends channel the purified energy into Tobias.", "green"), 0.04)
        slowprint(color_text("You all weaken Tobias, but he isn't going down without a fight.", "italic"), 0.04)
        sep()
        return run_tobias_battle()

    # GOOD ENDING
    elif spared + defeated == 3 and spared > 0:
        slowprint(color_text("You stand alone, but the memory of your friends gives you strength.", "italic"), 0.04)
        slowprint(color_text(f"{player['name']} faces Tobias in a final battle of will.", "yellow"), 0.04)
        slowprint_glitch("YOU THINK YOU CAN DEFEAT ME ALONE?", "CYAN", 0.04, 0.05)
        slowprint(color_text("Im not alone... I carry the strength of those you tried to take from me.", "blue"), 0.04)
        return run_tobias_battle(final_form=True)

    # SECRET ENDING
    elif "arena token" in inventory and "purified_water" not in inventory and spared == 0:
        slowprint(color_text("Tobias smiles. You feel... curious.", "italic"), 0.04)
        slowprint_glitch("YOU'VE SEEN WHAT I CAN DO. JOIN ME.", "cyan", 0.04, 0.05)
        slowprint_glitch("TOGETHER, JUST IMAGINE ALL THE FUN WE CAN HAVE.", "cyan", 0.04, 0.05)
        choice = input("Do you join Tobias? (yes/no): ").strip().lower()
        
        if choice == "yes":
            slowprint(color_text(f"{player['name']} steps forward, eyes glowing with static.", "magenta"), 0.04)
            slowprint(color_text("You become part of the arcade... forever.", "red"), 0.04)
            slowprint(color_text("SECRET ENDING UNLOCKED", "bold"), 0.1)
            player["joined_tobias"] = True
            return "loss"
        
        else:
            slowprint(color_text("You resist. Tobias snarls. The final battle begins.", "red"), 0.04)
            return run_tobias_battle(final_form=True)

    # LAME ENDING
    elif spared + defeated == 0 and quitter == True:
        slowprint(color_text("After all that work, you decide to smash open the window to the arcades outside.", "italic"), 0.04)
        slowprint(color_text("No final battle. No answers. Just... leaving.", "italic"), 0.04)
        slowprint(color_text("The arcade hums behind you, still alive with secrets.", "red"), 0.04)
        slowprint(color_text("LAME ENDING UNLOCKED", "bold"), 0.1)
        return "victory"

    # BAD ENDING
    else:
        slowprint(color_text("You face Tobias, but you're too weak. The souls you've lost weigh you down.", "red"), 0.04)
        slowprint_glitch("YOU BELONG TO ME NOW.", "cyan", 0.04, 0.05)
        slowprint(color_text(f"{player['name']}'s body collapses. Their soul flickers into the arcade's circuitry.", "red"), 0.04)
        slowprint(color_text("BAD ENDING UNLOCKED", "bold"), 0.1)
        sep()
        slowprint(color_text("This isn't how the story goes and you know it. Stick to the script.", "red"), 0.04)
        sep()
       
#Final Boss Battle Logic
def run_tobias_battle(final_form=False):
    """Run the Tobias boss fight (different stat lines depending on the bosses form)"""
    slowprint(color_text("FINAL BATTLE: TOBIAS", "cyan"), 0.02)
    boss_health = 500 if final_form else 350
    player_health = player["health"]
    boss_attack = 52 if final_form else 40

    while boss_health > 0 and player_health > 0:
        sep()
        slowprint(color_text(f"Your HP: {player_health} | Tobias's HP: {boss_health}", "yellow"))
        action = get_player_input("Choose your action (attack / dodge / heal / run): ").strip().lower()

        if action == "attack":
            roll = dice_roll()
            damage = max(1, player["attack"] + random.randint(0, roll))
            slowprint(color_text(f"\nYou strike Tobias for {damage} damage!", "green"))
            boss_health -= damage

        elif action == "heal":
            player_heal_amount = random.randint(40, 85)
            player_health  = min(player_health + player_heal_amount, player["health"])
            slowprint(color_text(f"\nYou heal for {player_heal_amount} HP!", "green"))

        elif action == "dodge":
            if dice_roll() >= 5:
                slowprint(color_text("You dodge Tobias's attack!", "cyan"))
                continue
            else:
                slowprint(color_text("You fail to dodge...", "red"))

        elif action == "run":
            slowprint(color_text("You try to run... but the arcade walls close in around you.", "red"))
            continue

        #Tobias attacks
        if boss_health > 0:
            boss_action = boss_move_pattern("Tobias the Wizard", boss_health, player_health)          
            if boss_action == "hit":
                damage = max(2, boss_attack + random.randint(0, dice_roll()))
                slowprint(f"\nTobias attacks for {damage} damage!")
                player_health -= damage

            elif boss_action == "heal":
                heal_amount = random.randint(20, 50)
                boss_health = min(boss_health + heal_amount, bosses["Tobias the Wizard"]["health"])

                if boss_health > 350 and final_form == False:
                    boss_health = 350

                elif boss_health > 500 and final_form == True:
                    boss_health = 500

                slowprint(color_text(f"\nTobias heals for {heal_amount} HP!", "green"))

            elif boss_action == "dodge":
                slowprint(color_text(f"\nTobias dodges!", "cyan"))
                boss_health += damage

    if player_health <= 0:
        slowprint(color_text("You fall as Tobias laughs... you watch hopelessly as your soul is consumed.", "red"))
        slowprint(color_text("BAD ENDING UNLOCKED", "bold"), 0.1)
        player["alive"] = False
        sep()
        slowprint(color_text("This isn't how the story goes and you know it. Stick to the script.", "red"), 0.04)
        sep()

        choice = input("Retry the boss fight? (yes/no): ").strip().lower()
        if choice == "yes":
            player["alive"] = True
            player["health"] = 150
            fake_glitch_sequence()

            #Call battle again in the same function scope
            return run_tobias_battle(final_form=final_form)
                
        else:
            slowprint(color_text("Coward.", "red"))
            return "loss"

    else:
        slowprint(color_text("\nWith a final cry, Tobias shatters into static.", "green"))
        slowprint(color_text("\nYou stumble out of the arcade... alive.", "green"))
        return "victory"
#------------------------------------------------------------
        
# ========= Room and Object Logic =========
#Describe Current Room
def describe_room(room):
    global locations
    """Describe the room the player is currently in"""
    data = locations[room]
    slowprint(f"\nYou are in the {room}.", 0.02)
    slowprint(data["description"], 0.02)
    pause()
    if "objects" in data:
        slowprint("\nYou notice...\n", 0.04)
        for obj in data["objects"]:
            slowprint(f"- {obj}", 0.02)

#Examine Place in Room
def examine_object(room, obj_name):
    global locations
    """Examine a given POI in a room"""
    room_data = locations[room]
    if "objects" not in room_data or obj_name not in room_data["objects"]:
        slowprint("\nThere's no places like that here.", 0.02)
        return
    
    obj = room_data["objects"][obj_name]
    slowprint(color_text(f"\n{obj_name.upper()}:", "bold"))
    slowprint(obj["description"])
#------------------------------------------

# ========= Puzzle Dispatcher =========
def run_puzzle(puzzle_name):
    """Run the puzzle if the dict keys return a match"""
    puzzles = {
        "generator": puzzle_generator,
        "syntax": puzzle_syntax,
        "signal_interrupt": puzzle_interrupt,
        "file_restore": puzzle_file_restore,
        "eof_input": puzzle_eof,
        "bootloader": puzzle_bootloader
    }

    if puzzle_name in puzzles:
        puzzles[puzzle_name]()
    else:
        slowprint("Im over thinking this..", 0.02)

#Individual Puzzle Definitions
def puzzle_generator():
    sep()
    slowprint_glitch(">>> POWER GENERATOR TERMINAL <<<", "cyan", 0.02, 0.08)
    pause()
    slowprint("SYSTEM STATUS: OFFLINE", 0.03)
    slowprint("You see 3 voltage dials. The volts needed exactly have been scratched out..but you can make out a 1 and a 0")
    pause()

    voltages = []
    for i in range(3):
        v = input(f"Set voltage dial {i+1} (or type 'exit' to leave): ").strip()
        if v.lower() == "exit":
            slowprint("You step away from the generator for now.", 0.02)
            return
        try:
            voltages.append(int(v))
        except ValueError:
            slowprint("That's not a valid number. Try again.", 0.02)
            return puzzle_generator()

    if sum(voltages) == 100:
        flicker_text(color_text("POWER RESTORED", "green"), 6, 0.15)
        slowprint("Lights hum back to life across the arcade...")
        unlock_room("arcade_room_floor")
        #Ensure requires_power flags set off
        if "control room" in locations:
            locations["control room"]["requires_power"] = False
        if "arcade room floor" in locations:
            locations["arcade room floor"]["requires_power"] = False
        global power_on
        power_on = True
        locations["backroom"]["objects"]["generator"]["puzzle_solved"] = True
    
    else:
        slowprint(color_text("VOLTAGE INSTABILITY DETECTED: SYSTEM SHUTTING DOWN...", "red"))
        fake_glitch_sequence()

def puzzle_syntax():
    sep()
    slowprint("You find an old CRT monitor showing broken Python code:")
    print(color_text('for i in range(5)\n    print("Open Arena")', "yellow"))
    slowprint(color_text("Type 'exit' to leave the puzzle.", "italic"))
    pause()
    guess = input("Fix the code (or type exit to exit): ").strip()
    if guess.lower() == "exit":
        slowprint("You back away from the monitor.", 0.02)
        return

    if guess == 'for i in range(5): print("Open Arena")' or guess == 'for i in range(5):\n    print("Open Arena")':
        slowprint(color_text("\nCODE COMPILED SUCCESSFULLY.", "green"))
        unlock_room("big b arena")  
        # Mark puzzle solved
        if "control room" in locations and "objects" in locations["control room"]:
            if "monitor" in locations["control room"]["objects"]:
                locations["control room"]["objects"]["monitor"]["puzzle_solved"] = True
    else:
        slowprint(color_text("SYNTAX ERROR: TRY AGAIN LATER...", "red"))

def puzzle_interrupt():
    global loop_broken
    sep()
    slowprint("The terminal hums while a strange program runs endlessly...")
    print(color_text("while True:\n    print('RUNNING...')", "yellow"))
    pause()
    choice = input("Type 'start' to begin or 'exit' to leave: ").strip().lower()
    if choice == "exit":
        slowprint("You leave the terminal alone.", 0.02)
        return

    try:
        counter = 0
        while not loop_broken:
            slowprint_glitch("STEALING SOULS...", "red", 0.05, 0.1)
            #Allow player to break by hitting enter and typing 'interrupt'
            try:
                #Ask for input with short timeout isn't portable; so prompt occasionally
                if counter % 6 == 0:
                    resp = input("(Press Enter to wait): ").strip().lower()
                    if resp == "interrupt":
                        raise KeyboardInterrupt
                time.sleep(0.3)
            except KeyboardInterrupt:
                raise
            counter += 1
            # auto-fallback after some cycles to avoid infinite loop in constrained environments
            if counter >= 30:
                slowprint(color_text("\nSYSTEM AUTO-SHUTDOWN. MAZE ACCESS GRANTED.", "green"))
                loop_broken = True
                break
    except KeyboardInterrupt:
        loop_broken = True
    #When exiting loop set unlocks
    if loop_broken:
        if "arcade room floor" in locations and "objects" in locations["arcade room floor"]:
            if "maze entrance" in locations["arcade room floor"]["objects"]:
                locations["arcade room floor"]["objects"]["maze entrance"]["puzzle_solved"] = True
                if locations["arcade room floor"]["objects"]["maze entrance"]["puzzle_solved"] == True:
                    slowprint(color_text("\nPROGRAM INTERRUPTED. MAZE ACCESS GRANTED.", "green"))
                    unlock_room("maze")       

def puzzle_file_restore():
    sep()
    slowprint("You find a broken log file named system_log.txt")
    try:
        with open("system_log.txt", "w") as f:
            f.write("ERROR###POWER###NOT###RESTORED###DATA###CORRUPTED\n")
    except OSError:
        slowprint(color_text("File write failed — running in restricted mode.", "red"), 0.02)

    slowprint("A message reads: 'Restore log integrity to continue.'")
    guess = input("Enter the restored text line (or type exit to exit): ").strip()
    if guess.lower() == "exit":
        slowprint("You leave the terminal alone.", 0.02)
        return
    if guess.lower() == "power restored successfully":
        try:
            with open("system_log.txt", "w") as f:
                f.write("POWER RESTORED SUCCESSFULLY\n")
        except OSError:
            pass
        slowprint(color_text("\nLOG REPAIRED. ACCESS UNLOCKED.", "green"))
        slowprint("\nYou see the terminal print out a token...")
        player["inventory"].append("arena token")
        slowprint(color_text("\nYou obtained: arena token", "green"))
        if "control room" in locations and "objects" in locations["control room"]:
            if "terminal" in locations["control room"]["objects"]:
                locations["control room"]["objects"]["terminal"]["puzzle_solved"] = True

    else:
        slowprint(color_text("RESTORATION FAILED...", "red"))

def puzzle_eof():
    sep()
    slowprint("You see a message: 'Awaiting user input to terminate connection...'")
    slowprint(color_text("Hint: Sometimes silence says more than words...", "italic"))
    slowprint(color_text("Type 'exit' or 'EOF' to leave the puzzle.", "italic"))
    try:
        while True:
            line = input(">> ")
            if line.lower() == "exit":
                slowprint("You leave the terminal alone.", 0.02)
                return
            if line.lower() == "eof":
                slowprint(color_text("\nCONNECTION TERMINATED.", "green"))
                if "arcade room floor" in locations and "objects" in locations["arcade room floor"]:
                    if "dispenser" in locations["arcade room floor"]["objects"]:
                        locations["arcade room floor"]["objects"]["dispenser"]["puzzle_solved"] = True
                return
    except EOFError:
        slowprint(color_text("\nCONNECTION TERMINATED.", "green"))
        if "arcade room floor" in locations and "objects" in locations["arcade room floor"]:
            if "dispenser" in locations["arcade room floor"]["objects"]:
                locations["arcade room floor"]["objects"]["dispenser"]["puzzle_solved"] = True
    except KeyboardInterrupt:
        slowprint(color_text("\nWRONG INPUT TYPE.", "RED"))

def puzzle_bootloader():
    sep()
    slowprint_glitch(">>> BOOT SECTOR CORRUPTED <<<", "red", 0.03, 0.1)
    pause()
    slowprint("Repair sequence initiated...")
    time.sleep(1)
    slowprint("TYPE 'REPAIR' WHEN PROMPTED TO STABILIZE SECTORS.")
    for i in range(5):
        sys.stdout.write(glitch_text(f"Sector {i+1}: STABILIZING...\n", 0.2))
        time.sleep(random.uniform(0.5, 1.2))
        inp = input("TYPE NOW: ").strip().upper()
        if inp != "REPAIR":
            slowprint(color_text("SECTOR DESTABALIZED, BOOT REQUIRES RESTART...", "red"))
            return
    slowprint(color_text("ALL SECTORS STABILIZED. SYSTEM BOOTED SUCCESSFULLY.", "green"))
    if "cafeteria" in locations and "objects" in locations["cafeteria"]:
        if "dispenser" in locations["cafeteria"]["objects"]:
            locations["cafeteria"]["objects"]["dispenser"]["puzzle_solved"] = True
#--------------------------------------

# ========= Error Recovery =========
def recover_from_error(e, tb = None):
    """Recover from an unexpected error and log detailed traceback info."""
    slowprint(color_text(f"\nAn unexpected error occurred: {e}", "red"), 0.02)
    
    # Get traceback if not passed explicitly
    if tb is None:
        tb = sys.exc_info()[2]

    # Extract line and file info if traceback exists
    if tb:
        filename = tb.tb_frame.f_code.co_filename
        line_no = tb.tb_lineno
        slowprint(color_text(f"(Error occurred in {filename}, line {line_no})", "yellow"))
    else:
        filename, line_no = "unknown", "?"

    # Format full traceback
    tb_info = "".join(traceback.format_exception(type(e), e, tb))

    # Write to error log
    try:
        with open("error_log.txt", "a") as f:
            f.write(f"\n{time.ctime()} - {e}\n")
            f.write(f"File: {filename}, Line: {line_no}\n")
            f.write(tb_info + "\n")
    except OSError:
        pass

    # Add immersive feedback
    fake_glitch_sequence()
    choice = input("Would you like to restart the game? (yes/no): ").strip().lower()

    if choice == "yes":
        global opening_sequence_completed, scene1_completed, gameplay_started, scene2_completed, player
        preserved_name = player.get("name")

        # Reset player state
        player = {
            "name": preserved_name,
            "location": "lobby",
            "inventory": [],
            "bosses_defeated": 0,
            "bosses_spared": 0,
            "alive": True,
            "joined_tobias": False,
            "visited_rooms": set(),
            "health": 150,
            "attack": 65
        }

        # Reset scene and progress flags
        opening_sequence_completed = False
        scene1_completed = False
        gameplay_started = False
        scene2_completed = False

        # Reset boss states
        for b in bosses:
            bosses[b]["alive"] = True
            if b == "Road-Boxer":
                bosses[b]["health"] = 300
            elif b == "Angry-Monkey":
                bosses[b]["health"] = 400
            elif b == "Pack-Dude":
                bosses[b]["health"] = 350
            elif b == "Tobias the Wizard":
                bosses[b]["health"] = 500

        # Restart main gameplay
        gameplay()
        scene2()

    else:
        slowprint(color_text("You step away from the case... for now.", "italic"))
#---------------------------------------

# ========= Game Dialogue Scenes ==========
def opening():
    global player_name, opening_sequence_completed
    sep()
    slowprint("Oct. 31, 2004", 0.05)
    pause()
    slowprint("19:46:35", 0.05)
    pause()
    slowprint("SNIS Evidence Room", 0.05)
    sep()
    pause()

    #First dialogue
    slowprint(color_text("Is this recorder on?", "blue"), 0.02)
    slowprint(color_text("Yeah it's recordin'", "magenta"), 0.02)
    pause()
    slowprint(color_text("Alright, tell them what we're doing..", "magenta"), 0.02)
    slowprint(color_text("K..Well I'm Agent Dunn and this is Agent Mureaux of the SNIS", "blue"), 0.02)
    slowprint(color_text("Super-Natural Investigation Service, be specific Dunn", "magenta"), 0.02)
    slowprint(color_text("Yeah yeah..", "blue"))
    slowprint(color_text("We're the agents assigned to the Big B Arcade Case", "blue"), 0.02)
    slowprint(color_text("Lets see, what is the individual's name Mureaux?","blue"),0.02)
    slowprint(color_text("Case-file is right here, it says...", "magenta"), 0.02)
    pause()
    sep()
    player_name = input("What is your name?: ").strip()
    player["name"] = player_name
    sep()
    pause()
    slowprint(color_text(f"{player_name}...", "magenta"), 0.02)
    pause()
    slowprint(color_text("Interesting name, so where do we start?", "blue"), 0.02)
    pause()
    slowprint(color_text("10 years ago...","magenta"),0.02)
    pause(1)
    sep()
    opening_sequence_completed = True

def scene1():
    global scene1_completed, player_name
    slowprint("Oct. 31, 1994", 0.05)
    slowprint("20:52:23", 0.05)
    slowprint("Big B's Arcade, Detroit, Mi", 0.05)
    sep()
    slowprint(color_text("in front of an arcade", "italic"), 0.05)
    sep()

    slowprint(color_text("So this is the place, Big B's Arcade?","red"),0.02)
    slowprint(color_text("This places makes me feel like we're going to be kidnapped..","green"),0.02)
    slowprint(color_text("Yeah..", "blue"), 0.08)
    pause()
    slowprint(color_text("Be careful everyone","blue"),0.02)
    pause()
    slowprint(color_text(f"Don't worry {player_name}, how scary can a place like this actually be?","red"),0.02)
    sep()
    slowprint(color_text("they all enter the arcade", "italic"), 0.05)
    pause(1)
    slowprint("21:12:47", 0.05)
    sep()

    slowprint(color_text("Yo Brad, I found a game that still works","yellow"),0.02)
    slowprint(color_text("Try and boot it up Chad","red"),0.02)
    slowprint(color_text("What game is it?","green"),0.02)
    slowprint(color_text("It is called Tobias the Wizard, geez use your eyes Arthur", "yellow"),0.02)
    pause()
    slowprint(color_text("Try starting it up, looks interesting enough", "red"), 0.02)
    pause(1)
    sep()
    for i in range(3):
        print(glitch_text("*SYSTEM REBOOT...*\n", 0.01))
        pause()
        pause()
    slowprint_glitch("TOBIAS THE WIZARD", "cyan", 0.04, 0.05)
    sep()
    slowprint(color_text("Oh cool!! The game actually works", "green"), 0.02)
    slowprint(color_text("The screen is glitched out though, shame", "yellow"), 0.02)
    
    sep()
    slowprint(color_text("the screen prints", "italic"), 0.02)
    sep()
    
    slowprint_glitch("HELLO THERE FRIENDS","cyan",0.02,.2)
    slowprint_glitch("WOULD YOU LIKE TO PLAY A GAME?","cyan",0.02,.2)
    sep()
    slowprint(color_text("Uhhhh, sure?","blue"),0.02)
    sep()
    slowprint(color_text("you press yes and the game starts", "italic"), 0.05)
    sep()
    slowprint(color_text("Woah, this is pretty cool. Reminds me of Super Mario", "blue"), 0.02)
    pause()
    slowprint(color_text("Hey!! I want a turn next!", "red"), 0.02)

    sep()
    slowprint(color_text("an hour passes", "italic"), 0.05)
    slowprint("22:14:55", 0.05)
    sep()

    slowprint_glitch("WOULD YOU LIKE TO PLAY AGAIN?", "cyan", 0.02, .2)
    slowprint(color_text("Well, that was fun, but it's time for us to move on", "yellow"), 0.02)
    slowprint(color_text("Maybe we can find the security room and look over the camera footage", "red"), 0.02)
    slowprint(color_text("For once Brad, a smart idea", "yellow"), 0.02)
    
    sep()
    slowprint(color_text("the arcade machine begins to shake violently", "italic"), 0.05)
    sep()

    slowprint(color_text("What the heck is happening to the machine..??", "green"), 0.02)
    slowprint_glitch("WHO EVER SAID YOU COULD LEAVE? WE'RE PLAYING AGAIN", "cyan", 0.02, 0.2)
    slowprint(color_text("What is wrong with the machine??", "blue"), 0.02)
    slowprint(color_text("QUICK, WE NEED TO GET OUT OF HERE, RUN!!!", "red"), 0.02)
    
    sep()
    slowprint(color_text("the arcade machine and the floor of the lobby rumble and hum with horrifying intent","italic"), 0.04)
    slowprint(color_text("Tobias, pulls himself out of the arcade window and into the real world", "italic"), 0.04)
    sep()
    slowprint_glitch("COME FRIENDS, ITS TIME TO PLAY UNTIL OUR HEARTS STOP", "cyan", 0.02, 0.2)
    sep()
    slowprint(color_text("you run into an abandoned area of the arcade, not knowing where you are or came from. Your friends' screams go silent as you start to look around", "italic"), 0.02)
    slowprint(color_text("you make your way out of the storage closet you're in but realize one thing...", "italic"), 0.02)
    slowprint(color_text("you need to find a way out of here...now", "italic"), 0.02)
    scene1_completed = True

def scene2(result):
    global player_name, scene2_completed

    if result == "victory":
        sep()
        slowprint("Oct. 31, 2004", 0.1)
        pause()
        slowprint("23:00:04", 0.1)
        pause()
        slowprint("SNIS Evidence Room", 0.1)
        sep()
        pause()
        slowprint(color_text("So... that really happened?", "magenta"), 0.04)
        slowprint(color_text("Yeah... every single last word and event in that case file is true.", "blue"), 0.04)
        pause()
        slowprint(color_text("But how is that even possible? An arcade game trapping people inside?", "magenta"), 0.04)
        slowprint(color_text("Beats me Mureaux, but I've seen stranger things in my time with the SNIS.", "blue"), 0.04)
        pause()
        slowprint(color_text(f"Do we know what happened to {player_name}?", "magenta"), 0.04)
        slowprint(color_text("Apparently, they were found wandering near the arcade a week later, mumbling about 'escaping the game'.", "blue"), 0.04)
        slowprint(color_text("But they had no memory of what happened inside.", "blue"), 0.04)
        pause()
        slowprint(color_text("Well, at least they made it out... I guess that's something.", "magenta"), 0.04)
        slowprint(color_text("Yeah... well the entire thing is just a rumor...", "blue"), 0.04)
        pause()
        slowprint(color_text("Come on, I'll treat you to coffee in the break room.", "blue"), 0.04)
        slowprint(color_text("Really? Aren't just the kindest.", "magenta"), 0.04)
        slowprint(color_text("Yeah...sure...whatever you say Mureaux.", "blue"), 0.04)
        sep()
        slowprint(color_text("you turn off the recorder, the room falling silent except for the hum of the overhead lights.", "italic"), 0.04)
        slowprint(color_text("as you walk both  walk out, Agent Dunn leaves their I.D. tag behind...", "italic"), 0.04)
        slowprint(color_text(f"the name on it reads, {player_name.upper()} Dunn", "bold"), 0.1)
        slowprint(color_text("THE END", "bold"), 0.1)
        scene2_completed = True
    
    elif result == "loss":
        sep()
        slowprint("Oct. 31, 2004", 0.1)
        pause()
        slowprint("23:00:04", 0.1)
        pause()
        slowprint("SNIS Evidence Room", 0.1)
        sep()
        pause()
        slowprint(color_text("So... that really happened?", "magenta"), 0.04)
        slowprint(color_text("Yeah... every single last word and event in that case file is true.", "blue"), 0.04)
        pause()
        slowprint(color_text("But how is that even possible? An arcade game trapping people inside?", "magenta"), 0.04)
        slowprint(color_text("Beats me Mureaux, but I've seen stranger things in my time with the SNIS.", "blue"), 0.04)
        pause()
        slowprint(color_text(f"Do we know what happened to {player_name}?", "magenta"), 0.04)
        slowprint(color_text("Apparently, they were found wandering near the arcade a week later, mumbling about 'escaping the game'.", "blue"), 0.04)
        slowprint(color_text("But they had no memory of what happened inside.", "blue"), 0.04)
        pause()
        slowprint(color_text("Well, at least they made it out... I guess that's something.", "magenta"), 0.04)
        slowprint(color_text("Yeah... well the entire thing is just a rumor...", "blue"), 0.04)
        pause()
        slowprint(color_text("Come on, I'll treat you to coffee in the break room.", "blue"), 0.04)
        slowprint(color_text("Really? Aren't just the kindest.", "magenta"), 0.04)
        slowprint_glitch("That's what friends are for Mureaux!", "blue", 0.04, 0.02)
        sep()
        slowprint(color_text("you turn off the recorder, the room falling silent except for the hum of the overhead lights.", "italic"), 0.04)
        slowprint(color_text("as you walk both  walk out, Agen Dunn leaves their I.D. tag behind...", "italic"), 0.04)
        slowprint(color_text(f"the name on it reads, {player_name.upper()} Dunn", "bold"), 0.1)
        slowprint(color_text("THE END", "bold"), 0.1)
        scene2_completed = True
#-----------------------------------------
    
# ========= Main Gameplay Loop =========
def gameplay():
    """Main gameplay loop with different commands depending on user input"""
    global gameplay_started, scene2_completed, tobias_isSummoned, quitter, ticket_is_claimed, keycard_is_claimed

    #Initialize Game State
    gameplay_started = True
    sep()
    slowprint(color_text("You find yourself in the lobby of the arcade. Your only company being the flickering lights and broken machines around you.", "italic"), 0.05)
    pause()
    slowprint(color_text("Look around, examine, and do whatever you can to escape", "italic"), 0.05)
    pause()


    while True:
        sep()
        
        # Check for Game Over
        if not player["alive"]:
            slowprint(color_text("\nYou have given into the arcade...", "red"), 0.1)
            slowprint(color_text("BAD ENDING", "red"), 0.1)
            sep()
            break
        
        #Get Player Command
        command = (get_player_input(color_text("> What would you like to do? (move / examine / inventory / help / look / map /interact): ", "yellow")) or "").strip().lower()

        current_room = player["location"]

        #Look around the room
        if command in ["scan", "look"]:
            describe_room(current_room) 

        #View Map
        elif command == "map":
            slowprint(color_text("\n           ===== MAP =====", "cyan"), 0.04)
            draw_bigb_map(player, locations, bosses, power_on)
            
        #Interact with POI's in the room
        elif command.startswith("interact "):

            # Extract the object name (strip the 'interact ' prefix) and create normalized variants
            obj_name = command.replace("interact ", "", 1).strip()
            norm_us, norm_nospace, norm_space = normalize_obj_name(obj_name)

            objs = locations[current_room].get("objects", {})

            # Attempt to find the object key (accept multiple forms)
            matched_key = None
            for key in objs.keys():
                if key == norm_us or key == norm_nospace or key == norm_space or key == obj_name:
                    matched_key = key
                    break

            # Fallback: allow partial matching (e.g., "ticket" matches "ticket_machine")
            if matched_key is None:
                for key in objs.keys():
                    if obj_name in key or obj_name in key.replace("_", " "):
                        matched_key = key
                        break

            if matched_key is None:
                slowprint("\nThere's nothing like that here.", 0.02)
                continue
                
            obj = objs[matched_key]
         
            #Object interaction logic
            if matched_key == "prize counter" and current_room == "lobby":
                if "key" not in player["inventory"] and "key" in locations["lobby"]["objects"]["prize counter"]["items"]:
                    if "ticket" in player["inventory"]:
                        slowprint("\nYou notice a dusty sign on the counter: 'Redeem tickets for prizes!'", 0.02)
                        choice = input("\nWould you like to redeem your ticket for a prize? (yes/no): ").strip().lower()
                        if choice == "yes":
                            slowprint(color_text("\nYou insert your ticket into the redemption slot... a small compartment pops open with a glinting key inside.", "bold"))
                            player["inventory"].append("key")
                            locations["lobby"]["objects"]["prize counter"]["items"].remove("key")
                            player["inventory"].remove("ticket")
                            slowprint(color_text("\nYou obtained: key", "green"))
                            slowprint(color_text("\nThe ticket is sucked in and vanishes.", "red"))
                        else:
                            slowprint(color_text("\nI think I'll hold onto my ticket for now.", "blue"), 0.02)
                    else:
                        slowprint(color_text("\n Too bad I don't have any tickets...", "blue"), 0.04)
                        slowprint(color_text("Maybe theres some around here?", "blue"), 0.04)
                    continue

                slowprint(color_text("\nI've already redeemed my prize from here, not point in sticking around it.", "blue"), 0.02)
                continue

            if matched_key == "cleaning cart" and current_room == "lobby":
                slowprint("\nYou rummage through the cleaning cart but find nothing useful, but you see an interesting note on the side. You think of [examining] it but move on..", 0.02)
                continue

            if matched_key == "ticket machine" and current_room == "lobby":
                if "ticket" not in player["inventory"] and "ticket" in locations["lobby"]["objects"]["ticket machine"]["items"]:
                    slowprint("\nThe ticket machine is broken beyond repair, but you take a ticket from it, half sticking out", 0.02)
                    player["inventory"].append("ticket")
                    locations["lobby"]["objects"]["ticket machine"]["items"].remove("ticket")
                    slowprint(color_text("\nYou obtained: ticket", "green"))
                    continue
                else:
                    slowprint("\nThe ticket machine has nothing left to give.", 0.02)
                continue

            if matched_key == "cafeteria table" and current_room == "cafeteria":
                if "keycard" not in player["inventory"] and keycard_is_claimed == False:
                    slowprint(color_text("\nLooks like there's a keycard here, don't mind if I do...", "blue"), 0.02)
                    player["inventory"].append("keycard")
                    keycard_is_claimed = True
                    slowprint(color_text("\nYou obtained: keycard", "green"))
                else:
                    slowprint(color_text("\nNothing else here, other than someone elses old food crumbs...", "blue"), 0.02)
                continue

            if matched_key == "dispenser" and current_room == "cafeteria":
                if "purified_water" in player["inventory"] and "purified_water" in locations["cafeteria"]["objects"]["dispenser"]["items"]:
                    slowprint(color_text("\nI already have some water, don't think I need any more.", "blue"), 0.02)
                    continue
                else:
                    if locations["cafeteria"]["objects"]["dispenser"].get("puzzle_solved"):
                        slowprint(color_text("\nThe dispenser is now functional...", "blue"), 0.02)
                        player["inventory"].append("purified_water")
                        slowprint(color_text("\nYou obtained: purified water", "green"))
                        locations["cafeteria"]["objects"]["dispenser"]["items"].remove("purified_water")
                    else:
                        slowprint(color_text("\nThe water dispenser seems to be broken. I wonder if I could fix it...", "blue"), 0.02)
                    continue

            if matched_key == "dispenser" and current_room == "control room":
                if "purified_water" not in player["inventory"] and "purified_water" in locations["control room"]["objects"]["dispenser"]["items"]:
                    slowprint("\nYou manage to get a bottle of purified water from the dispenser.", 0.02)
                    player["inventory"].append("purified_water")
                    slowprint(color_text("\nGreat, now I won't die of dehydration...", "blue"), 0.02)
                    slowprint(color_text("\nYou obtained: purified water", "green"))
                    locations["control room"]["objects"]["dispenser"]["items"].remove("purified_water")                    
                elif "purified_water" in player["inventory"]:
                    slowprint(color_text("\nI already have some water, don't think I need any more.", "blue"), 0.02)
                else:
                    slowprint(color_text("\nThe dispenser has nothing left to give me...shame.", "blue"), 0.02)
                continue

            if matched_key == "dispenser" and current_room == "arcade room floor":
                disp = locations["arcade room floor"]["objects"]["dispenser"]

                # Puzzle not solved yet → run it
                if not disp.get("puzzle_solved", False):
                    slowprint("\nThe dispenser screen flickers. Maybe there's a way to fix it...", 0.02)
                    run_puzzle(disp["puzzle"])

                    # If puzzle failed, stop here
                    if not disp.get("puzzle_solved", False):
                        slowprint("\nThe dispenser still seems broken.", 0.02)
                        continue

                    slowprint("\nYou hear a soft chime. The dispenser whirs back to life.", 0.02)

                # Puzzle solved → dispenser works
                if "purified_water" in disp["items"] and "purified_water" not in player["inventory"]:
                    slowprint(color_text("\nGreat, now I won't die of dehydration.", "blue"), 0.02)
                    player["inventory"].append("purified_water")
                    disp["items"].remove("purified_water")
                    slowprint(color_text("\nYou obtained: purified water", "green"))
                else:
                    slowprint("\nNothing left to dispense.", 0.02)

                continue
            
            if matched_key == "observation deck" and current_room == "big b arena":
                slowprint(color_text("\nYou try to mind your step as you walk through the shattered window into the guards obervation deck", "italic"))
                slowprint(color_text("\nYou look out over the whole arena and realize in a depressing sort of way, it looks surprisingly beautiful..."))

                roll = dice_roll()
                if roll < 5:
                    slowprint(color_text("\nYou cut yourself on the window as you try to make your way inside, injuring your legs and right arm"))
                    player["health"] -= 50
                    
                if "level 2 keycard" in locations["big b arena"]["objects"]["observation deck"]["items"]:
                    slowprint(color_text("\nYou pick up another keycard, this one with a 2 labeled on it...", "italic"))
                    slowprint(color_text("\nNice, I can start a collection with these", "blue"))
                    player["inventory"].append("level 2 keycard")
                    slowprint(color_text("\nYou obtained: level 2 keycard", "green"))
                    locations["big b arena"]["objects"]["observation deck"]["items"].remove("level 2 keycard")
                else:
                    slowprint(color_text("I already picked up the keycard from here, no sense in searching through all the rubble to find something else", "blue"))
            
            if matched_key == "guard locker" and current_room == "guard room":
                locker = locations["guard room"]["objects"]["guard locker"]

                # FIRST interaction
                if locker["hit_counter"] == 0:
                    slowprint("\nYou see a rusted metal locker and decide to open it but it won't budge...")
                    slowprint(color_text("\nDANG IT, SO FAR AND THIS IS ALL I GET?? A BROKEN LOCKER??", "blue"))
                    sep()
                    slowprint(color_text("you slam your whole body against the locker, denting it further", "italic"))
                    slowprint(color_text("you notice the door is now slightly more open than it was before...", "italic"))
                    locker["hit_counter"] += 1
                    continue

                # SECOND interaction
                elif locker["hit_counter"] == 1:
                    slowprint("\nYou shoulder-check the locker again. It creaks loudly.")
                    locker["hit_counter"] += 1
                    continue

                # THIRD interaction — opens!
                elif locker["hit_counter"] == 2:
                    slowprint(color_text("\nWith one final slam, the locker bursts open!", "green"))
                    locker["hit_counter"] += 1
                    locker["opened"] = True

                    # Give items if any
                    if "items" in locker and locker["items"]:
                        for item in locker["items"]:
                            player["inventory"].append(item)
                            slowprint(color_text(f"\nYou obtained: {item}", "green"))
                        locker["items"].remove("throne key")  #Empty so player can't farm items
                    continue

                # AFTER it’s already opened
                else:
                    slowprint("\nThe locker is already busted open. Nothing else inside.")
                    continue
            
            # If object is interactable and has an attached puzzle, run the puzzle
            if obj.get("interactable"):
                if obj.get("puzzle") and not obj.get("puzzle_solved", False):
                    run_puzzle(obj["puzzle"])
                else:
                    # Allow interactable objects without puzzles to have custom behavior
                    slowprint("\nYou fiddle with it, but else nothing happens.", 0.02)
                continue
            
            #The object exists but isn't interactable
            slowprint("You can't interact with that right now.", 0.02)
                   
        #Examine POI's in the room
        elif command.startswith("examine "):
            obj_name = command.replace("examine ", "")
            norm_us, norm_nospace, norm_space = normalize_obj_name(obj_name)
            for key in locations[current_room].get("objects", {}):
                if key in [norm_us, norm_nospace, norm_space]:
                    obj_name = key
                    break
            examine_object(current_room, obj_name)
                   
        #Move to another room
        elif command.startswith("move "):
            # Extract the object name (strip the 'interact ' prefix) and create normalized variants
            target = command.replace("move ", "", 1).strip()
            norm_us, norm_nospace, norm_space = normalize_obj_name(target)
            current_room = move_to_room(current_room, target, player["inventory"])
            check_for_boss(current_room)
                  
        #Check Inventory
        elif command == "inventory":
            slowprint("I have...: " + ", ".join(player["inventory"]) if player["inventory"] else "\nYour inventory is empty.", 0.02)
            
        #Get a list of commands
        elif command == "help":
            slowprint("\nI can... [move] to a <location>, [examine] an <object>, look at my [inventory], and [look] around my surroundings or at my [map], or [interact] with an <object>", 0.02)
            slowprint("\n(You can also [save] your game file, [load] your game file, list the [saves] and [delete] your game file)")    
        
        #Give up and quit
        elif command == "quit":
            slowprint("\nYou decide to give up and give into the darkness around you..", 0.02)
            slowprint(color_text("BAD ENDING","red"), 0.1)
            sep()
            slowprint_glitch("WHO EVER SAID YOU COULD LEAVE? WE'RE WHEN I SAY WE'RE DONE", "cyan", 0.04, 0.03)
            if quitter > 0 and quitter < 8:
                quitter += 1
            if quitter == 8:
                slowprint_glitch("YOU'RE LAME, BOOOOOORINGGGGGG", "cyan", 0.04, 0.03)
                quitter = True
                quittetr += 0
            continue
        
        #Save the current state of the game
        elif command.startswith("save "):
            try:
                filename = command.split(" ", 1)[1].strip()
                save_game(filename)
            except:
                slowprint("\nUsage: save <filename.json>", 0.02)

        #Load any given save, as long as you have the save key for it
        elif command.startswith("load "):
            try:
                filename = command.split(" ", 1)[1].strip()
                load_game(filename)
            except:
                slowprint("\nUsage: load <filename.json>", 0.02)

        #List all available saves
        elif command == "saves":
            list_all_saves()
        
        #Delete any save as long as you have the key for it
        elif command.startswith("delete "):
            try:
                filename = command.split(" ", 1)[1].strip()
                delete_save(filename)
            except:
                slowprint("Usage: delete <filename.json>", 0.02)

        #Unknown Command
        else:
            slowprint("\nI'm not sure thats something I can do..", 0.02)
            
        #Check for Tobias Boss Fight
        if player["location"] == "throne room" and not tobias_isSummoned:
            tobias_isSummoned = True
            return run_final_tobias_encounter()
#--------------------------------------
           
# ========= Run Game =========
def main():
    """Main function for all the gameplay functions"""
    global opening_sequence_completed, scene1_completed, gameplay_started, scene2_completed
    try:
        opening()
        scene1()
        result = gameplay()
        scene2(result)

    except(KeyboardInterrupt, EOFError) as e:
        recover_from_error(e, sys.exc_info()[2])
        
    except Exception as e:
        recover_from_error(e, sys.exc_info()[2])
if __name__ == "__main__":
    main()
#-----------------------------