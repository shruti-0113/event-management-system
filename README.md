# Event Management System

A comprehensive, AI-powered event management application built with Python and SQLite.

## Features

### Event Management
- **Create, View, Edit, Delete** events with full details (name, type, guests, budget, date, time)
- **Select Event** to work on multiple events seamlessly
- **Event Dashboard** with real-time statistics and metrics

### Program Management
- Create sub-programs within events (competitions, workshops, performances, etc.)
- Set duration, entry fees, and participant limits
- View and delete programs

### Guest Management
- Add guests with contact information (name, phone, email)
- Track RSVP status (Pending / Confirmed / Declined)
- Color-coded guest list for quick overview

### Budget & Expense Tracking
- Add budget categories with estimated costs
- Log actual expenses during the event
- Compare estimated vs actual spending
- Track remaining budget in real-time

### Task Management
- Create preparation tasks with priority levels (High / Medium / Low)
- Track task status (Pending / In Progress / Done)
- Auto-sorted by priority for efficient planning

### AI-Powered Features (via Ollama)
- **AI Event Detail Plan** — Comprehensive event planning with checklists and timelines
- **AI Program Suggestion** — Smart activity recommendations based on event type
- **AI Entry Fee Calculator** — Revenue optimization for ticketed programs
- **AI Budget Planner** — Detailed budget allocation across all categories
- **AI Schedule Generator** — Chronological timetable with breaks and meals
- **AI Chatbot** — Interactive Q&A about your event
- **AI Invitation Generator** — Beautiful, professional invitations
- **AI Vendor Suggestions** — Vendor recommendations for all event needs

### Export & Utilities
- Export event data to **JSON** (complete event backup)
- Export guest list to **CSV** (for sharing with vendors)
- Export task list to **CSV** (for team coordination)
- **Database Backup & Restore** with timestamped backups
- Auto-backup on exit (configurable)

## Prerequisites

1. **Python 3.8+**
2. **Ollama** — Install from [ollama.ai](https://ollama.ai) and pull a model:
   ```bash
   ollama pull llama3.2
   ```
3. Start the Ollama server before running the application:
   ```bash
   ollama serve
   ```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd event-management-system
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python event.py
   ```

## Project Structure

```
event-management-system/
├── event.py                 # Main application (all features)
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── LICENSE                  # MIT License
├── config.json              # Application configuration (auto-generated)
├── prompts.json             # AI prompts template (auto-generated)
├── event_management.db      # SQLite database (auto-generated)
└── backups/                 # Database backups directory (auto-generated)
```

## Configuration

The `config.json` file (auto-created on first run) supports:

| Key           | Description                        | Default     |
|---------------|------------------------------------|-------------|
| `model`       | Ollama model to use                | `llama3.2`  |
| `currency`    | Currency symbol for display        | `₹`         |
| `auto_backup` | Backup database on exit            | `true`      |

## Database Schema

The application uses SQLite with the following tables:

- **events** — Core event information
- **programs** — Sub-events within an event
- **budgets** — Budget categories with estimated/actual costs
- **schedules** — Time slots for programs
- **guests** — Guest contact info and RSVP status
- **expenses** — Actual money spent
- **tasks** — Preparation to-do items
- **chat_history** — AI conversation log

All tables use `ON DELETE CASCADE` to maintain referential integrity.

## Usage

The main menu presents **6 categories** for a focused, progressive experience:

1. **Events** (option 1) — Create, view, select, edit, or delete events
2. **Programs** (option 2) — Create, view, or delete sub-programs
3. **Guests** (option 3) — Add guests, update RSVP status
4. **Budget & Expenses** (option 4) — Set up budget categories, log expenses
5. **Tasks** (option 5) — Create and track preparation tasks
6. **AI & Tools** (option 6) — AI features, export, dashboard, backup/restore

**Getting started:**
1. Go to **Events → Create Event** to create your first event
2. Go to **Events → Select Event** to make it the active event
3. Use other categories to manage programs, guests, budget, and tasks
4. Use **AI & Tools → AI Features** for smart suggestions

## License

This project is licensed under the [MIT License](LICENSE).
