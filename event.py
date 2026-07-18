# ==========================================
# EVENT MANAGEMENT SYSTEM
# Cell 1 - Imports & Configuration
# ==========================================

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict

import ollama

# -------------------------------
# Database & Files
# -------------------------------

DATABASE_NAME = "event_management.db"
CONFIG_FILE = "config.json"
PROMPTS_FILE = "prompts.json"

# -------------------------------
# AI Model
# -------------------------------

OLLAMA_MODEL = "llama3.2"

# -------------------------------
# Event Types
# -------------------------------

EVENT_TYPES = [
    "Birthday",
    "Wedding",
    "Corporate",
    "College",
    "Sports",
    "Festival",
    "Seminar",
    "Workshop",
    "Other"
]

# -------------------------------
# Program Types
# -------------------------------

PROGRAM_TYPES = [
    "Competition",
    "Entertainment",
    "Workshop",
    "Seminar",
    "Performance",
    "Sports",
    "Gaming",
    "Other"
]

# -------------------------------
# Exit Commands
# -------------------------------

EXIT_COMMANDS = ["0", "exit", "back", "quit"]

# -------------------------------
# Header
# -------------------------------

def print_header():
    print("\n" + "*" * 50)
    print("          EVENT MANAGEMENT SYSTEM")
    print("*" * 50 + "\n")

print_header()




######## databases and connection 
# ==========================================
# Cell 2 - Project Initialization
# ==========================================

# Database Connection
conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

# Create config.json (if it doesn't exist)
config = {
    "model": OLLAMA_MODEL,
    "currency": "₹"
}

try:
    with open(CONFIG_FILE, "x") as file:
        json.dump(config, file, indent=4)
except FileExistsError:
    pass

# Create prompts.json (if it doesn't exist)
prompts = {
    "event_plan": "",
    "program_suggestion": "",
    "budget_planner": "",
    "entry_fee": "",
    "schedule": "",
    "chatbot": ""
}

try:
    with open(PROMPTS_FILE, "x") as file:
        json.dump(prompts, file, indent=4)
except FileExistsError:
    pass

# Check Ollama
try:
    ollama.list()
except Exception:
    print("Error: Ollama is not running.")
    print("Start Ollama and run this cell again.")

############# database table
# ==========================================
# Cell 3 - Create Database Tables
# ==========================================

# Event Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS events(
    event_id TEXT PRIMARY KEY,
    event_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    guests INTEGER NOT NULL,
    budget REAL NOT NULL,
    event_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    food_required TEXT NOT NULL
)
""")

# Program Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS programs(
    program_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    program_name TEXT NOT NULL,
    program_type TEXT NOT NULL,
    duration INTEGER,
    entry_fee REAL,
    max_participants INTEGER,
    FOREIGN KEY(event_id) REFERENCES events(event_id)
)
""")

# Budget Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS budgets(
    budget_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    category TEXT NOT NULL,
    estimated_cost REAL,
    actual_cost REAL,
    FOREIGN KEY(event_id) REFERENCES events(event_id)
)
""")

# Schedule Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS schedules(
    schedule_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    program_id TEXT,
    start_time TEXT,
    end_time TEXT,
    FOREIGN KEY(event_id) REFERENCES events(event_id),
    FOREIGN KEY(program_id) REFERENCES programs(program_id)
)
""")

# Guest Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS guests(
    guest_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    guest_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    FOREIGN KEY(event_id) REFERENCES events(event_id)
)
""")

# Expense Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses(
    expense_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    expense_name TEXT NOT NULL,
    amount REAL NOT NULL,
    expense_date TEXT,
    FOREIGN KEY(event_id) REFERENCES events(event_id)
)
""")

# Task Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    task_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    task_name TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY(event_id) REFERENCES events(event_id)
)
""")

# Chat History Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_history(
    chat_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    user_query TEXT,
    ai_response TEXT,
    timestamp TEXT,
    FOREIGN KEY(event_id) REFERENCES events(event_id)
)
""")

conn.commit()


############ ai prompt
# ==========================================
# Cell 4 - AI Engine
# ==========================================

def ask_ai(prompt):

    try:

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content":
                    "You are an intelligent Event Management Assistant. "
                    "Provide clear, practical and well-structured answers."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]

    except Exception as e:
        return f"AI Error : {e}"


########################5

# ==========================================
# Cell 5 - Helper Functions
# ==========================================

def generate_id():
    return str(uuid.uuid4())


def get_input(message):

    while True:

        value = input(message).strip()

        if value.lower() in EXIT_COMMANDS:
            return None

        if value == "":
            print("Input cannot be empty.")
            continue

        return value


def get_integer(message):

    while True:

        value = get_input(message)

        if value is None:
            return None

        try:
            return int(value)

        except ValueError:
            print("Enter a valid number.")


def get_float(message):

    while True:

        value = get_input(message)

        if value is None:
            return None

        try:
            return float(value)

        except ValueError:
            print("Enter a valid amount.")


def get_choice(title, options):

    print(f"\n{title}")

    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")

    while True:

        choice = get_input("\nSelect Option : ")

        if choice is None:
            return None

        try:

            choice = int(choice)

            if 1 <= choice <= len(options):
                return options[choice - 1]

        except ValueError:
            pass

        print("Invalid Choice.")


def yes_no(message):

    while True:

        value = get_input(f"{message} (Yes/No): ")

        if value is None:
            return None

        value = value.lower()

        if value in ["yes", "y"]:
            return "Yes"

        if value in ["no", "n"]:
            return "No"

        print("Enter Yes or No.")

######################################################################################################################################################
# ==========================================
# Cell 6 - Event Functions
# ==========================================

CURRENT_EVENT = None


def create_event():

    print("\n********** CREATE EVENT **********\n")

    event_name = get_input("Event Name : ")
    if event_name is None:
        return

    event_type = get_input("Event Type : ")
    if event_type is None:
        return

    guests = get_integer("Number of Guests : ")
    if guests is None:
        return

    budget = get_float("Budget : ")
    if budget is None:
        return

    event_date = get_input("Event Date (DD-MM-YYYY) : ")
    if event_date is None:
        return

    start_time = get_input("Start Time (HH:MM) : ")
    if start_time is None:
        return

    end_time = get_input("End Time (HH:MM) : ")
    if end_time is None:
        return

    food_required = yes_no("Food Required")
    if food_required is None:
        return

    event_id = generate_id()

    cursor.execute("""
        INSERT INTO events
        VALUES(?,?,?,?,?,?,?,?,?)
    """, (
        event_id,
        event_name,
        event_type,
        guests,
        budget,
        event_date,
        start_time,
        end_time,
        food_required
    ))

    conn.commit()

    print("\nEvent Created Successfully.\n")


def view_events():

    cursor.execute("""
        SELECT
            event_id,
            event_name,
            event_type,
            guests,
            budget,
            event_date,
            start_time,
            end_time,
            food_required
        FROM events
    """)

    events = cursor.fetchall()

    if not events:
        print("\nNo Events Found.\n")
        return

    print("\n********** EVENT LIST **********\n")

    for index, event in enumerate(events, start=1):

        print(f"{index}. {event[1]}")
        print(f"   Type   : {event[2]}")
        print(f"   Guests : {event[3]}")
        print(f"   Budget : ₹{event[4]}")
        print(f"   Date   : {event[5]}")
        print(f"   Time   : {event[6]} - {event[7]}")
        print(f"   Food   : {event[8]}")
        print("-" * 45)


def select_event():

    global CURRENT_EVENT

    cursor.execute("""
        SELECT
            event_id,
            event_name,
            event_type,
            guests,
            budget,
            event_date,
            start_time,
            end_time,
            food_required
        FROM events
    """)

    events = cursor.fetchall()

    if not events:
        print("\nNo Events Available.\n")
        return None

    print("\n********** SELECT EVENT **********\n")

    for index, event in enumerate(events, start=1):
        print(f"{index}. {event[1]} ({event[2]})")

    while True:

        choice = get_integer("\nSelect Event : ")

        if choice is None:
            return None

        if 1 <= choice <= len(events):

            event = events[choice - 1]

            CURRENT_EVENT = {
                "event_id": event[0],
                "event_name": event[1],
                "event_type": event[2],
                "guests": event[3],
                "budget": event[4],
                "event_date": event[5],
                "start_time": event[6],
                "end_time": event[7],
                "food_required": event[8]
            }

            print(f"\nCurrent Event : {CURRENT_EVENT['event_name']}\n")

            return CURRENT_EVENT

        print("Invalid Choice.")


   

        
######################################################################################################################################################
# ==========================================
# Cell 7A - Program Functions
# ==========================================

CURRENT_PROGRAM = None


def create_program():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    print("\n********** CREATE PROGRAM **********\n")

    program_name = get_input("Program Name : ")
    if program_name is None:
        return

    program_type = get_input("Program Type : ")
    if program_type is None:
        return

    duration = get_integer("Duration (Minutes) : ")
    if duration is None:
        return

    max_participants = get_integer("Maximum Participants : ")
    if max_participants is None:
        return

    entry_required = yes_no("Entry Fee Required")
    if entry_required is None:
        return

    entry_fee = 0

    if entry_required == "Yes":

        entry_fee = get_float("Entry Fee : ")

        if entry_fee is None:
            return

    program_id = generate_id()

    cursor.execute("""
        INSERT INTO programs(
            program_id,
            event_id,
            program_name,
            program_type,
            duration,
            entry_fee,
            max_participants
        )
        VALUES(?,?,?,?,?,?,?)
    """, (
        program_id,
        CURRENT_EVENT["event_id"],
        program_name,
        program_type,
        duration,
        entry_fee,
        max_participants
    ))

    conn.commit()

    print("\nProgram Created Successfully.\n")


def view_programs():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            program_id,
            program_name,
            program_type,
            duration,
            entry_fee,
            max_participants
        FROM programs
        WHERE event_id = ?
    """, (CURRENT_EVENT["event_id"],))

    programs = cursor.fetchall()

    if not programs:
        print("\nNo Programs Found.\n")
        return

    print(f"\n********** PROGRAMS : {CURRENT_EVENT['event_name']} **********\n")

    for index, program in enumerate(programs, start=1):

        print(f"{index}. {program[1]}")
        print(f"   Type              : {program[2]}")
        print(f"   Duration          : {program[3]} Minutes")
        print(f"   Entry Fee         : ₹{program[4]}")
        print(f"   Max Participants  : {program[5]}")
        print("-" * 50)


def select_program():

    global CURRENT_PROGRAM

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return None

    cursor.execute("""
        SELECT
            program_id,
            program_name,
            program_type,
            duration,
            entry_fee,
            max_participants
        FROM programs
        WHERE event_id = ?
    """, (CURRENT_EVENT["event_id"],))

    programs = cursor.fetchall()

    if not programs:
        print("\nNo Programs Available.\n")
        return None

    print("\n********** SELECT PROGRAM **********\n")

    for index, program in enumerate(programs, start=1):
        print(f"{index}. {program[1]}")

    while True:

        choice = get_integer("\nSelect Program : ")

        if choice is None:
            return None

        if 1 <= choice <= len(programs):

            program = programs[choice - 1]

            CURRENT_PROGRAM = {
                "program_id": program[0],
                "program_name": program[1],
                "program_type": program[2],
                "duration": program[3],
                "entry_fee": program[4],
                "max_participants": program[5]
            }

            print(f"\nCurrent Program : {CURRENT_PROGRAM['program_name']}\n")

            return CURRENT_PROGRAM

        print("Invalid Choice.")

 





#######################################################################################################################################################
# ==========================================
# Cell 7B - AI Program Functions
# ==========================================

def ai_program_suggestion():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    prompt = f"""
You are an Event Management Expert.

Suggest suitable programs for the following event.

Event Name : {CURRENT_EVENT['event_name']}
Event Type : {CURRENT_EVENT['event_type']}
Guests : {CURRENT_EVENT['guests']}
Budget : ₹{CURRENT_EVENT['budget']}
Food Required : {CURRENT_EVENT['food_required']}

Return:

Program Name
Purpose
Approximate Duration

Provide 8-10 suitable programs.
"""

    print("\nGenerating AI Suggestions...\n")

    response = ask_ai(prompt)

    print(response)


def ai_entry_fee_calculator():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    program = select_program()

    if program is None:
        return

    prompt = f"""
You are an Event Budget Planner.

Event Type : {CURRENT_EVENT['event_type']}
Total Guests : {CURRENT_EVENT['guests']}
Total Budget : ₹{CURRENT_EVENT['budget']}

Program Name : {program['program_name']}
Program Type : {program['program_type']}
Maximum Participants : {program['max_participants']}

Suggest

1. Ideal Entry Fee
2. Expected Registrations
3. Expected Revenue
4. Short Explanation

Keep the answer concise.
"""

    print("\nCalculating Entry Fee...\n")

    response = ask_ai(prompt)

    print(response)
####################################################################################################################################################
# ==========================================
# Cell 7C - AI Budget Planner
# ==========================================

def ai_budget_planner():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            program_name,
            program_type,
            duration,
            entry_fee,
            max_participants
        FROM programs
        WHERE event_id = ?
    """,(CURRENT_EVENT["event_id"],))

    programs = cursor.fetchall()

    if len(programs) == 0:
        print("\nNo Programs Found.\n")
        return

    program_details = ""

    for program in programs:

        program_details += f"""
Program Name : {program[0]}
Program Type : {program[1]}
Duration : {program[2]} Minutes
Entry Fee : ₹{program[3]}
Maximum Participants : {program[4]}

"""

    prompt = f"""
You are an expert Event Budget Planner.

Event Details

Event Name : {CURRENT_EVENT['event_name']}
Event Type : {CURRENT_EVENT['event_type']}
Guests : {CURRENT_EVENT['guests']}
Budget : ₹{CURRENT_EVENT['budget']}
Food Required : {CURRENT_EVENT['food_required']}

Programs

{program_details}

Prepare a complete budget allocation.

Include:

1. Venue
2. Food
3. Decoration
4. Programs
5. Photography
6. Sound & Lighting
7. Marketing
8. Emergency Fund
9. Miscellaneous

For every category provide

- Estimated Cost
- Percentage of Total Budget

Finally provide

- Total Estimated Cost
- Remaining Budget
- Suggestions to reduce cost if necessary.
"""

    print("\nGenerating Budget Plan...\n")

    response = ask_ai(prompt)

    print(response)

##################################################################################################################################################

# ==========================================
# Cell 8 - Schedule Functions
# ==========================================

def ai_schedule_generator():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            program_name,
            program_type,
            duration
        FROM programs
        WHERE event_id = ?
    """, (CURRENT_EVENT["event_id"],))

    programs = cursor.fetchall()

    if len(programs) == 0:
        print("\nNo Programs Found.\n")
        return

    program_list = ""

    for program in programs:

        program_list += f"""
Program Name : {program[0]}
Program Type : {program[1]}
Duration : {program[2]} Minutes

"""

    prompt = f"""
You are an Event Scheduling Expert.

Create a complete event schedule.

Event Name : {CURRENT_EVENT['event_name']}
Event Type : {CURRENT_EVENT['event_type']}
Event Date : {CURRENT_EVENT['event_date']}
Start Time : {CURRENT_EVENT['start_time']}
End Time : {CURRENT_EVENT['end_time']}

Programs

{program_list}

Instructions

Arrange every program in chronological order.

Add

- Welcome
- Breaks if required
- Lunch or Dinner if food is available
- Closing Ceremony

Return the schedule in a clean timetable.
"""

    print("\nGenerating Schedule...\n")

    response = ask_ai(prompt)

    print(response)


def view_schedule():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    print("\nGenerate the schedule using AI.\n")
    ai_schedule_generator()
    
#######################################################################################################################################################
# ==========================================
# Cell 9 - AI Chatbot
# ==========================================

def event_chatbot():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            program_name,
            program_type,
            duration
        FROM programs
        WHERE event_id = ?
    """, (CURRENT_EVENT["event_id"],))

    programs = cursor.fetchall()

    program_details = ""

    if programs:

        for program in programs:

            program_details += f"""
Program Name : {program[0]}
Program Type : {program[1]}
Duration : {program[2]} Minutes
"""

    print("\n********** EVENT AI CHATBOT **********")
    print("Type 'exit' to return.\n")

    while True:

        user_query = input("You : ").strip()

        if user_query.lower() in EXIT_COMMANDS:
            print()
            break

        prompt = f"""
You are an AI Event Management Assistant.

Event Details

Event Name : {CURRENT_EVENT['event_name']}
Event Type : {CURRENT_EVENT['event_type']}
Guests : {CURRENT_EVENT['guests']}
Budget : ₹{CURRENT_EVENT['budget']}
Event Date : {CURRENT_EVENT['event_date']}
Start Time : {CURRENT_EVENT['start_time']}
End Time : {CURRENT_EVENT['end_time']}
Food Required : {CURRENT_EVENT['food_required']}

Programs

{program_details}

User Question

{user_query}

Answer only according to this event.
If appropriate, provide practical suggestions.
"""

        response = ask_ai(prompt)

        print("\nAI :", response)
        print


##################################################################################################################################################
# ==========================================
# Cell 9B - AI Event Detail Plan
# ==========================================

def ai_event_detail_plan():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            program_name,
            program_type,
            duration
        FROM programs
        WHERE event_id = ?
    """, (CURRENT_EVENT["event_id"],))

    programs = cursor.fetchall()

    program_details = ""

    if programs:

        for program in programs:

            program_details += f"""
Program Name : {program[0]}
Program Type : {program[1]}
Duration : {program[2]} Minutes
"""

    else:

        program_details = "No programs have been created yet."

    prompt = f"""
You are an expert Event Management Planner.

Prepare a detailed event plan.

Event Details

Event Name : {CURRENT_EVENT['event_name']}
Event Type : {CURRENT_EVENT['event_type']}
Guests : {CURRENT_EVENT['guests']}
Budget : ₹{CURRENT_EVENT['budget']}
Event Date : {CURRENT_EVENT['event_date']}
Start Time : {CURRENT_EVENT['start_time']}
End Time : {CURRENT_EVENT['end_time']}
Food Required : {CURRENT_EVENT['food_required']}

Programs

{program_details}

Generate a professional event plan including:

1. Event Overview

2. Preparation Checklist

3. Required Staff

4. Required Equipment

5. Decoration Suggestions

6. Food Planning

7. Safety Measures

8. Timeline Before Event

9. Timeline During Event

10. Risk Management

11. Final Recommendations

Give the answer in a clean structured format.
"""

    print("\nGenerating Event Plan...\n")

    response = ask_ai(prompt)

    print(response)

######################################################################################################################################################

    
    # ==========================================
# Cell 9C - Guest Management
# ==========================================

def add_guest():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    print("\n********** ADD GUEST **********\n")

    guest_name = get_input("Guest Name : ")
    if guest_name is None:
        return

    phone = get_input("Phone Number : ")
    if phone is None:
        return

    email = get_input("Email : ")
    if email is None:
        return

    guest_id = generate_id()

    cursor.execute("""
        INSERT INTO guests(
            guest_id,
            event_id,
            guest_name,
            phone,
            email
        )
        VALUES(?,?,?,?,?)
    """, (
        guest_id,
        CURRENT_EVENT["event_id"],
        guest_name,
        phone,
        email
    ))

    conn.commit()

    print("\nGuest Added Successfully.\n")


def view_guests():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            guest_name,
            phone,
            email
        FROM guests
        WHERE event_id = ?
        ORDER BY guest_name
    """, (CURRENT_EVENT["event_id"],))

    guests = cursor.fetchall()

    if not guests:
        print("\nNo Guests Found.\n")
        return

    print(f"\n********** GUEST LIST : {CURRENT_EVENT['event_name']} **********\n")

    for index, guest in enumerate(guests, start=1):

        print(f"{index}. {guest[0]}")
        print(f"   Phone : {guest[1]}")
        print(f"   Email : {guest[2]}")
        print("-" * 40)


def guest_menu():

    while True:

        print("\n********** GUEST MANAGEMENT **********\n")

        print("1. Add Guest")
        print("2. View Guests")
        print("0. Back")

        choice = input("\nEnter Choice : ").strip()

        if choice == "1":
            add_guest()

        elif choice == "2":
            view_guests()

        elif choice == "0":
            break

        else:
            print("\nInvalid Choice.\n")
    
  #######################################################################################################################################
def view_guests():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            guest_name,
            phone,
            email
        FROM guests
        WHERE event_id = ?
        ORDER BY guest_name
    """, (CURRENT_EVENT["event_id"],))

    guests = cursor.fetchall()

    if not guests:
        print("\nNo Guests Found.\n")
        return

    print(f"\n********** GUEST LIST : {CURRENT_EVENT['event_name']} **********\n")

    for index, guest in enumerate(guests, start=1):

        print(f"{index}. {guest[0]}")
        print(f"   Phone : {guest[1]}")
        print(f"   Email : {guest[2]}")
        print("-" * 40)

###################################################################################################################################################
    # ==========================================
# Cell 9D - AI Invitation Generator
# ==========================================

def ai_invitation_generator():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            guest_name
        FROM guests
        WHERE event_id = ?
    """, (CURRENT_EVENT["event_id"],))

    guests = cursor.fetchall()

    guest_count = len(guests)

    prompt = f"""
You are an expert invitation writer.

Generate a professional invitation for the following event.

Event Name : {CURRENT_EVENT['event_name']}
Event Type : {CURRENT_EVENT['event_type']}
Guests Expected : {CURRENT_EVENT['guests']}
Guest List Created : {guest_count}
Budget : ₹{CURRENT_EVENT['budget']}
Event Date : {CURRENT_EVENT['event_date']}
Start Time : {CURRENT_EVENT['start_time']}
End Time : {CURRENT_EVENT['end_time']}
Food Required : {CURRENT_EVENT['food_required']}

Generate a beautiful invitation containing:

1. Attractive Heading
2. Welcome Message
3. Event Name
4. Event Type
5. Date
6. Time
7. Food Information
8. Closing Message

Return only the invitation.
"""

    print("\nGenerating Invitation...\n")

    response = ask_ai(prompt)

    print(response)
    
############################################################################################################################################
    # ==========================================
# Cell 9E - AI Vendor Suggestions
# ==========================================

def ai_vendor_suggestions():

    if CURRENT_EVENT is None:
        print("\nPlease select an event first.\n")
        return

    cursor.execute("""
        SELECT
            program_name,
            program_type
        FROM programs
        WHERE event_id = ?
    """, (CURRENT_EVENT["event_id"],))

    programs = cursor.fetchall()

    program_details = ""

    if programs:

        for program in programs:

            program_details += f"""
Program Name : {program[0]}
Program Type : {program[1]}
"""

    else:

        program_details = "No programs added."

    prompt = f"""
You are an experienced Event Management Consultant.

Suggest suitable vendors for the following event.

Event Details

Event Name : {CURRENT_EVENT['event_name']}
Event Type : {CURRENT_EVENT['event_type']}
Guests : {CURRENT_EVENT['guests']}
Budget : ₹{CURRENT_EVENT['budget']}
Food Required : {CURRENT_EVENT['food_required']}

Programs

{program_details}

Suggest vendors for:

1. Venue
2. Catering (if food is required)
3. Decoration
4. Photography & Videography
5. Sound & Lighting
6. DJ / Entertainment (if required)
7. Security
8. Event Management Team

For each vendor category provide:

- Vendor Type
- Why they are suitable
- Approximate Budget Range

Keep the response concise and well structured.
"""

    print("\nGenerating Vendor Suggestions...\n")

    response = ask_ai(prompt)

    print(response)
    
    
    
    
###################################################################################################################################################    
    
# ==========================================
# Cell 10 - Main Menu
# ==========================================

def print_header():

    print("\n" + "*" * 50)
    print("          EVENT MANAGEMENT SYSTEM")
    print("*" * 50)


def main_menu():

    while True:

        print_header()

        print("\nEVENT MANAGEMENT")
        print("1. Create Event")
        print("2. View Events")
        print("3. Select Event")

        print("\nAI FEATURES")
        print("4. AI Event Detail Plan")
        print("5. AI Program Suggestion")
        print("6. AI Entry Fee Calculator")
        print("7. AI Budget Planner")
        print("8. AI Schedule Generator")
        print("9. AI Chatbot")
        print("10. AI Invitation Generator")
        print("11. AI Vendor Suggestions")

        print("\nPROGRAM MANAGEMENT")
        print("12. Create Program")
        print("13. View Programs")

        print("\nGUEST MANAGEMENT")
        print("14. Add Guest")
        print("15. View Guest list")

        print("\nOTHER")
        print("0. Exit")

        choice = input("\nEnter Choice : ").strip()

        if choice == "1":
            create_event()

        elif choice == "2":
            view_events()

        elif choice == "3":
            select_event()

        elif choice == "4":
            ai_event_detail_plan()

        elif choice == "5":
            ai_program_suggestion()

        elif choice == "6":
            ai_entry_fee_calculator()

        elif choice == "7":
            ai_budget_planner()

        elif choice == "8":
            ai_schedule_generator()

        elif choice == "10":
            ai_invitation_generator()
    

        elif choice == "9":
            event_chatbot()

        elif choice == "11":
            ai_vendor_suggestions()
    

        elif choice == "12":
            create_program()

        elif choice == "13":
            view_programs()

        elif choice == "14":
            add_guest()


        elif choice == "15":
            view_guests()

        elif choice == "0":
            print("\nExiting Event Management System...\n")
            break

        else:
            print("\nInvalid Choice.\n")
main_menu()