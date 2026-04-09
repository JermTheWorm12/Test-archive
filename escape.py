from flask import Flask, request, session, redirect, url_for, render_template_string
import random
import json
import os

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"

ROOM_EXITS = {
    "Bedroom": ["Hallway"],
    "Hallway": ["Bedroom", "Master Bedroom", "Hall Bathroom", "Guest Bedroom", "Foyer"],
    "Foyer": ["Hallway", "Kitchen", "Living Room"],
    "Master Bedroom": ["Hallway", "Master Bathroom"],
    "Master Bathroom": ["Master Bedroom"],
    "Hall Bathroom": ["Hallway"],
    "Guest Bedroom": ["Hallway"],
    "Kitchen": ["Foyer", "Dining Room"],
    "Living Room": ["Foyer", "Dining Room"],
    "Dining Room": ["Living Room", "Kitchen", "Library", "Backyard"],
    "Library": ["Dining Room", "Den", "Laundry Room"],
    "Backyard": ["Dining Room"],
    "Laundry Room": ["Library"],
    "Den": ["Library"]
}

ROOM_OBJECTS = {
    "Bedroom": ["Bedroom Drawer"],
    "Hallway": ["Hall Closet"],
    "Foyer": ["Front Door"],
    "Master Bedroom": ["MB Closet", "MB Nightstand", "Desk"],
    "Master Bathroom": ["Master Cabinet"],
    "Hall Bathroom": ["Hall Cabinet"],
    "Guest Bedroom": ["GB Nightstand", "GB Closet"],
    "Kitchen": ["Cabinet1", "Cabinet2", "Kitchen Drawer"],
    "Living Room": ["Mantle", "Coffee Table"],
    "Dining Room": ["Table"],
    "Library": ["Bookshelf"],
    "Backyard": ["Garage"],
    "Laundry Room": ["Laundry Shelf"],
    "Den": ["Safe"]
}

SEARCH_RESULTS = {
    "Bedroom Drawer": "You search the bedroom drawer.",
    "Bookshelf": "You search the bookshelf.",
    "Mantle": "You inspect the mantle.",
    "Laundry Shelf": "You search the laundry room shelf.",
    "MB Nightstand": "You search the master bedroom nightstand.",
    "GB Nightstand": "You search the guest bedroom nightstand.",
    "Desk": "The desk drawer is jammed shut.",
    "Hall Closet": "Nothing useful here.",
    "Master Cabinet": "You search the master bathroom cabinet.",
    "Hall Cabinet": "You search the hall bathroom cabinet.",
    "Cabinet1": "Cabinet1 is screwed shut.",
    "Cabinet2": "You search Cabinet2.",
    "Coffee Table": "You search the coffee table.",
    "Table": "You search the table.",
    "MB Closet": "You search the master bedroom closet.",
    "GB Closet": "You search the guest bedroom closet.",
    "Garage": "You find a crowbar.",
    "Kitchen Drawer": "You search the kitchen drawer."
}

SAVE_FILE = "savegame_web.json"


PAGE = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Escape House</title>
    <style>
        body {
            margin: 0;
            background: #0c0c0c;
            color: #e8e8e8;
            font-family: Consolas, "Courier New", monospace;
        }
        .terminal {
            max-width: 980px;
            margin: 28px auto;
            padding: 22px 26px;
            min-height: calc(100vh - 56px);
            box-sizing: border-box;
            background: #111111;
            border: 1px solid #2a2a2a;
            box-shadow: inset 0 0 0 1px #161616;
        }
        .titlebar {
            color: #b8b8b8;
            margin-bottom: 18px;
            font-size: 15px;
        }
        .block {
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 20px;
            margin-bottom: 22px;
        }
        .command-row {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 20px;
        }
        .prompt {
            color: #f0f0f0;
        }
        input[type="text"] {
            flex: 1;
            background: transparent;
            color: #f0f0f0;
            border: none;
            outline: none;
            font-family: Consolas, "Courier New", monospace;
            font-size: 20px;
            padding: 0;
        }
        .button-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
        }
        button, input[type="submit"] {
            background: #1b1b1b;
            color: #f0f0f0;
            border: 1px solid #3a3a3a;
            padding: 8px 14px;
            font-family: Consolas, "Courier New", monospace;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover, input[type="submit"]:hover {
            background: #252525;
        }
        .hint {
            color: #a9a9a9;
            font-size: 14px;
            margin-top: 16px;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="terminal">
        <div class="titlebar">Escape House - Web Terminal</div>

        <div class="block">{{ display_text }}</div>

        {% if won %}
            <div class="button-row">
                <form method="post" action="/action">
                    <input type="hidden" name="action" value="reset">
                    <input type="submit" value="Reset Game">
                </form>
                <form method="post" action="/action">
                    <input type="hidden" name="action" value="new">
                    <input type="submit" value="New Game">
                </form>
            </div>
        {% else %}
            <form method="post" action="/action" class="command-row" autocomplete="off">
                <span class="prompt">What do you do?</span>
                <input type="hidden" name="action" value="command">
                <input type="text" name="target" autofocus spellcheck="false">
            </form>

            <div class="button-row">
                <form method="post" action="/action">
                    <input type="hidden" name="action" value="inventory">
                    <button type="submit">Inventory</button>
                </form>
                <form method="post" action="/action">
                    <input type="hidden" name="action" value="save">
                    <button type="submit">Save</button>
                </form>
                <form method="post" action="/action">
                    <input type="hidden" name="action" value="load">
                    <button type="submit">Load</button>
                </form>
                <form method="post" action="/action">
                    <input type="hidden" name="action" value="new">
                    <button type="submit">New Game</button>
                </form>
                <form method="post" action="/action">
                    <input type="hidden" name="action" value="quit">
                    <button type="submit">Quit</button>
                </form>
            </div>
        {% endif %}

        <div class="hint">Commands:
go hallway
search bedroom drawer
open safe 123
inventory
save
load
new
quit</div>
    </div>
</body>
</html>
"""


def new_game_state():
    safe_code = random.choice(["381", "527", "194"])

    eligible_digit_objects = [
        "Bedroom Drawer",
        "Desk",
        "Bookshelf",
        "Mantle",
        "Master Cabinet",
        "Hall Cabinet",
        "Cabinet1",
        "Cabinet2",
        "Coffee Table",
        "Table",
        "MB Closet",
        "GB Closet",
        "Laundry Shelf",
        "MB Nightstand",
        "GB Nightstand",
        "Kitchen Drawer"
    ]

    digit_objects = random.sample(eligible_digit_objects, 3)
    screwdriver_location = random.choice(["MB Nightstand", "GB Nightstand", "Laundry Shelf"])

    return {
        "current_room": "Bedroom",
        "inventory": [],
        "safe_unlocked": False,
        "safe_code": safe_code,
        "digit_locations": {
            "1st digit": digit_objects[0],
            "2nd digit": digit_objects[1],
            "3rd digit": digit_objects[2]
        },
        "screwdriver_location": screwdriver_location,
        "message": "You wake up in the Bedroom. Find clues, open the safe in the Den, and escape through the Front Door.",
        "won": False
    }



def get_state():
    if "game" not in session:
        session["game"] = new_game_state()
    return session["game"]



def save_state(state):
    session["game"] = state
    session.modified = True



def object_digits(state):
    code = state["safe_code"]
    return {
        state["digit_locations"]["1st digit"]: ("1st digit", code[0]),
        state["digit_locations"]["2nd digit"]: ("2nd digit", code[1]),
        state["digit_locations"]["3rd digit"]: ("3rd digit", code[2])
    }



def reveal_digit_if_present(state, obj):
    digits = object_digits(state)

    if obj in digits:
        digit_label, digit_value = digits[obj]
        note = f"{digit_label}: {digit_value}"
        if note not in state["inventory"]:
            state["inventory"].append(note)
        return f"You find a note labeled '{digit_label}' with the number {digit_value}."

    return "Nothing useful here."



def normalize_spaces(text):
    return " ".join(text.strip().split())



def find_case_insensitive_match(user_text, options):
    cleaned = normalize_spaces(user_text).lower()
    option_map = {option.lower(): option for option in options}
    return option_map.get(cleaned)



def build_display_text(state):
    lines = [state["message"], "", f"You are in the {state['current_room']}.", "", "You can go to:"]
    for room in ROOM_EXITS[state["current_room"]]:
        lines.append(f"- {room}")

    lines.append("")
    lines.append("You can search:")
    for obj in ROOM_OBJECTS[state["current_room"]]:
        lines.append(f"- {obj}")

    lines.append("")
    if state["inventory"]:
        lines.append("Inventory: " + ", ".join(state["inventory"]))
    else:
        lines.append("Inventory: empty")

    if state.get("won"):
        lines.append("")
        lines.append("You escaped the house.")

    return "\n".join(lines)



def handle_go(state, target):
    exits = ROOM_EXITS[state["current_room"]]
    destination = find_case_insensitive_match(target, exits)
    if destination:
        state["current_room"] = destination
        state["message"] = f"You move to the {destination}."
    else:
        state["message"] = "You can't go there."



def handle_search(state, target):
    current_room = state["current_room"]
    available_objects = ROOM_OBJECTS[current_room]
    obj = find_case_insensitive_match(target, available_objects)

    if not obj:
        state["message"] = "You don't see that here."
        return

    if obj == "Safe":
        if state["safe_unlocked"]:
            state["message"] = "The safe is already open."
        else:
            state["message"] = "The safe is locked. Use: open safe 123"
        return

    if obj == "Front Door":
        if "key" in state["inventory"]:
            state["message"] = "You unlock the front door and escape!"
            state["won"] = True
        else:
            state["message"] = "The front door is locked."
        return

    if obj == "Garage":
        if "crowbar" not in state["inventory"]:
            state["inventory"].append("crowbar")
            state["message"] = "You search the garage and find a crowbar."
        else:
            state["message"] = "You already took the crowbar."
        return

    if obj == "Desk":
        if "crowbar" in state["inventory"]:
            state["message"] = "You pry open the stuck desk drawer with the crowbar.\n" + reveal_digit_if_present(state, "Desk")
        else:
            state["message"] = "The desk drawer is stuck. You need something to pry it open."
        return

    if obj == "Cabinet1":
        if "screwdriver" in state["inventory"]:
            state["message"] = "You unscrew Cabinet1 and open it.\n" + reveal_digit_if_present(state, "Cabinet1")
        else:
            state["message"] = "Cabinet1 is screwed shut. You need a screwdriver."
        return

    if obj in ["MB Nightstand", "GB Nightstand", "Laundry Shelf"]:
        messages = [SEARCH_RESULTS[obj]]
        if obj == state["screwdriver_location"] and "screwdriver" not in state["inventory"]:
            state["inventory"].append("screwdriver")
            messages.append("You find a screwdriver.")
        messages.append(reveal_digit_if_present(state, obj))
        state["message"] = "\n".join(messages)
        return

    base = SEARCH_RESULTS.get(obj, "Nothing useful here.")
    digit = reveal_digit_if_present(state, obj)
    state["message"] = f"{base}\n{digit}"



def handle_safe_code(state, code_attempt):
    if state["current_room"] != "Den" or "Safe" not in ROOM_OBJECTS[state["current_room"]]:
        state["message"] = "You are not at the safe."
    elif state["safe_unlocked"]:
        state["message"] = "The safe is already open."
    elif code_attempt == state["safe_code"]:
        state["safe_unlocked"] = True
        if "key" not in state["inventory"]:
            state["inventory"].append("key")
        state["message"] = "The safe clicks open. Inside, you find a key."
    else:
        state["message"] = "Wrong code."



def handle_command(state, command_text):
    command = normalize_spaces(command_text)
    lowered = command.lower()

    if not command:
        state["message"] = "Type a command."
        return

    if lowered.startswith("go to "):
        handle_go(state, command[6:])
        return

    if lowered.startswith("go "):
        handle_go(state, command[3:])
        return

    if lowered.startswith("search "):
        handle_search(state, command[7:])
        return

    if lowered.startswith("inspect "):
        handle_search(state, command[8:])
        return

    if lowered.startswith("open safe "):
        handle_safe_code(state, command[10:])
        return

    if lowered == "inventory":
        if state["inventory"]:
            state["message"] = "Inventory: " + ", ".join(state["inventory"])
        else:
            state["message"] = "Inventory: empty"
        return

    if lowered == "save":
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(state, file)
        state["message"] = f"Game saved to {SAVE_FILE}."
        return

    if lowered == "load":
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as file:
                loaded_state = json.load(file)
            state.clear()
            state.update(loaded_state)
            state["message"] = f"Game loaded from {SAVE_FILE}."
        else:
            state["message"] = "No save file found."
        return

    if lowered == "new":
        state.clear()
        state.update(new_game_state())
        return

    if lowered == "quit":
        session.clear()
        state.clear()
        state.update(new_game_state())
        state["message"] = "Game ended. Start again from the Bedroom."
        return

    if lowered == "help":
        state["message"] = (
            "Commands:\n"
            "go hallway\n"
            "search bedroom drawer\n"
            "open safe 123\n"
            "inventory\n"
            "save\n"
            "load\n"
            "new\n"
            "quit"
        )
        return

    state["message"] = "Unknown command. Type help for commands."


@app.route("/")
def index():
    state = get_state()
    return render_template_string(
        PAGE,
        display_text=build_display_text(state),
        won=state.get("won", False)
    )


@app.route("/action", methods=["POST"])
def action():
    state = get_state()
    action_name = request.form.get("action", "")
    target = request.form.get("target", "").strip()

    if action_name == "command":
        handle_command(state, target)

    elif action_name == "inventory":
        if state["inventory"]:
            state["message"] = "Inventory: " + ", ".join(state["inventory"])
        else:
            state["message"] = "Inventory: empty"

    elif action_name == "save":
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump(state, file)
        state["message"] = f"Game saved to {SAVE_FILE}."

    elif action_name == "load":
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as file:
                state = json.load(file)
            state["message"] = f"Game loaded from {SAVE_FILE}."
        else:
            state["message"] = "No save file found."

    elif action_name == "new":
        state = new_game_state()

    elif action_name == "reset":
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        session.clear()
        state = new_game_state()
        state["message"] = "Game reset. Any saved file was deleted, and you are back in the Bedroom."

    elif action_name == "quit":
        session.clear()
        state = new_game_state()
        state["message"] = "Game ended. Start again from the Bedroom."

    save_state(state)
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"

    print("Starting Escape House web server...")
    print(f"Listening on 0.0.0.0:{port}")
    print(f"Open http://127.0.0.1:{port} locally, or use your Render URL when deployed.")

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
