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
    "Hall Closet": "You search the hall closet.",
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
        :root {
            --bg: #000000;
            --panel: #050505;
            --text: #00ff9c;
            --border: #e9e9e9;
            --active-fill: #18ef9d;
            --active-text: #00170d;
            --muted: #8cffc7;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family: Consolas, "Courier New", monospace;
        }

        .shell {
            min-height: 100vh;
            display: grid;
            grid-template-columns: minmax(420px, 1.35fr) minmax(420px, 1fr);
            gap: 24px;
            padding: 20px;
        }

        .terminal, .map-panel {
            background: var(--panel);
            border: 1px solid #0d0d0d;
            min-height: calc(100vh - 40px);
        }

        .terminal {
            padding: 24px 28px;
        }

        .display {
            white-space: pre-wrap;
            line-height: 1.35;
            font-size: 17px;
            margin-bottom: 18px;
        }

        .command-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 8px;
        }

        .prompt {
            color: var(--text);
            white-space: nowrap;
            font-size: 17px;
        }

        input[type="text"] {
            flex: 1;
            min-width: 0;
            background: transparent;
            color: var(--text);
            border: none;
            border-bottom: 1px solid #1a1a1a;
            outline: none;
            font-family: inherit;
            font-size: 17px;
            padding: 4px 0;
        }

        .button-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 18px;
        }

        button, input[type="submit"] {
            background: #0a0a0a;
            color: var(--text);
            border: 1px solid #2a2a2a;
            padding: 8px 12px;
            font-family: inherit;
            font-size: 14px;
            cursor: pointer;
        }

        button:hover, input[type="submit"]:hover {
            background: #101010;
        }

        .hint {
            margin-top: 18px;
            color: var(--muted);
            white-space: pre-wrap;
            font-size: 13px;
            line-height: 1.35;
        }

        .map-panel {
            padding: 18px 18px 14px;
            display: flex;
            flex-direction: column;
        }

        .map-title {
            font-size: 15px;
            color: var(--muted);
            margin-bottom: 10px;
        }

        .map-wrap {
            width: 100%;
            aspect-ratio: 16 / 9.2;
            border: 3px solid var(--border);
            position: relative;
            background: #dcdcdc;
            overflow: hidden;
        }

        .room {
            position: absolute;
            border: 3px solid #000;
            background: #dcdcdc;
            color: #111;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 6px;
            font-size: clamp(11px, 1.1vw, 15px);
            line-height: 1.15;
        }

        .room.active {
            background: var(--active-fill);
            color: var(--active-text);
            font-weight: 700;
            box-shadow: inset 0 0 0 2px rgba(255,255,255,0.35);
        }

        /* House layout */
        .master-bedroom { left: 0%; top: 0%; width: 27.5%; height: 38.5%; }
        .master-bathroom { left: 27.5%; top: 0%; width: 15%; height: 19%; }
        .hall-bathroom { left: 27.5%; top: 19%; width: 15%; height: 19.5%; }
        .kitchen { left: 42.5%; top: 0%; width: 17%; height: 38.5%; }
        .dining-room { left: 59.5%; top: 0%; width: 19.5%; height: 38.5%; }
        .laundry-room { left: 79%; top: 0%; width: 21%; height: 31.5%; }

        .hallway { left: 0%; top: 38.5%; width: 48.5%; height: 20.5%; }
        .foyer { left: 48.5%; top: 38.5%; width: 11%; height: 61.5%; }
        .living-room { left: 59.5%; top: 38.5%; width: 19.5%; height: 61.5%; }
        .library { left: 79%; top: 31.5%; width: 21%; height: 17%; }
        .den { left: 79%; top: 48.5%; width: 21%; height: 51.5%; }

        .bedroom { left: 0%; top: 59%; width: 24.5%; height: 41%; }
        .guest-bedroom { left: 24.5%; top: 59%; width: 24%; height: 41%; }

        /* Backyard layout */
        .yard {
            background: #dcdcdc;
        }

        .yard-garage {
            left: 0%;
            top: 0%;
            width: 32%;
            height: 26%;
        }

        .yard-label {
            position: absolute;
            left: 39%;
            bottom: 1%;
            width: 22%;
            height: 9%;
            border: 3px solid #000;
            background: #dcdcdc;
            color: #111;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: clamp(10px, 1vw, 13px);
            text-align: center;
            padding: 4px;
        }

        .yard-label.active {
            background: var(--active-fill);
            color: var(--active-text);
            font-weight: 700;
        }

        .map-note {
            margin-top: 10px;
            color: var(--muted);
            font-size: 12px;
        }

        @media (max-width: 1100px) {
            .shell {
                grid-template-columns: 1fr;
            }

            .terminal, .map-panel {
                min-height: auto;
            }

            .map-wrap {
                max-width: 820px;
            }
        }
    </style>
</head>
<body>
    <div class="shell">
        <div class="terminal">
            <div class="display">{{ display_text }}</div>

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
go (room)
go to (room)
search (object)
open front door
open safe (code)
inventory
save
load
new
quit</div>
        </div>

        <div class="map-panel">
            <div class="map-title">
                {% if current_room == "Backyard" %}
                    Backyard layout
                {% else %}
                    House layout
                {% endif %}
            </div>

            {% if current_room == "Backyard" %}
                <div class="map-wrap yard">
                    <div class="room yard-garage"></div>
                    <div class="yard-label active"></div>
                </div>
            {% else %}
                <div class="map-wrap">
                    <div class="room master-bedroom {% if current_room == 'Master Bedroom' %}active{% endif %}"></div>
                    <div class="room master-bathroom {% if current_room == 'Master Bathroom' %}active{% endif %}"></div>
                    <div class="room hall-bathroom {% if current_room == 'Hall Bathroom' %}active{% endif %}"></div>
                    <div class="room kitchen {% if current_room == 'Kitchen' %}active{% endif %}"></div>
                    <div class="room dining-room {% if current_room == 'Dining Room' %}active{% endif %}"></div>
                    <div class="room laundry-room {% if current_room == 'Laundry Room' %}active{% endif %}"></div>

                    <div class="room hallway {% if current_room == 'Hallway' %}active{% endif %}"></div>
                    <div class="room foyer {% if current_room == 'Foyer' %}active{% endif %}"></div>
                    <div class="room living-room {% if current_room == 'Living Room' %}active{% endif %}"></div>
                    <div class="room library {% if current_room == 'Library' %}active{% endif %}"></div>
                    <div class="room den {% if current_room == 'Den' %}active{% endif %}"></div>

                    <div class="room bedroom {% if current_room == 'Bedroom' %}active{% endif %}"></div>
                    <div class="room guest-bedroom {% if current_room == 'Guest Bedroom' %}active{% endif %}"></div>
                </div>
            {% endif %}

        </div>
    </div>
</body>
</html>
"""


def new_game_state():
    safe_code = "".join(random.sample("123456789", 3))

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

    crowbar_spawn_options = ["Garage", "Hall Closet", "MB Closet", "GB Closet"]
    screwdriver_spawn_options = ["Garage", "MB Nightstand", "GB Nightstand", "Laundry Shelf"]

    crowbar_location = random.choice(crowbar_spawn_options)
    screwdriver_valid_options = [place for place in screwdriver_spawn_options if place != crowbar_location]
    screwdriver_location = random.choice(screwdriver_valid_options)

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
        "crowbar_location": crowbar_location,
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

    search_objects = []
    open_objects = []

    for obj in ROOM_OBJECTS[state["current_room"]]:
        if obj == "Front Door":
            open_objects.append(obj)
        else:
            search_objects.append(obj)

    if search_objects:
        lines.append("You can search:")
        for obj in search_objects:
            lines.append(f"- {obj}")

    if open_objects:
        lines.append("")
        lines.append("You can open:")
        for obj in open_objects:
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


    if obj == "Garage":
        messages = ["You search the garage."]
        found_anything = False

        if state.get("crowbar_location") == "Garage" and "crowbar" not in state["inventory"]:
            state["inventory"].append("crowbar")
            messages.append("You find a crowbar.")
            found_anything = True

        if state.get("screwdriver_location") == "Garage" and "screwdriver" not in state["inventory"]:
            state["inventory"].append("screwdriver")
            messages.append("You find a screwdriver.")
            found_anything = True

        if not found_anything:
            if "crowbar" in state["inventory"] or "screwdriver" in state["inventory"]:
                messages.append("Nothing else useful here.")
            else:
                messages.append("Nothing useful here.")

        state["message"] = "\n".join(messages)
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

    if obj == "Hall Closet":
        messages = ["You search the hall closet."]
        found_anything = False

        if state.get("crowbar_location") == "Hall Closet" and "crowbar" not in state["inventory"]:
            state["inventory"].append("crowbar")
            messages.append("You find a crowbar.")
            found_anything = True

        if not found_anything:
            if "crowbar" in state["inventory"]:
                messages.append("Nothing else useful here.")
            else:
                messages.append("Nothing useful here.")

        state["message"] = "\n".join(messages)
        return

    if obj == "MB Closet":
        messages = ["You search the master bedroom closet."]
        found_anything = False

        if state.get("crowbar_location") == "MB Closet" and "crowbar" not in state["inventory"]:
            state["inventory"].append("crowbar")
            messages.append("You find a crowbar.")
            found_anything = True

        messages.append(reveal_digit_if_present(state, "MB Closet"))
        state["message"] = "\n".join(messages)
        return

    if obj == "GB Closet":
        messages = ["You search the guest bedroom closet."]
        found_anything = False

        if state.get("crowbar_location") == "GB Closet" and "crowbar" not in state["inventory"]:
            state["inventory"].append("crowbar")
            messages.append("You find a crowbar.")
            found_anything = True

        messages.append(reveal_digit_if_present(state, "GB Closet"))
        state["message"] = "\n".join(messages)
        return

    if obj in ["MB Nightstand", "GB Nightstand", "Laundry Shelf"]:
        messages = [SEARCH_RESULTS[obj]]
        if obj == state.get("screwdriver_location") and "screwdriver" not in state["inventory"]:
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
        state["inventory"] = [
            item for item in state["inventory"]
            if "digit" not in item.lower()
        ]
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

    if lowered == "open front door":
        if state["current_room"] == "Foyer":
            if "key" in state["inventory"]:
                state["message"] = "You unlock the front door and escape!"
                state["won"] = True
            else:
                state["message"] = "The front door is locked."
        else:
            state["message"] = "You are not at the front door."
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
            "go (room)\n"
            "go to (room)\n"
            "search (object)r\n"
            "open front door\n"
            "open safe (code)\n"
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
        current_room=state["current_room"],
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
    print("Starting Escape House web server...")
    port = int(os.environ.get("PORT", 5000))
    print(f"Open http://127.0.0.1:{port} in your browser.")
    app.run(host="0.0.0.0", port=port, debug=True)
