# Study Group Finder App

A beginner-friendly full-stack Flask web app to help students discover and join study groups.

## Features

- User authentication (register, login, logout)
- User profile management (subjects, skill level, availability)
- Create study groups (subject, description, schedule, max members)
- Browse and filter groups by subject and schedule
- Join and leave groups
- Simple matching suggestions on dashboard
- Dashboard with joined groups and upcoming sessions
- SQLite database for local development

## Tech Stack

- Backend: Flask + Flask-SQLAlchemy + Flask-Login
- Frontend: Flask templates (Jinja2) + basic CSS
- Database: SQLite

## Folder Structure

```
study-group-finder/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── templates/
├── static/
├── models/
├── routes/
├── database/
├── utils/
└── instance/
```

## Run Locally

1. Open a terminal in the project folder.
2. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies.

```powershell
pip install -r requirements.txt
```

4. Run the app.

```powershell
python app.py
```

5. Open `http://127.0.0.1:5000` in your browser.

## Seed Sample Data

Use Flask CLI commands to initialize and seed the database:

```powershell
$env:FLASK_APP = "app.py"
flask init-db
flask seed-db
```

### Sample Login Accounts

After seeding:

- `ava@example.com` / `password123`
- `liam@example.com` / `password123`
- `noah@example.com` / `password123`

## Notes

- To use a custom secret key, set `SECRET_KEY` in environment variables.
- To use a custom database path, set `DATABASE_URL`.
