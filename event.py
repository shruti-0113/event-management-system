# =============================================================================
# EVENT MANAGEMENT SYSTEM
# =============================================================================
# A comprehensive event management solution powered by AI (Ollama).
#
# Features:
#   - Create, view, select, edit, and delete events
#   - Manage programs, guests, budgets, and schedules
#   - AI-powered planning, suggestions, and chatbot
#   - Export data to JSON and CSV
#   - Event statistics and dashboard
#   - Database backup and restore
#   - Color-coded terminal output
#
# Author: Shruti
# =============================================================================


# =============================================================================
# SECTION 1: IMPORTS & CONFIGURATION
# =============================================================================
# All standard library and third-party imports are grouped here.
# Configuration constants control database names, file paths, and AI models.
# =============================================================================

import json
import sqlite3
import uuid
import csv
import shutil
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

import ollama

# -----------------------------------------------
# Database & File Configuration
# -----------------------------------------------
DATABASE_NAME = "event_management.db"
CONFIG_FILE = "config.json"
PROMPTS_FILE = "prompts.json"
BACKUP_DIR = "backups"

# -----------------------------------------------
# AI Model Configuration
# -----------------------------------------------
OLLAMA_MODEL = "gemma2:2b"

# -----------------------------------------------
# Event Types (predefined categories)
# -----------------------------------------------
EVENT_TYPES = [
    "Birthday",
    "Wedding",
    "Corporate",
    "College",
    "Sports",
    "Festival",
    "Seminar",
    "Workshop",
    "Other",
]

# -----------------------------------------------
# Program Types (sub-events within an event)
# -----------------------------------------------
PROGRAM_TYPES = [
    "Competition",
    "Entertainment",
    "Workshop",
    "Seminar",
    "Performance",
    "Sports",
    "Gaming",
    "Other",
]

# -----------------------------------------------
# Exit / Navigation Commands
# -----------------------------------------------
EXIT_COMMANDS = ["0", "exit", "back", "quit"]

# -----------------------------------------------
# Budget Categories (for AI budget planner)
# -----------------------------------------------
BUDGET_CATEGORIES = [
    "Venue",
    "Food & Catering",
    "Decoration",
    "Programs & Activities",
    "Photography & Videography",
    "Sound & Lighting",
    "Marketing & Promotion",
    "Security",
    "Transportation",
    "Emergency Fund",
    "Miscellaneous",
]

# -----------------------------------------------
# Terminal Colors (ANSI escape codes)
# -----------------------------------------------
class Colors:
    """ANSI color codes for terminal output formatting."""
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


# =============================================================================
# SECTION 2: PROJECT INITIALIZATION
# =============================================================================
# Sets up the database connection, creates configuration files if they don't
# exist, and verifies that the Ollama AI service is running.
# =============================================================================

# -----------------------------------------------
# Database Connection
# -----------------------------------------------
conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

# Enable foreign key enforcement (SQLite ignores FKs by default)
cursor.execute("PRAGMA foreign_keys = ON")

# -----------------------------------------------
# Default Configuration File
# -----------------------------------------------
config = {
    "model": OLLAMA_MODEL,
    "currency": "\u20b9",
    "theme": "default",
    "auto_backup": True,
}

try:
    with open(CONFIG_FILE, "x") as file:
        json.dump(config, file, indent=4)
except FileExistsError:
    # Config already exists — load it so we can use settings
    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)

# -----------------------------------------------
# Prompts Template File
# -----------------------------------------------
prompts = {
    "event_plan": "",
    "program_suggestion": "",
    "budget_planner": "",
    "entry_fee": "",
    "schedule": "",
    "chatbot": "",
    "invitation": "",
    "vendor_suggestions": "",
}

try:
    with open(PROMPTS_FILE, "x") as file:
        json.dump(prompts, file, indent=4)
except FileExistsError:
    pass

# -----------------------------------------------
# Backup Directory
# -----------------------------------------------
Path(BACKUP_DIR).mkdir(exist_ok=True)

# -----------------------------------------------
# Ollama Service Check
# -----------------------------------------------
OLLAMA_AVAILABLE = True
try:
    ollama.list()
except Exception:
    OLLAMA_AVAILABLE = False
    print(f"{Colors.RED}[WARNING] Ollama is not running.{Colors.END}")
    print(f"{Colors.YELLOW}Start Ollama and restart this application.{Colors.END}\n")


# =============================================================================
# SECTION 3: DATABASE TABLES
# =============================================================================
# All database tables are created here with IF NOT EXISTS so the script is
# idempotent. Relationships are enforced via FOREIGN KEY constraints.
# =============================================================================

# -----------------------------------------------
# Events Table — stores high-level event info
# -----------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS events(
    event_id      TEXT PRIMARY KEY,
    event_name    TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    guests        INTEGER NOT NULL,
    budget        REAL NOT NULL,
    event_date    TEXT NOT NULL,
    start_time    TEXT NOT NULL,
    end_time      TEXT NOT NULL,
    food_required TEXT NOT NULL,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# -----------------------------------------------
# Programs Table — sub-events within an event
# -----------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS programs(
    program_id        TEXT PRIMARY KEY,
    event_id          TEXT NOT NULL,
    program_name      TEXT NOT NULL,
    program_type      TEXT NOT NULL,
    duration          INTEGER,
    entry_fee         REAL DEFAULT 0,
    max_participants  INTEGER,
    created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
)
""")

# -----------------------------------------------
# Budgets Table — cost breakdown per event
# -----------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS budgets(
    budget_id      TEXT PRIMARY KEY,
    event_id       TEXT NOT NULL,
    category       TEXT NOT NULL,
    estimated_cost REAL,
    actual_cost    REAL DEFAULT 0,
    notes          TEXT DEFAULT '',
    FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
)
""")

# -----------------------------------------------
# Schedules Table — time slots for programs
# -----------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS schedules(
    schedule_id TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL,
    program_id  TEXT,
    start_time  TEXT,
    end_time    TEXT,
    notes       TEXT DEFAULT '',
    FOREIGN KEY(event_id)   REFERENCES events(event_id)   ON DELETE CASCADE,
    FOREIGN KEY(program_id) REFERENCES programs(program_id) ON DELETE SET NULL
)
""")

# -----------------------------------------------
# Guests Table — guest contact information
# -----------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS guests(
    guest_id    TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL,
    guest_name  TEXT NOT NULL,
    phone       TEXT DEFAULT '',
    email       TEXT DEFAULT '',
    rsvp_status TEXT DEFAULT 'Pending',
    FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
)
""")

# -----------------------------------------------
# Expenses Table — actual money spent
# -----------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses(
    expense_id   TEXT PRIMARY KEY,
    event_id     TEXT NOT NULL,
    expense_name TEXT NOT NULL,
    amount       REAL NOT NULL,
    expense_date TEXT,
    category     TEXT DEFAULT 'Miscellaneous',
    FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
)
""")

# -----------------------------------------------
# Tasks Table — to-do items for each event
# -----------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    task_id     TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL,
    task_name   TEXT NOT NULL,
    status      TEXT DEFAULT 'Pending',
    priority    TEXT DEFAULT 'Medium',
    due_date    TEXT DEFAULT '',
    FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
)
""")

# -----------------------------------------------
# Chat History Table — AI conversation log
# -----------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_history(
    chat_id     TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL,
    user_query  TEXT,
    ai_response TEXT,
    timestamp   TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
)
""")

conn.commit()


# =============================================================================
# SECTION 4: AI ENGINE
# =============================================================================
# Wraps the Ollama API to provide a simple ask_ai() function used by all
# AI-powered features throughout the application.
# =============================================================================

def ask_ai(prompt: str, system_role: str = None) -> str:
    """
    Send a prompt to the Ollama model and return the response text.

    Args:
        prompt:      The user query to send to the AI.
        system_role: Optional system message to set the AI's behavior.

    Returns:
        The AI's response as a string, or an error message.
    """
    if not OLLAMA_AVAILABLE:
        return "[AI Offline] Ollama is not running. Please start Ollama and try again."

    if system_role is None:
        system_role = (
            "You are an intelligent Event Management Assistant. "
            "Provide clear, practical, and well-structured answers. "
            "Use bullet points and numbered lists where appropriate."
        )

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt},
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"[AI Error] {e}"


# =============================================================================
# SECTION 5: HELPER / UTILITY FUNCTIONS
# =============================================================================
# Small utility functions used throughout the application for input handling,
# ID generation, formatting, and display.
# =============================================================================

# -----------------------------------------------
# ID Generation
# -----------------------------------------------

def generate_id() -> str:
    """Generate a unique identifier for database records."""
    return str(uuid.uuid4())


# -----------------------------------------------
# Input Helpers (with exit/back support)
# -----------------------------------------------

def get_input(message: str) -> Optional[str]:
    """
    Prompt the user for a non-empty string input.
    Returns None if the user types an exit command.
    """
    while True:
        value = input(message).strip()
        if value.lower() in EXIT_COMMANDS:
            return None
        if value == "":
            print(f"{Colors.RED}Input cannot be empty.{Colors.END}")
            continue
        return value


def get_integer(message: str) -> Optional[int]:
    """
    Prompt the user for a valid integer.
    Returns None if the user types an exit command.
    """
    while True:
        value = get_input(message)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number.{Colors.END}")


def get_float(message: str) -> Optional[float]:
    """
    Prompt the user for a valid floating-point number.
    Returns None if the user types an exit command.
    """
    while True:
        value = get_input(message)
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            print(f"{Colors.RED}Please enter a valid amount.{Colors.END}")


def get_choice(title: str, options: list, page_size: int = 7) -> Optional[str]:
    """
    Display a numbered menu and return the selected option string.
    Automatically paginates when options exceed page_size.
    Returns None if the user types an exit command.
    """
    total = len(options)
    if total <= page_size:
        print(f"\n{Colors.BOLD}{title}{Colors.END}")
        for i, option in enumerate(options, start=1):
            print(f"  {Colors.CYAN}{i}.{Colors.END} {option}")
    else:
        total_pages = (total + page_size - 1) // page_size
        page = 0
        while True:
            start = page * page_size
            end = min(start + page_size, total)
            print(f"\n{Colors.BOLD}{title}{Colors.END}  "
                  f"{Colors.YELLOW}[Page {page + 1}/{total_pages}]{Colors.END}")
            for i, option in enumerate(options[start:end], start=start + 1):
                print(f"  {Colors.CYAN}{i}.{Colors.END} {option}")
            nav = []
            if page > 0:
                nav.append(f"{Colors.CYAN}p.{Colors.END} Previous")
            if page < total_pages - 1:
                nav.append(f"{Colors.CYAN}n.{Colors.END} Next")
            if nav:
                print(f"  {Colors.GREEN}{'   '.join(nav)}{Colors.END}")

            nav_hint = ""
            if page > 0 and page < total_pages - 1:
                nav_hint = ", n/p"
            elif page > 0:
                nav_hint = ", p"
            elif page < total_pages - 1:
                nav_hint = ", n"
            while True:
                choice = get_input(f"\n  Select [1-{total}{nav_hint}] : ")
                if choice is None:
                    return None
                if choice.lower() == "n" and page < total_pages - 1:
                    page += 1
                    break
                if choice.lower() == "p" and page > 0:
                    page -= 1
                    break
                try:
                    choice = int(choice)
                    if 1 <= choice <= total:
                        return options[choice - 1]
                except ValueError:
                    pass
                print(f"{Colors.RED}Invalid choice. Try again.{Colors.END}")
        return None

    while True:
        choice = get_input(f"\n  Select [1-{total}] : ")
        if choice is None:
            return None
        try:
            choice = int(choice)
            if 1 <= choice <= total:
                return options[choice - 1]
        except ValueError:
            pass
        print(f"{Colors.RED}Invalid choice. Try again.{Colors.END}")


def yes_no(message: str) -> Optional[str]:
    """
    Ask a yes/no question and return 'Yes' or 'No'.
    Returns None if the user types an exit command.
    """
    while True:
        value = get_input(f"{message} (Yes/No): ")
        if value is None:
            return None
        value = value.lower()
        if value in ["yes", "y"]:
            return "Yes"
        if value in ["no", "n"]:
            return "No"
        print(f"{Colors.RED}Please enter Yes or No.{Colors.END}")


# -----------------------------------------------
# Display Helpers
# -----------------------------------------------

def print_header():
    """Print the application header/banner."""
    print(f"\n{Colors.HEADER}{'=' * 55}")
    print(f"{'EVENT MANAGEMENT SYSTEM':^55}")
    print(f"{'=' * 55}{Colors.END}\n")


def print_section(title: str):
    """Print a styled section divider with a title."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 55}")
    print(f"  {title}")
    print(f"{'─' * 55}{Colors.END}")


def print_success(message: str):
    """Print a green success message."""
    print(f"{Colors.GREEN}[SUCCESS] {message}{Colors.END}")


def print_error(message: str):
    """Print a red error message."""
    print(f"{Colors.RED}[ERROR] {message}{Colors.END}")


def print_warning(message: str):
    """Print a yellow warning message."""
    print(f"{Colors.YELLOW}[WARNING] {message}{Colors.END}")


def print_info(message: str):
    """Print a cyan info message."""
    print(f"{Colors.CYAN}[INFO] {message}{Colors.END}")


def clear_line():
    """Print a visual separator line."""
    print(f"{Colors.BLUE}{'─' * 50}{Colors.END}")


def pause():
    """Pause and wait for the user to press Enter."""
    input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")


# -----------------------------------------------
# Dashboard Summary & Smart Suggestions
# -----------------------------------------------

def print_dashboard() -> Optional[str]:
    """
    Print a prominent, bordered dashboard before the main menu.
    Returns the recommended option number (or None).
    """
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    border = "=" * 50
    print(f"\n  {Colors.BOLD}{border}{Colors.END}")

    if total_events == 0:
        print(f"  {Colors.YELLOW}{Colors.BOLD}STATUS:{Colors.END}  "
              f"No events in the database yet.")
        print(f"  {Colors.GREEN}>> {Colors.BOLD}Create an event first!{Colors.END}")
        print(f"     Pick option {Colors.GREEN}{Colors.BOLD}1{Colors.END} below.")
        print(f"  {Colors.BOLD}{border}{Colors.END}")
        return "1"

    if CURRENT_EVENT is None:
        print(f"  {Colors.YELLOW}{Colors.BOLD}STATUS:{Colors.END}  "
              f"{total_events} event(s) found, none selected.")
        print(f"  {Colors.GREEN}>> {Colors.BOLD}Select an event to start managing it!{Colors.END}")
        print(f"     Pick option {Colors.GREEN}{Colors.BOLD}1{Colors.END} below "
              f"> {Colors.GREEN}Select Event{Colors.END}.")
        print(f"  {Colors.BOLD}{border}{Colors.END}")
        return "1"

    # --- Gather stats for the active event ---
    eid = CURRENT_EVENT["event_id"]

    cursor.execute("SELECT COUNT(*) FROM programs WHERE event_id = ?", (eid,))
    n_programs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM guests WHERE event_id = ?", (eid,))
    n_guests = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM guests WHERE event_id = ? "
        "AND rsvp_status = 'Confirmed'",
        (eid,),
    )
    n_confirmed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM budgets WHERE event_id = ?", (eid,))
    n_budget = cursor.fetchone()[0]

    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE event_id = ?", (eid,)
    )
    total_spent = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE event_id = ?", (eid,))
    n_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE event_id = ? AND status = 'Done'",
        (eid,),
    )
    n_done = cursor.fetchone()[0]

    # --- Print event name and stats ---
    print(
        f"  {Colors.GREEN}{Colors.BOLD}ACTIVE:{Colors.END}  "
        f"{CURRENT_EVENT['event_name']} "
        f"({CURRENT_EVENT['event_type']}, "
        f"{CURRENT_EVENT['event_date']})"
    )
    print(
        f"  Guests: {n_guests} added ({n_confirmed} confirmed)  |  "
        f"Programs: {n_programs}  |  "
        f"Tasks: {n_done}/{n_tasks} done  |  "
        f"Spent: \u20b9{total_spent:,.2f} / "
        f"\u20b9{CURRENT_EVENT['budget']:,.2f}"
    )

    # --- Determine the next best action ---
    suggestion = None
    suggested_option = None

    if n_programs == 0:
        suggestion = "Add programs to your event."
        suggested_option = "2"
    elif n_budget == 0:
        suggestion = "Set up a budget breakdown."
        suggested_option = "4"
    elif n_guests == 0:
        suggestion = "Add guests to your event."
        suggested_option = "3"
    elif n_tasks == 0:
        suggestion = "Add preparation tasks."
        suggested_option = "5"
    elif n_done < n_tasks:
        pending = n_tasks - n_done
        suggestion = f"You have {pending} pending task(s)."
        suggested_option = "5"

    if suggestion:
        print(
            f"  {Colors.GREEN}>> {Colors.BOLD}NEXT: {suggestion} "
            f"Pick option {Colors.BOLD}{suggested_option}{Colors.END}"
        )

    print(f"  {Colors.BOLD}{border}{Colors.END}")
    return suggested_option


# =============================================================================
# SECTION 6: EVENT MANAGEMENT FUNCTIONS
# =============================================================================
# CRUD operations for events: create, view, select, edit, delete.
# =============================================================================

# Global variable to track the currently selected event
CURRENT_EVENT: Optional[Dict[str, Any]] = None


def create_event():
    """
    Create a new event by collecting details from the user.
    Saves the event to the database with a unique ID.
    """
    print_section("CREATE NEW EVENT")

    # --- Collect event details from the user ---
    event_name = get_input("Event Name : ")
    if event_name is None:
        return

    event_type = get_choice("Select Event Type", EVENT_TYPES)
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

    # --- Generate a unique ID and insert into database ---
    event_id = generate_id()

    cursor.execute(
        """INSERT INTO events
           (event_id, event_name, event_type, guests, budget,
            event_date, start_time, end_time, food_required)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (event_id, event_name, event_type, guests, budget,
         event_date, start_time, end_time, food_required),
    )
    conn.commit()

    print_success(f"Event '{event_name}' created successfully!")
    print_info(f"Event ID: {event_id}")


def view_events():
    """
    Display all events stored in the database in a formatted list.
    Shows key details: name, type, guests, budget, date, and time.
    """
    cursor.execute(
        """SELECT event_id, event_name, event_type, guests, budget,
                  event_date, start_time, end_time, food_required
           FROM events
           ORDER BY event_date"""
    )
    events = cursor.fetchall()

    if not events:
        print_warning("No events found. Create one first!")
        return

    print_section(f"ALL EVENTS ({len(events)} found)")

    for index, event in enumerate(events, start=1):
        print(f"\n  {Colors.BOLD}{Colors.GREEN}{index}. {event[1]}{Colors.END}")
        print(f"     ID     : {event[0][:8]}...")
        print(f"     Type   : {event[2]}")
        print(f"     Guests : {event[3]}")
        print(f"     Budget : \u20b9{event[4]:,.2f}")
        print(f"     Date   : {event[5]}")
        print(f"     Time   : {event[6]} - {event[7]}")
        print(f"     Food   : {event[8]}")
        clear_line()


def select_event() -> Optional[Dict[str, Any]]:
    """
    Let the user choose an event from the list.
    Sets the global CURRENT_EVENT variable for use by other features.

    Returns:
        A dictionary with event details, or None if cancelled.
    """
    global CURRENT_EVENT

    cursor.execute(
        """SELECT event_id, event_name, event_type, guests, budget,
                  event_date, start_time, end_time, food_required
           FROM events
           ORDER BY event_date"""
    )
    events = cursor.fetchall()

    if not events:
        print_warning("No events available. Create one first!")
        return None

    print_section("SELECT EVENT")

    for index, event in enumerate(events, start=1):
        print(f"  {Colors.CYAN}{index}.{Colors.END} {event[1]} ({event[2]})")

    while True:
        choice = get_integer(f"\n  Select Event [1-{len(events)}] : ")
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
                "food_required": event[8],
            }
            print_success(f"Event selected: {CURRENT_EVENT['event_name']}")
            return CURRENT_EVENT

        print_error("Invalid choice. Try again.")


def edit_event():
    """
    Edit an existing event's details.
    User can modify name, type, guests, budget, date, times, and food.
    """
    global CURRENT_EVENT

    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    print_section(f"EDIT EVENT: {CURRENT_EVENT['event_name']}")

    # Show current values
    print(f"\n  {Colors.YELLOW}Current values (press Enter to keep unchanged):{Colors.END}")
    print(f"  Name  : {CURRENT_EVENT['event_name']}")
    print(f"  Type  : {CURRENT_EVENT['event_type']}")
    print(f"  Guests: {CURRENT_EVENT['guests']}")
    print(f"  Budget: \u20b9{CURRENT_EVENT['budget']:,.2f}")
    print(f"  Date  : {CURRENT_EVENT['event_date']}")
    print(f"  Start : {CURRENT_EVENT['start_time']}")
    print(f"  End   : {CURRENT_EVENT['end_time']}")
    print(f"  Food  : {CURRENT_EVENT['food_required']}")

    # Collect new values (empty = keep current)
    new_name = input(f"\n  New Name [{CURRENT_EVENT['event_name']}]: ").strip()
    new_type = input(f"  New Type [{CURRENT_EVENT['event_type']}]: ").strip()
    new_guests = input(f"  New Guests [{CURRENT_EVENT['guests']}]: ").strip()
    new_budget = input(f"  New Budget [{CURRENT_EVENT['budget']}]: ").strip()
    new_date = input(f"  New Date [{CURRENT_EVENT['event_date']}]: ").strip()
    new_start = input(f"  New Start Time [{CURRENT_EVENT['start_time']}]: ").strip()
    new_end = input(f"  New End Time [{CURRENT_EVENT['end_time']}]: ").strip()
    new_food = input(f"  New Food Required [{CURRENT_EVENT['food_required']}]: ").strip()

    # Build update query dynamically (only changed fields)
    updates = []
    values = []

    if new_name:
        updates.append("event_name = ?")
        values.append(new_name)
    if new_type:
        updates.append("event_type = ?")
        values.append(new_type)
    if new_guests:
        updates.append("guests = ?")
        values.append(int(new_guests))
    if new_budget:
        updates.append("budget = ?")
        values.append(float(new_budget))
    if new_date:
        updates.append("event_date = ?")
        values.append(new_date)
    if new_start:
        updates.append("start_time = ?")
        values.append(new_start)
    if new_end:
        updates.append("end_time = ?")
        values.append(new_end)
    if new_food:
        updates.append("food_required = ?")
        values.append(new_food.capitalize())

    if not updates:
        print_info("No changes made.")
        return

    values.append(CURRENT_EVENT["event_id"])
    query = f"UPDATE events SET {', '.join(updates)} WHERE event_id = ?"
    cursor.execute(query, values)
    conn.commit()

    # Refresh CURRENT_EVENT with updated values
    cursor.execute("SELECT * FROM events WHERE event_id = ?", (CURRENT_EVENT["event_id"],))
    row = cursor.fetchone()
    CURRENT_EVENT = {
        "event_id": row[0],
        "event_name": row[1],
        "event_type": row[2],
        "guests": row[3],
        "budget": row[4],
        "event_date": row[5],
        "start_time": row[6],
        "end_time": row[7],
        "food_required": row[8],
    }

    print_success("Event updated successfully!")


def delete_event():
    """
    Delete an event and all its associated data (programs, guests, etc.)
    Requires user confirmation before deletion.
    """
    global CURRENT_EVENT

    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    print_section(f"DELETE EVENT: {CURRENT_EVENT['event_name']}")
    print_warning("This will delete ALL associated programs, guests, schedules, and data!")

    confirm = yes_no(f"Are you sure you want to delete '{CURRENT_EVENT['event_name']}'?")
    if confirm != "Yes":
        print_info("Deletion cancelled.")
        return

    # CASCADE will remove related records automatically
    cursor.execute("DELETE FROM events WHERE event_id = ?", (CURRENT_EVENT["event_id"],))
    conn.commit()

    print_success(f"Event '{CURRENT_EVENT['event_name']}' deleted successfully!")
    CURRENT_EVENT = None


# =============================================================================
# SECTION 7: PROGRAM MANAGEMENT FUNCTIONS
# =============================================================================
# CRUD operations for programs (sub-events within an event).
# =============================================================================

# Global variable to track the currently selected program
CURRENT_PROGRAM: Optional[Dict[str, Any]] = None


def create_program():
    """
    Create a new program under the currently selected event.
    Prompts for program name, type, duration, participants, and entry fee.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    print_section(f"CREATE PROGRAM — {CURRENT_EVENT['event_name']}")

    program_name = get_input("Program Name : ")
    if program_name is None:
        return

    program_type = get_choice("Select Program Type", PROGRAM_TYPES)
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

    entry_fee = 0.0
    if entry_required == "Yes":
        entry_fee = get_float("Entry Fee (\u20b9) : ")
        if entry_fee is None:
            return

    # Insert the program into the database
    program_id = generate_id()
    cursor.execute(
        """INSERT INTO programs
           (program_id, event_id, program_name, program_type,
            duration, entry_fee, max_participants)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (program_id, CURRENT_EVENT["event_id"], program_name, program_type,
         duration, entry_fee, max_participants),
    )
    conn.commit()

    print_success(f"Program '{program_name}' created successfully!")


def view_programs():
    """
    Display all programs for the currently selected event.
    Shows name, type, duration, entry fee, and max participants.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT program_id, program_name, program_type, duration,
                  entry_fee, max_participants
           FROM programs
           WHERE event_id = ?
           ORDER BY created_at""",
        (CURRENT_EVENT["event_id"],),
    )
    programs = cursor.fetchall()

    if not programs:
        print_warning("No programs found for this event.")
        return

    print_section(f"PROGRAMS — {CURRENT_EVENT['event_name']} ({len(programs)} found)")

    for index, prog in enumerate(programs, start=1):
        print(f"\n  {Colors.BOLD}{Colors.GREEN}{index}. {prog[1]}{Colors.END}")
        print(f"     ID              : {prog[0][:8]}...")
        print(f"     Type            : {prog[2]}")
        print(f"     Duration        : {prog[3]} minutes")
        print(f"     Entry Fee       : \u20b9{prog[4]:,.2f}")
        print(f"     Max Participants: {prog[5]}")
        clear_line()


def select_program() -> Optional[Dict[str, Any]]:
    """
    Let the user choose a program from the current event's program list.
    Sets the global CURRENT_PROGRAM variable.

    Returns:
        A dictionary with program details, or None if cancelled.
    """
    global CURRENT_PROGRAM

    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return None

    cursor.execute(
        """SELECT program_id, program_name, program_type, duration,
                  entry_fee, max_participants
           FROM programs
           WHERE event_id = ?""",
        (CURRENT_EVENT["event_id"],),
    )
    programs = cursor.fetchall()

    if not programs:
        print_warning("No programs available for this event.")
        return None

    print_section("SELECT PROGRAM")

    for index, prog in enumerate(programs, start=1):
        print(f"  {Colors.CYAN}{index}.{Colors.END} {prog[1]} ({prog[2]})")

    while True:
        choice = get_integer(f"\n  Select Program [1-{len(programs)}] : ")
        if choice is None:
            return None

        if 1 <= choice <= len(programs):
            prog = programs[choice - 1]
            CURRENT_PROGRAM = {
                "program_id": prog[0],
                "program_name": prog[1],
                "program_type": prog[2],
                "duration": prog[3],
                "entry_fee": prog[4],
                "max_participants": prog[5],
            }
            print_success(f"Program selected: {CURRENT_PROGRAM['program_name']}")
            return CURRENT_PROGRAM

        print_error("Invalid choice. Try again.")


def delete_program():
    """Delete a program from the currently selected event."""
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    program = select_program()
    if program is None:
        return

    confirm = yes_no(f"Delete program '{program['program_name']}'?")
    if confirm != "Yes":
        print_info("Deletion cancelled.")
        return

    cursor.execute("DELETE FROM programs WHERE program_id = ?", (program["program_id"],))
    conn.commit()

    print_success(f"Program '{program['program_name']}' deleted!")


# =============================================================================
# SECTION 8: GUEST MANAGEMENT FUNCTIONS
# =============================================================================
# Add, view, edit, and manage guests for the currently selected event.
# =============================================================================


def add_guest():
    """
    Add a new guest to the currently selected event.
    Collects name, phone, email, and optional RSVP status.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    print_section(f"ADD GUEST — {CURRENT_EVENT['event_name']}")

    guest_name = get_input("Guest Name : ")
    if guest_name is None:
        return

    phone = get_input("Phone Number : ")
    if phone is None:
        return

    email = get_input("Email : ")
    if email is None:
        return

    rsvp = get_choice("RSVP Status", ["Pending", "Confirmed", "Declined"])
    if rsvp is None:
        rsvp = "Pending"

    guest_id = generate_id()
    cursor.execute(
        """INSERT INTO guests
           (guest_id, event_id, guest_name, phone, email, rsvp_status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (guest_id, CURRENT_EVENT["event_id"], guest_name, phone, email, rsvp),
    )
    conn.commit()

    print_success(f"Guest '{guest_name}' added successfully!")


def view_guests():
    """
    Display all guests for the currently selected event.
    Shows name, phone, email, and RSVP status with color coding.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT guest_id, guest_name, phone, email, rsvp_status
           FROM guests
           WHERE event_id = ?
           ORDER BY guest_name""",
        (CURRENT_EVENT["event_id"],),
    )
    guests = cursor.fetchall()

    if not guests:
        print_warning("No guests found for this event.")
        return

    print_section(f"GUEST LIST — {CURRENT_EVENT['event_name']} ({len(guests)} guests)")

    for index, guest in enumerate(guests, start=1):
        # Color-code RSVP status
        status = guest[4]
        if status == "Confirmed":
            status_display = f"{Colors.GREEN}{status}{Colors.END}"
        elif status == "Declined":
            status_display = f"{Colors.RED}{status}{Colors.END}"
        else:
            status_display = f"{Colors.YELLOW}{status}{Colors.END}"

        print(f"\n  {Colors.BOLD}{index}. {guest[1]}{Colors.END}")
        print(f"     Phone  : {guest[2]}")
        print(f"     Email  : {guest[3]}")
        print(f"     RSVP   : {status_display}")
        clear_line()


def update_guest_rsvp():
    """
    Update the RSVP status of a guest.
    Useful for tracking confirmations before the event.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT guest_id, guest_name, rsvp_status
           FROM guests WHERE event_id = ?""",
        (CURRENT_EVENT["event_id"],),
    )
    guests = cursor.fetchall()

    if not guests:
        print_warning("No guests found.")
        return

    print_section("UPDATE RSVP STATUS")

    for index, guest in enumerate(guests, start=1):
        print(f"  {index}. {guest[1]} (Current: {guest[2]})")

    choice = get_integer(f"\n  Select Guest [1-{len(guests)}] : ")
    if choice is None:
        return

    if 1 <= choice <= len(guests):
        new_status = get_choice("New RSVP Status", ["Pending", "Confirmed", "Declined"])
        if new_status is None:
            return

        cursor.execute(
            "UPDATE guests SET rsvp_status = ? WHERE guest_id = ?",
            (new_status, guests[choice - 1][0]),
        )
        conn.commit()
        print_success(f"RSVP updated to '{new_status}' for {guests[choice - 1][1]}")
    else:
        print_error("Invalid choice.")


def delete_guest():
    """Delete a guest from the current event."""
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        "SELECT guest_id, guest_name FROM guests WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    guests = cursor.fetchall()

    if not guests:
        print_warning("No guests found.")
        return

    print_section("DELETE GUEST")

    for index, guest in enumerate(guests, start=1):
        print(f"  {index}. {guest[1]}")

    choice = get_integer(f"\n  Select Guest to Delete [1-{len(guests)}] : ")
    if choice is None:
        return

    if 1 <= choice <= len(guests):
        confirm = yes_no(f"Delete guest '{guests[choice - 1][1]}'?")
        if confirm == "Yes":
            cursor.execute("DELETE FROM guests WHERE guest_id = ?", (guests[choice - 1][0],))
            conn.commit()
            print_success(f"Guest '{guests[choice - 1][1]}' deleted!")
    else:
        print_error("Invalid choice.")


def guest_menu():
    """Sub-menu for guest management operations."""
    while True:
        print_section("GUEST MANAGEMENT")
        print(f"  {Colors.CYAN}1.{Colors.END} Add Guest")
        print(f"  {Colors.CYAN}2.{Colors.END} View Guests")
        print(f"  {Colors.CYAN}3.{Colors.END} Update RSVP Status")
        print(f"  {Colors.CYAN}4.{Colors.END} Delete Guest")
        print(f"  {Colors.CYAN}0.{Colors.END} Back to Main Menu")

        choice = input(f"\n  Enter Choice [1-4] : ").strip()

        if choice == "1":
            add_guest()
        elif choice == "2":
            view_guests()
        elif choice == "3":
            update_guest_rsvp()
        elif choice == "4":
            delete_guest()
        elif choice in EXIT_COMMANDS:
            break
        else:
            print_error("Invalid choice.")


# =============================================================================
# SECTION 9: BUDGET & EXPENSE TRACKING
# =============================================================================
# Track estimated vs actual costs, and log individual expenses.
# =============================================================================


def add_budget_category():
    """
    Add a budget category with estimated cost for the current event.
    This helps plan the budget breakdown before the event.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    print_section("ADD BUDGET CATEGORY")

    category = get_choice("Select Category", BUDGET_CATEGORIES)
    if category is None:
        return

    estimated = get_float("Estimated Cost (\u20b9) : ")
    if estimated is None:
        return

    notes = get_input("Notes (optional) : ")
    if notes is None:
        notes = ""

    budget_id = generate_id()
    cursor.execute(
        """INSERT INTO budgets
           (budget_id, event_id, category, estimated_cost, actual_cost, notes)
           VALUES (?, ?, ?, ?, 0, ?)""",
        (budget_id, CURRENT_EVENT["event_id"], category, estimated, notes),
    )
    conn.commit()

    print_success(f"Budget category '{category}' added!")


def view_budget():
    """
    Display the budget breakdown for the current event.
    Shows estimated vs actual costs and remaining budget.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT category, estimated_cost, actual_cost, notes
           FROM budgets WHERE event_id = ?""",
        (CURRENT_EVENT["event_id"],),
    )
    budgets = cursor.fetchall()

    if not budgets:
        print_warning("No budget categories found. Add some first!")
        return

    print_section(f"BUDGET BREAKDOWN — {CURRENT_EVENT['event_name']}")

    total_estimated = 0
    total_actual = 0

    for b in budgets:
        total_estimated += b[1]
        total_actual += b[2]
        diff = b[2] - b[1]
        diff_color = Colors.RED if diff > 0 else Colors.GREEN

        print(f"\n  {Colors.BOLD}{b[0]}{Colors.END}")
        print(f"    Estimated : \u20b9{b[1]:>12,.2f}")
        print(f"    Actual    : \u20b9{b[2]:>12,.2f}")
        print(f"    Diff      : {diff_color}\u20b9{diff:>+12,.2f}{Colors.END}")
        if b[3]:
            print(f"    Notes     : {b[3]}")

    print(f"\n  {Colors.BOLD}{'─' * 45}")
    print(f"  Total Estimated : \u20b9{total_estimated:>12,.2f}")
    print(f"  Total Actual    : \u20b9{total_actual:>12,.2f}")

    remaining = CURRENT_EVENT["budget"] - total_actual
    rem_color = Colors.GREEN if remaining >= 0 else Colors.RED
    print(f"  Event Budget    : \u20b9{CURRENT_EVENT['budget']:>12,.2f}")
    print(f"  Remaining       : {rem_color}\u20b9{remaining:>12,.2f}{Colors.END}")
    print(f"  {'─' * 45}{Colors.END}")


def log_expense():
    """
    Log an actual expense for the current event.
    Records the expense name, amount, date, and category.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    print_section("LOG EXPENSE")

    name = get_input("Expense Name : ")
    if name is None:
        return

    amount = get_float("Amount (\u20b9) : ")
    if amount is None:
        return

    date = get_input("Date (DD-MM-YYYY) : ")
    if date is None:
        date = datetime.now().strftime("%d-%m-%Y")

    category = get_choice("Category", BUDGET_CATEGORIES)
    if category is None:
        category = "Miscellaneous"

    expense_id = generate_id()
    cursor.execute(
        """INSERT INTO expenses
           (expense_id, event_id, expense_name, amount, expense_date, category)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (expense_id, CURRENT_EVENT["event_id"], name, amount, date, category),
    )
    conn.commit()

    print_success(f"Expense '{name}' (\u20b9{amount:,.2f}) logged!")


def view_expenses():
    """Display all expenses logged for the current event."""
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT expense_name, amount, expense_date, category
           FROM expenses WHERE event_id = ? ORDER BY expense_date""",
        (CURRENT_EVENT["event_id"],),
    )
    expenses = cursor.fetchall()

    if not expenses:
        print_warning("No expenses logged yet.")
        return

    print_section(f"EXPENSES — {CURRENT_EVENT['event_name']}")

    total = 0
    for index, exp in enumerate(expenses, start=1):
        total += exp[1]
        print(f"  {index}. {exp[0]}")
        print(f"     Amount : \u20b9{exp[1]:,.2f}")
        print(f"     Date   : {exp[2]}")
        print(f"     Category: {exp[3]}")
        clear_line()

    print(f"\n  {Colors.BOLD}Total Expenses: \u20b9{total:,.2f}{Colors.END}")


# =============================================================================
# SECTION 10: TASK MANAGEMENT
# =============================================================================
# Simple to-do list for tracking event preparation tasks.
# =============================================================================


def add_task():
    """Add a preparation task for the current event."""
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    print_section("ADD TASK")

    task_name = get_input("Task Description : ")
    if task_name is None:
        return

    priority = get_choice("Priority", ["High", "Medium", "Low"])
    if priority is None:
        priority = "Medium"

    due_date = get_input("Due Date (DD-MM-YYYY) : ")
    if due_date is None:
        due_date = ""

    task_id = generate_id()
    cursor.execute(
        """INSERT INTO tasks
           (task_id, event_id, task_name, status, priority, due_date)
           VALUES (?, ?, ?, 'Pending', ?, ?)""",
        (task_id, CURRENT_EVENT["event_id"], task_name, priority, due_date),
    )
    conn.commit()

    print_success(f"Task added: '{task_name}' (Priority: {priority})")


def view_tasks():
    """Display all tasks for the current event with their status."""
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT task_id, task_name, status, priority, due_date
           FROM tasks WHERE event_id = ?
           ORDER BY
             CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END""",
        (CURRENT_EVENT["event_id"],),
    )
    tasks = cursor.fetchall()

    if not tasks:
        print_warning("No tasks found.")
        return

    print_section(f"TASKS — {CURRENT_EVENT['event_name']} ({len(tasks)} total)")

    for index, task in enumerate(tasks, start=1):
        # Color-code status
        if task[2] == "Done":
            status = f"{Colors.GREEN}{task[2]}{Colors.END}"
        else:
            status = f"{Colors.YELLOW}{task[2]}{Colors.END}"

        # Color-code priority
        if task[3] == "High":
            priority = f"{Colors.RED}{task[3]}{Colors.END}"
        elif task[3] == "Medium":
            priority = f"{Colors.YELLOW}{task[3]}{Colors.END}"
        else:
            priority = f"{Colors.GREEN}{task[3]}{Colors.END}"

        print(f"\n  {index}. {task[1]}")
        print(f"     Status  : {status}")
        print(f"     Priority: {priority}")
        if task[4]:
            print(f"     Due     : {task[4]}")
        clear_line()


def update_task_status():
    """Update the status of a task (Pending / In Progress / Done)."""
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        "SELECT task_id, task_name, status FROM tasks WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    tasks = cursor.fetchall()

    if not tasks:
        print_warning("No tasks found.")
        return

    print_section("UPDATE TASK STATUS")

    for index, task in enumerate(tasks, start=1):
        print(f"  {index}. {task[1]} [{task[2]}]")

    choice = get_integer(f"\n  Select Task [1-{len(tasks)}] : ")
    if choice is None:
        return

    if 1 <= choice <= len(tasks):
        new_status = get_choice("New Status", ["Pending", "In Progress", "Done"])
        if new_status is None:
            return

        cursor.execute(
            "UPDATE tasks SET status = ? WHERE task_id = ?",
            (new_status, tasks[choice - 1][0]),
        )
        conn.commit()
        print_success(f"Task updated to '{new_status}'")
    else:
        print_error("Invalid choice.")


def delete_task():
    """Delete a task from the current event."""
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        "SELECT task_id, task_name FROM tasks WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    tasks = cursor.fetchall()

    if not tasks:
        print_warning("No tasks found.")
        return

    print_section("DELETE TASK")

    for index, task in enumerate(tasks, start=1):
        print(f"  {index}. {task[1]}")

    choice = get_integer(f"\n  Select Task to Delete [1-{len(tasks)}] : ")
    if choice is None:
        return

    if 1 <= choice <= len(tasks):
        confirm = yes_no(f"Delete task '{tasks[choice - 1][1]}'?")
        if confirm == "Yes":
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (tasks[choice - 1][0],))
            conn.commit()
            print_success("Task deleted!")
    else:
        print_error("Invalid choice.")


def task_menu():
    """Sub-menu for task management operations."""
    while True:
        print_section("TASK MANAGEMENT")
        print(f"  {Colors.CYAN}1.{Colors.END} Add Task")
        print(f"  {Colors.CYAN}2.{Colors.END} View Tasks")
        print(f"  {Colors.CYAN}3.{Colors.END} Update Task Status")
        print(f"  {Colors.CYAN}4.{Colors.END} Delete Task")
        print(f"  {Colors.CYAN}0.{Colors.END} Back to Main Menu")

        choice = input(f"\n  Enter Choice [1-4] : ").strip()

        if choice == "1":
            add_task()
        elif choice == "2":
            view_tasks()
        elif choice == "3":
            update_task_status()
        elif choice == "4":
            delete_task()
        elif choice in EXIT_COMMANDS:
            break
        else:
            print_error("Invalid choice.")


# =============================================================================
# SECTION 11: EXPORT & IMPORT FUNCTIONS
# =============================================================================
# Export event data to JSON/CSV and import from JSON.
# =============================================================================


def export_event_json():
    """
    Export the current event and all its data to a JSON file.
    Includes events, programs, guests, budgets, tasks, and expenses.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    print_section("EXPORT EVENT TO JSON")

    event_id = CURRENT_EVENT["event_id"]

    # Fetch all related data
    cursor.execute("SELECT * FROM programs WHERE event_id = ?", (event_id,))
    programs = cursor.fetchall()

    cursor.execute("SELECT * FROM guests WHERE event_id = ?", (event_id,))
    guests = cursor.fetchall()

    cursor.execute("SELECT * FROM budgets WHERE event_id = ?", (event_id,))
    budgets = cursor.fetchall()

    cursor.execute("SELECT * FROM tasks WHERE event_id = ?", (event_id,))
    tasks = cursor.fetchall()

    cursor.execute("SELECT * FROM expenses WHERE event_id = ?", (event_id,))
    expenses = cursor.fetchall()

    # Build export dictionary
    export_data = {
        "event": CURRENT_EVENT,
        "exported_at": datetime.now().isoformat(),
        "programs": [
            {"id": p[0], "name": p[2], "type": p[3], "duration": p[4],
             "entry_fee": p[5], "max_participants": p[6]}
            for p in programs
        ],
        "guests": [
            {"name": g[2], "phone": g[3], "email": g[4], "rsvp": g[5]}
            for g in guests
        ],
        "budgets": [
            {"category": b[2], "estimated": b[3], "actual": b[4], "notes": b[5]}
            for b in budgets
        ],
        "tasks": [
            {"name": t[2], "status": t[3], "priority": t[4], "due_date": t[5]}
            for t in tasks
        ],
        "expenses": [
            {"name": e[2], "amount": e[3], "date": e[4], "category": e[5]}
            for e in expenses
        ],
    }

    # Write to file
    filename = f"{CURRENT_EVENT['event_name'].replace(' ', '_')}_export.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=4, ensure_ascii=False)

    print_success(f"Event exported to '{filename}'")


def export_guests_csv():
    """
    Export the guest list for the current event to a CSV file.
    Useful for sharing with vendors or team members.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT guest_name, phone, email, rsvp_status
           FROM guests WHERE event_id = ?
           ORDER BY guest_name""",
        (CURRENT_EVENT["event_id"],),
    )
    guests = cursor.fetchall()

    if not guests:
        print_warning("No guests to export.")
        return

    filename = f"{CURRENT_EVENT['event_name'].replace(' ', '_')}_guests.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Phone", "Email", "RSVP Status"])
        writer.writerows(guests)

    print_success(f"Guest list exported to '{filename}' ({len(guests)} guests)")


def export_tasks_csv():
    """
    Export the task list for the current event to a CSV file.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT task_name, status, priority, due_date
           FROM tasks WHERE event_id = ?
           ORDER BY
             CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END""",
        (CURRENT_EVENT["event_id"],),
    )
    tasks = cursor.fetchall()

    if not tasks:
        print_warning("No tasks to export.")
        return

    filename = f"{CURRENT_EVENT['event_name'].replace(' ', '_')}_tasks.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Task", "Status", "Priority", "Due Date"])
        writer.writerows(tasks)

    print_success(f"Task list exported to '{filename}' ({len(tasks)} tasks)")


def export_menu():
    """Sub-menu for export options."""
    while True:
        print_section("EXPORT DATA")
        print(f"  {Colors.CYAN}1.{Colors.END} Export Event to JSON")
        print(f"  {Colors.CYAN}2.{Colors.END} Export Guests to CSV")
        print(f"  {Colors.CYAN}3.{Colors.END} Export Tasks to CSV")
        print(f"  {Colors.CYAN}0.{Colors.END} Back to Main Menu")

        choice = input(f"\n  Enter Choice [1-3] : ").strip()

        if choice == "1":
            export_event_json()
        elif choice == "2":
            export_guests_csv()
        elif choice == "3":
            export_tasks_csv()
        elif choice in EXIT_COMMANDS:
            break
        else:
            print_error("Invalid choice.")


# =============================================================================
# SECTION 12: DATABASE BACKUP & RESTORE
# =============================================================================


def backup_database():
    """
    Create a timestamped backup of the database file.
    Backups are stored in the 'backups' directory.
    """
    print_section("BACKUP DATABASE")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"event_db_backup_{timestamp}.db")

    try:
        shutil.copy2(DATABASE_NAME, backup_file)
        print_success(f"Database backed up to '{backup_file}'")
    except Exception as e:
        print_error(f"Backup failed: {e}")


def restore_database():
    """
    Restore the database from a backup file.
    Lists available backups and lets the user choose one.
    """
    print_section("RESTORE DATABASE")

    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")],
        reverse=True,
    )

    if not backups:
        print_warning("No backup files found.")
        return

    print("  Available backups:\n")
    for i, backup in enumerate(backups, 1):
        print(f"  {Colors.CYAN}{i}.{Colors.END} {backup}")

    choice = get_integer("\n  Select backup number to restore : ")
    if choice is None:
        return

    if 1 <= choice <= len(backups):
        confirm = yes_no(
            f"Restore from '{backups[choice - 1]}'? This will OVERWRITE current data!"
        )
        if confirm == "Yes":
            try:
                conn.close()
                shutil.copy2(
                    os.path.join(BACKUP_DIR, backups[choice - 1]), DATABASE_NAME
                )
                print_success("Database restored successfully!")
                print_info("Please restart the application.")
                sys.exit(0)
            except Exception as e:
                print_error(f"Restore failed: {e}")
    else:
        print_error("Invalid choice.")


# =============================================================================
# SECTION 13: EVENT DASHBOARD & STATISTICS
# =============================================================================
# Summary view showing key metrics for the current event.
# =============================================================================


def event_dashboard():
    """
    Display a comprehensive dashboard for the current event.
    Shows guest stats, budget overview, task progress, and more.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    event_id = CURRENT_EVENT["event_id"]

    # Gather statistics
    cursor.execute(
        "SELECT COUNT(*) FROM guests WHERE event_id = ?", (event_id,)
    )
    total_guests = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM guests WHERE event_id = ? AND rsvp_status = 'Confirmed'",
        (event_id,),
    )
    confirmed_guests = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM programs WHERE event_id = ?", (event_id,)
    )
    total_programs = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE event_id = ?", (event_id,)
    )
    total_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE event_id = ? AND status = 'Done'",
        (event_id,),
    )
    done_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE event_id = ?", (event_id,)
    )
    total_expenses = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT SUM(estimated_cost) FROM budgets WHERE event_id = ?", (event_id,)
    )
    total_estimated = cursor.fetchone()[0] or 0

    # Calculate days until event
    try:
        event_date = datetime.strptime(CURRENT_EVENT["event_date"], "%d-%m-%Y")
        days_until = (event_date - datetime.now()).days
    except ValueError:
        days_until = "N/A"

    # Display dashboard
    print_section(f"EVENT DASHBOARD — {CURRENT_EVENT['event_name']}")

    print(f"""
  {Colors.BOLD}EVENT INFO{Colors.END}
  {'─' * 45}
  Name       : {CURRENT_EVENT['event_name']}
  Type       : {CURRENT_EVENT['event_type']}
  Date       : {CURRENT_EVENT['event_date']}
  Time       : {CURRENT_EVENT['start_time']} - {CURRENT_EVENT['end_time']}
  Days Left  : {days_until}

  {Colors.BOLD}GUESTS{Colors.END}
  {'─' * 45}
  Total      : {total_guests} / {CURRENT_EVENT['guests']} expected
  Confirmed  : {Colors.GREEN}{confirmed_guests}{Colors.END}

  {Colors.BOLD}PROGRAMS{Colors.END}
  {'─' * 45}
  Total      : {total_programs}

  {Colors.BOLD}TASKS{Colors.END}
  {'─' * 45}
  Completed  : {Colors.GREEN}{done_tasks}{Colors.END} / {total_tasks}
  Pending    : {Colors.YELLOW}{total_tasks - done_tasks}{Colors.END}

  {Colors.BOLD}FINANCES{Colors.END}
  {'─' * 45}
  Budget     : \u20b9{CURRENT_EVENT['budget']:>12,.2f}
  Estimated  : \u20b9{total_estimated:>12,.2f}
  Spent      : \u20b9{total_expenses:>12,.2f}
  Remaining  : \u20b9{CURRENT_EVENT['budget'] - total_expenses:>12,.2f}
  {'─' * 45}
""")


# =============================================================================
# SECTION 14: AI-POWERED FEATURES
# =============================================================================
# AI-powered functions for event planning, suggestions, and chatbot.
# =============================================================================


def ai_event_detail_plan():
    """
    Generate a comprehensive event plan using AI.
    Includes preparation checklist, staffing, equipment, and more.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    # Fetch programs for context
    cursor.execute(
        "SELECT program_name, program_type, duration FROM programs WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    programs = cursor.fetchall()

    program_details = ""
    if programs:
        for p in programs:
            program_details += f"\n- {p[0]} ({p[1]}, {p[2]} min)"
    else:
        program_details = "\nNo programs created yet."

    prompt = f"""
You are an expert Event Management Planner. Prepare a detailed event plan.

EVENT DETAILS:
- Name: {CURRENT_EVENT['event_name']}
- Type: {CURRENT_EVENT['event_type']}
- Guests: {CURRENT_EVENT['guests']}
- Budget: \u20b9{CURRENT_EVENT['budget']:,.2f}
- Date: {CURRENT_EVENT['event_date']}
- Time: {CURRENT_EVENT['start_time']} to {CURRENT_EVENT['end_time']}
- Food Required: {CURRENT_EVENT['food_required']}

PROGRAMS:
{program_details}

Generate a professional event plan with:
1. Event Overview
2. Preparation Checklist (2-4 weeks before)
3. Day-Before Checklist
4. Day-Of Timeline
5. Required Staff & Volunteers
6. Equipment & Supplies
7. Decoration Suggestions
8. Food & Beverage Planning
9. Safety & Emergency Measures
10. Post-Event Tasks

Use clean formatting with headers and bullet points.
"""
    print("\n  Generating AI Event Plan...\n")
    response = ask_ai(prompt)
    print(response)


def ai_program_suggestion():
    """
    Get AI-powered program suggestions based on event details.
    Recommends suitable activities with durations and purposes.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    prompt = f"""
You are an Event Management Expert. Suggest suitable programs for this event.

EVENT DETAILS:
- Name: {CURRENT_EVENT['event_name']}
- Type: {CURRENT_EVENT['event_type']}
- Guests: {CURRENT_EVENT['guests']}
- Budget: \u20b9{CURRENT_EVENT['budget']:,.2f}
- Food: {CURRENT_EVENT['food_required']}

Suggest 8-10 programs with:
1. Program Name
2. Type (Entertainment/Competition/Workshop/etc.)
3. Duration (minutes)
4. Why it suits this event
5. Estimated cost range

Provide practical, engaging suggestions appropriate for the event type.
"""
    print("\n  Generating AI Program Suggestions...\n")
    response = ask_ai(prompt)
    print(response)


def ai_budget_planner():
    """
    Generate an AI-powered budget breakdown for the event.
    Allocates costs across venue, food, decoration, and more.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        """SELECT program_name, program_type, duration, entry_fee, max_participants
           FROM programs WHERE event_id = ?""",
        (CURRENT_EVENT["event_id"],),
    )
    programs = cursor.fetchall()

    program_details = ""
    if programs:
        for p in programs:
            program_details += f"\n- {p[0]} ({p[1]}, {p[2]} min, fee: \u20b9{p[3]})"
    else:
        program_details = "\nNo programs created yet."

    prompt = f"""
You are an expert Event Budget Planner. Prepare a complete budget allocation.

EVENT DETAILS:
- Name: {CURRENT_EVENT['event_name']}
- Type: {CURRENT_EVENT['event_type']}
- Guests: {CURRENT_EVENT['guests']}
- Total Budget: \u20b9{CURRENT_EVENT['budget']:,.2f}
- Food Required: {CURRENT_EVENT['food_required']}

PROGRAMS:
{program_details}

Provide a budget breakdown for these categories:
1. Venue
2. Food & Catering
3. Decoration
4. Programs & Activities
5. Photography & Videography
6. Sound & Lighting
7. Marketing & Promotion
8. Security
9. Transportation
10. Emergency Fund (5-10%)
11. Miscellaneous

For each category, include:
- Estimated Cost (\u20b9)
- Percentage of Total Budget
- Money-saving tips

Finally provide:
- Total Estimated Cost
- Remaining Budget
- Priority areas to invest more
- Areas where costs can be cut
"""
    print("\n  Generating AI Budget Plan...\n")
    response = ask_ai(prompt)
    print(response)


def ai_entry_fee_calculator():
    """
    Use AI to calculate ideal entry fees for a program.
    Considers event type, budget, and participant limits.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    program = select_program()
    if program is None:
        return

    prompt = f"""
You are an Event Revenue Calculator. Calculate the ideal entry fee.

EVENT:
- Type: {CURRENT_EVENT['event_type']}
- Total Guests: {CURRENT_EVENT['guests']}
- Total Budget: \u20b9{CURRENT_EVENT['budget']:,.2f}

PROGRAM:
- Name: {program['program_name']}
- Type: {program['program_type']}
- Max Participants: {program['max_participants']}

Calculate and provide:
1. Recommended Entry Fee (\u20b9)
2. Expected Registration Count (realistic estimate)
3. Expected Revenue
4. Break-even Analysis
5. Pricing Strategy Explanation

Keep the answer concise and practical.
"""
    print("\n  Calculating Entry Fee...\n")
    response = ask_ai(prompt)
    print(response)


def ai_schedule_generator():
    """
    Generate a detailed event schedule using AI.
    Arranges programs chronologically with breaks and meals.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        "SELECT program_name, program_type, duration FROM programs WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    programs = cursor.fetchall()

    if not programs:
        print_warning("No programs found. Add some first!")
        return

    program_list = ""
    for p in programs:
        program_list += f"\n- {p[0]} ({p[1]}, {p[2]} min)"

    prompt = f"""
You are an Event Scheduling Expert. Create a complete event schedule.

EVENT:
- Name: {CURRENT_EVENT['event_name']}
- Type: {CURRENT_EVENT['event_type']}
- Date: {CURRENT_EVENT['event_date']}
- Start: {CURRENT_EVENT['start_time']}
- End: {CURRENT_EVENT['end_time']}
- Food: {CURRENT_EVENT['food_required']}

PROGRAMS:
{program_list}

Create a detailed timetable with:
1. Welcome & Registration
2. Opening Ceremony
3. Each program in chronological order
4. Breaks (10-15 min every 1-2 hours)
5. Meal Break ({'Lunch' if 'Yes' in CURRENT_EVENT['food_required'] else 'N/A'})
6. Closing Ceremony

Format as a clean timetable with:
TIME | ACTIVITY | DURATION | NOTES
"""
    print("\n  Generating AI Schedule...\n")
    response = ask_ai(prompt)
    print(response)


def ai_invitation_generator():
    """
    Generate a beautiful event invitation using AI.
    Includes all event details in an attractive format.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        "SELECT COUNT(*) FROM guests WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    guest_count = cursor.fetchone()[0]

    prompt = f"""
You are an expert invitation writer. Generate a beautiful event invitation.

EVENT DETAILS:
- Name: {CURRENT_EVENT['event_name']}
- Type: {CURRENT_EVENT['event_type']}
- Expected Guests: {CURRENT_EVENT['guests']}
- Guest List: {guest_count} added
- Budget: \u20b9{CURRENT_EVENT['budget']:,.2f}
- Date: {CURRENT_EVENT['event_date']}
- Time: {CURRENT_EVENT['start_time']} to {CURRENT_EVENT['end_time']}
- Food: {CURRENT_EVENT['food_required']}

Generate a professional invitation with:
1. Decorative Heading
2. Warm Welcome Message
3. Event Name (prominent)
4. Event Type & Description
5. Date & Time (highlighted)
6. Food Information
7. RSVP Request
8. Closing Message

Make it elegant and appropriate for the event type.
"""
    print("\n  Generating AI Invitation...\n")
    response = ask_ai(prompt)
    print(response)


def ai_vendor_suggestions():
    """
    Get AI-powered vendor recommendations for the event.
    Suggests vendors for venue, catering, photography, etc.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        "SELECT program_name, program_type FROM programs WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    programs = cursor.fetchall()

    program_details = ""
    if programs:
        for p in programs:
            program_details += f"\n- {p[0]} ({p[1]})"
    else:
        program_details = "\nNo programs added yet."

    prompt = f"""
You are an experienced Event Management Consultant. Suggest vendors for this event.

EVENT:
- Name: {CURRENT_EVENT['event_name']}
- Type: {CURRENT_EVENT['event_type']}
- Guests: {CURRENT_EVENT['guests']}
- Budget: \u20b9{CURRENT_EVENT['budget']:,.2f}
- Food: {CURRENT_EVENT['food_required']}

PROGRAMS:
{program_details}

Suggest vendors for:
1. Venue
2. Catering (if food required)
3. Decoration & Florist
4. Photography & Videography
5. Sound & Lighting
6. DJ / Entertainment
7. Security
8. Event Management Team

For each vendor category provide:
- Vendor Type / Specialty
- Why they suit this event
- Estimated Budget Range
- What to look for when hiring

Keep the response concise and actionable.
"""
    print("\n  Generating AI Vendor Suggestions...\n")
    response = ask_ai(prompt)
    print(response)


def event_chatbot():
    """
    Interactive AI chatbot for answering event-related questions.
    Maintains context about the current event throughout the conversation.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    # Fetch event programs for context
    cursor.execute(
        "SELECT program_name, program_type, duration FROM programs WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    programs = cursor.fetchall()

    program_details = ""
    if programs:
        for p in programs:
            program_details += f"\n- {p[0]} ({p[1]}, {p[2]} min)"

    print_section("AI EVENT CHATBOT")
    print(f"  {Colors.YELLOW}Ask me anything about your event!{Colors.END}")
    print(f"  {Colors.YELLOW}Type 'exit' to return to the main menu.{Colors.END}\n")

    chat_count = 0

    while True:
        user_query = input(f"  {Colors.CYAN}You:{Colors.END} ").strip()

        if user_query.lower() in EXIT_COMMANDS:
            print(f"\n  {Colors.YELLOW}Chat ended. ({chat_count} messages exchanged){Colors.END}\n")
            break

        if not user_query:
            continue

        prompt = f"""
You are an AI Event Management Assistant.

EVENT CONTEXT:
- Name: {CURRENT_EVENT['event_name']}
- Type: {CURRENT_EVENT['event_type']}
- Guests: {CURRENT_EVENT['guests']}
- Budget: \u20b9{CURRENT_EVENT['budget']:,.2f}
- Date: {CURRENT_EVENT['event_date']}
- Time: {CURRENT_EVENT['start_time']} to {CURRENT_EVENT['end_time']}
- Food: {CURRENT_EVENT['food_required']}
Programs:
{program_details or '  None yet'}

USER QUESTION: {user_query}

Answer based on the event context above. Be helpful and practical.
"""
        response = ask_ai(prompt)
        print(f"\n  {Colors.GREEN}AI:{Colors.END} {response}\n")

        # Save to chat history
        chat_id = generate_id()
        cursor.execute(
            """INSERT INTO chat_history
               (chat_id, event_id, user_query, ai_response)
               VALUES (?, ?, ?, ?)""",
            (chat_id, CURRENT_EVENT["event_id"], user_query, response),
        )
        conn.commit()
        chat_count += 1


# =============================================================================
# SECTION 15: VIEW SCHEDULE (WRAPPER)
# =============================================================================


def view_schedule():
    """
    View the event schedule.
    Uses AI to generate a schedule if none exists.
    """
    if CURRENT_EVENT is None:
        print_warning("Please select an event first!")
        return

    cursor.execute(
        "SELECT COUNT(*) FROM schedules WHERE event_id = ?",
        (CURRENT_EVENT["event_id"],),
    )
    count = cursor.fetchone()[0]

    if count == 0:
        print_info("No schedule found. Generating with AI...")
        ai_schedule_generator()
    else:
        # Display existing schedule
        cursor.execute(
            """SELECT s.start_time, s.end_time,
                      p.program_name, s.notes
               FROM schedules s
               LEFT JOIN programs p ON s.program_id = p.program_id
               WHERE s.event_id = ?
               ORDER BY s.start_time""",
            (CURRENT_EVENT["event_id"],),
        )
        rows = cursor.fetchall()

        print_section(f"SCHEDULE — {CURRENT_EVENT['event_name']}")
        for row in rows:
            print(f"  {row[0]} - {row[1]}  |  {row[2]}  |  {row[3]}")


# =============================================================================
# SECTION 16: AI FEATURES MENU
# =============================================================================


def ai_features_menu():
    """Sub-menu for all AI-powered features."""
    while True:
        print_section("AI-POWERED FEATURES")
        print(f"  {Colors.CYAN}1.{Colors.END}  AI Event Detail Plan")
        print(f"  {Colors.CYAN}2.{Colors.END}  AI Program Suggestion")
        print(f"  {Colors.CYAN}3.{Colors.END}  AI Entry Fee Calculator")
        print(f"  {Colors.CYAN}4.{Colors.END}  AI Budget Planner")
        print(f"  {Colors.CYAN}5.{Colors.END}  AI Schedule Generator")
        print(f"  {Colors.CYAN}6.{Colors.END}  AI Chatbot")
        print(f"  {Colors.CYAN}7.{Colors.END}  AI Invitation Generator")
        print(f"  {Colors.CYAN}8.{Colors.END}  AI Vendor Suggestions")
        print(f"  {Colors.CYAN}0.{Colors.END}  Back to Main Menu")

        choice = input(f"\n  Enter Choice [1-8] : ").strip()

        if choice == "1":
            ai_event_detail_plan()
        elif choice == "2":
            ai_program_suggestion()
        elif choice == "3":
            ai_entry_fee_calculator()
        elif choice == "4":
            ai_budget_planner()
        elif choice == "5":
            ai_schedule_generator()
        elif choice == "6":
            event_chatbot()
        elif choice == "7":
            ai_invitation_generator()
        elif choice == "8":
            ai_vendor_suggestions()
        elif choice in EXIT_COMMANDS:
            break
        else:
            print_error("Invalid choice.")


# =============================================================================
# SECTION 17: BUDGET & EXPENSE MENU
# =============================================================================


def budget_expense_menu():
    """Sub-menu for budget and expense operations."""
    while True:
        print_section("BUDGET & EXPENSE TRACKING")
        print(f"  {Colors.CYAN}1.{Colors.END} Add Budget Category")
        print(f"  {Colors.CYAN}2.{Colors.END} View Budget Breakdown")
        print(f"  {Colors.CYAN}3.{Colors.END} Log Expense")
        print(f"  {Colors.CYAN}4.{Colors.END} View Expenses")
        print(f"  {Colors.CYAN}0.{Colors.END} Back to Main Menu")

        choice = input(f"\n  Enter Choice [1-4] : ").strip()

        if choice == "1":
            add_budget_category()
        elif choice == "2":
            view_budget()
        elif choice == "3":
            log_expense()
        elif choice == "4":
            view_expenses()
        elif choice in EXIT_COMMANDS:
            break
        else:
            print_error("Invalid choice.")


# =============================================================================
# SECTION 18: PROGRESSIVE SUB-MENUS
# =============================================================================
# These menus group related operations under high-level categories
# to keep the main menu limited and progressive.
# =============================================================================


def events_menu():
    """Sub-menu for event operations."""
    while True:
        print_section("EVENTS")
        print(f"  {Colors.CYAN}1.{Colors.END} Create Event")
        print(f"  {Colors.CYAN}2.{Colors.END} View All Events")
        print(f"  {Colors.CYAN}3.{Colors.END} Select Event")
        edit_hint = "" if CURRENT_EVENT else f" {Colors.YELLOW}(select an event first){Colors.END}"
        print(f"  {Colors.CYAN}4.{Colors.END} Edit Event{edit_hint}")
        delete_hint = "" if CURRENT_EVENT else f" {Colors.YELLOW}(select an event first){Colors.END}"
        print(f"  {Colors.CYAN}5.{Colors.END} Delete Event{delete_hint}")
        print(f"  {Colors.CYAN}0.{Colors.END} Back")

        choice = input(f"\n  Enter Choice [1-5] : ").strip()

        if choice == "1":
            create_event()
        elif choice == "2":
            view_events()
        elif choice == "3":
            select_event()
        elif choice == "4":
            edit_event()
        elif choice == "5":
            delete_event()
        elif choice in EXIT_COMMANDS:
            break
        else:
            print_error("Invalid choice.")


def programs_menu():
    """Sub-menu for program operations."""
    while True:
        print_section("PROGRAMS")
        print(f"  {Colors.CYAN}1.{Colors.END} Create Program")
        print(f"  {Colors.CYAN}2.{Colors.END} View Programs")
        print(f"  {Colors.CYAN}3.{Colors.END} Delete Program")
        print(f"  {Colors.CYAN}0.{Colors.END} Back")

        choice = input(f"\n  Enter Choice [1-3] : ").strip()

        if choice == "1":
            create_program()
        elif choice == "2":
            view_programs()
        elif choice == "3":
            delete_program()
        elif choice in EXIT_COMMANDS:
            break
        else:
            print_error("Invalid choice.")


def ai_tools_menu():
    """Sub-menu combining AI features, export, and utility operations."""
    while True:
        print_section("AI & TOOLS")
        print(f"  {Colors.CYAN}1.{Colors.END} AI Features")
        print(f"  {Colors.CYAN}2.{Colors.END} Export Data")
        print(f"  {Colors.CYAN}3.{Colors.END} Event Dashboard")
        print(f"  {Colors.CYAN}4.{Colors.END} Backup Database")
        print(f"  {Colors.CYAN}5.{Colors.END} Restore Database")
        print(f"  {Colors.CYAN}0.{Colors.END} Back")

        choice = input(f"\n  Enter Choice [1-5] : ").strip()

        if choice == "1":
            ai_features_menu()
        elif choice == "2":
            export_menu()
        elif choice == "3":
            event_dashboard()
        elif choice == "4":
            backup_database()
        elif choice == "5":
            restore_database()
        elif choice in EXIT_COMMANDS:
            break
        else:
            print_error("Invalid choice.")


# =============================================================================
# SECTION 19: MAIN MENU
# =============================================================================
# The primary entry point that ties all features together.
# =============================================================================


def main_menu():
    """
    Main application loop. Displays a limited set of top-level categories
    and routes user choices to progressive sub-menus.
    """
    while True:
        print_header()

        # --- Prominent dashboard with recommendation ---
        suggested = print_dashboard()

        # --- Top-Level Categories (max 6 choices) ---
        print(f"  {Colors.CYAN}1.{Colors.END} Events")
        print(f"  {Colors.CYAN}2.{Colors.END} Programs")
        print(f"  {Colors.CYAN}3.{Colors.END} Guests")
        print(f"  {Colors.CYAN}4.{Colors.END} Budget & Expenses")
        print(f"  {Colors.CYAN}5.{Colors.END} Tasks")
        print(f"  {Colors.CYAN}6.{Colors.END} AI & Tools")

        # --- Exit ---
        print(f"\n  {Colors.CYAN}0.{Colors.END} Exit")

        # --- Show recommendation in the input prompt ---
        hint = f" (Recommended: {suggested})" if suggested else ""
        choice = input(
            f"\n  {Colors.BOLD}Enter Choice [1-6]{hint} : {Colors.END}"
        ).strip()

        # --- Route to sub-menu ---
        if choice == "1":
            events_menu()
        elif choice == "2":
            programs_menu()
        elif choice == "3":
            guest_menu()
        elif choice == "4":
            budget_expense_menu()
        elif choice == "5":
            task_menu()
        elif choice == "6":
            ai_tools_menu()
        elif choice == "0":
            # Auto-backup on exit if enabled
            if config.get("auto_backup", False):
                print_info("Creating auto-backup before exit...")
                backup_database()
            print(f"\n  {Colors.GREEN}Thank you for using Event Management System!{Colors.END}\n")
            break
        else:
            print_error("Invalid choice. Please try again.")


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.YELLOW}Application interrupted by user.{Colors.END}")
    finally:
        conn.close()
