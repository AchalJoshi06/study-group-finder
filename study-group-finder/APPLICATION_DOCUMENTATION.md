# Study Group Finder - Complete Application Documentation

## 1. Application Overview

Study Group Finder is a Flask web application that helps students:

- register and log in
- manage their profile (subjects, skill level, availability)
- create study groups
- browse, filter, join, and leave groups
- view a dashboard with joined groups, suggestions, and upcoming sessions

The app uses server-rendered Jinja templates with custom CSS and SQLite for local persistence.

## 2. Tech Stack

Backend:

- Flask 3.0.3
- Flask-Login 0.6.3
- Flask-SQLAlchemy 3.1.1
- python-dotenv 1.0.1

Frontend:

- Jinja2 templates
- Bootstrap 5.3.3 (CDN)
- Bootstrap Icons (CDN)
- Custom CSS and JS

Database:

- SQLite (default local database in `instance/app.db`)

## 3. Project Structure

```
study-group-finder/
  app.py
  config.py
  requirements.txt
  README.md
  APPLICATION_DOCUMENTATION.md
  database/
    db.py
    schema.sql
  models/
    user.py
    group.py
    membership.py
  routes/
    auth_routes.py
    group_routes.py
    user_routes.py
  templates/
    base.html
    index.html
    login.html
    register.html
    dashboard.html
    create_group.html
    browse_groups.html
    profile.html
  static/
    style.css
    script.js
  instance/
```

## 4. Configuration

Defined in `config.py`:

- `SECRET_KEY`: session and CSRF-related secret
- `SQLALCHEMY_DATABASE_URI`:
  - default: `sqlite:///.../instance/app.db`
  - can be overridden with `DATABASE_URL`
- `SQLALCHEMY_TRACK_MODIFICATIONS = False`

## 5. App Initialization

Defined in `app.py`:

1. Creates Flask app (`create_app()`)
2. Loads `Config`
3. Initializes extensions (`db`, `login_manager`)
4. Registers blueprints:
   - `auth_bp`
   - `group_bp`
   - `user_bp`
5. Exposes home route (`/`) with recent groups
6. Defines CLI commands:
   - `flask init-db`
   - `flask seed-db`
7. Ensures tables exist with `db.create_all()`

## 6. Authentication and Session Handling

In `database/db.py` and `models/user.py`:

- `LoginManager` is configured with:
  - `login_view = "auth.login"`
  - `login_message_category = "warning"`
- `User` model mixes in `UserMixin`
- Passwords are hashed via Werkzeug:
  - `set_password()` uses `generate_password_hash`
  - `check_password()` uses `check_password_hash`
- User loader resolves session identity by integer `user_id`

## 7. Data Model

### 7.1 User (`models/user.py`)

Fields:

- `id` (PK)
- `name` (required)
- `email` (unique, required)
- `password_hash` (required)
- `subjects` (text, default empty)
- `skill_level` (default `Beginner`)
- `availability` (text, default empty)
- `created_at` (UTC timestamp)

Relationships:

- `memberships` -> `GroupMember`
- `created_groups` -> `StudyGroup`

### 7.2 StudyGroup (`models/group.py`)

Fields:

- `id` (PK)
- `subject` (required)
- `description` (required)
- `schedule` (required)
- `max_members` (default 5)
- `creator_id` (FK -> user.id)
- `created_at` (UTC timestamp)

Relationships:

- `creator` -> `User`
- `members` -> `GroupMember`

Computed property:

- `current_member_count`: `len(self.members)`

### 7.3 GroupMember (`models/membership.py`)

Fields:

- `user_id` (FK -> user.id, part of composite PK)
- `group_id` (FK -> study_group.id, part of composite PK)
- `joined_at` (UTC timestamp)

Relationships:

- `user` -> `User`
- `group` -> `StudyGroup`

## 8. Seed Data

CLI command: `flask seed-db`

Behavior:

- creates tables if needed
- skips seeding if at least one user already exists
- inserts sample users, groups, and memberships

Sample accounts:

- `ava@example.com` / `password123`
- `liam@example.com` / `password123`
- `noah@example.com` / `password123`

Sample groups:

- Math - Mon 6PM
- Chemistry - Thu 6PM
- History - Sat 10AM

## 9. Utility Logic

### 9.1 Input normalization (`utils/validators.py`)

- `normalize_text(value)`: trims leading/trailing whitespace
- `split_csv_field(value)`: converts comma-separated text into cleaned tokens

### 9.2 Group suggestion logic (`utils/matcher.py`)

`suggest_groups_for_user(user, groups, joined_group_ids, limit=5)` scoring:

- skip groups already joined
- subject exact match with user subjects: `+3`
- availability substring overlap with group schedule: `+2` per overlap
- available seat in group: `+1`
- keeps only positive-score groups
- sorts descending by score and returns top `limit`

## 10. Route Reference

### 10.1 Root Route (`app.py`)

- `GET /`
  - Public home page
  - Renders recent groups in `index.html`

### 10.2 Auth Routes (`routes/auth_routes.py`)

- `GET, POST /register`
  - Redirects authenticated users to dashboard
  - Validates required fields
  - Rejects duplicate emails
  - Creates new user with hashed password

- `GET, POST /login`
  - Redirects authenticated users to dashboard
  - Validates credentials
  - Starts login session

- `GET /logout`
  - Requires authentication
  - Ends login session

### 10.3 Group Routes (`routes/group_routes.py`)

Blueprint prefix: `/groups`

- `GET, POST /groups/create`
  - Requires authentication
  - Validates input and `max_members >= 2`
  - Creates group and auto-enrolls creator

- `GET /groups/browse`
  - Requires authentication
  - Optional filters:
    - `subject`
    - `time`
  - Renders browse page with group list and joined group IDs

- `POST /groups/<group_id>/join`
  - Requires authentication
  - Guards against duplicate membership
  - Guards against full groups

- `POST /groups/<group_id>/leave`
  - Requires authentication
  - Removes membership if present

### 10.4 User Routes (`routes/user_routes.py`)

- `GET /dashboard`
  - Requires authentication
  - Renders joined groups, suggested groups, and upcoming sessions

- `GET, POST /profile`
  - Requires authentication
  - Updates name, subjects, skill level, availability
  - Enforces non-empty name

## 11. Frontend Templates

- `base.html`: app shell, navbar, flash messages, CSS/JS includes
- `index.html`: home hero and recent groups preview
- `login.html`: sign-in form
- `register.html`: account creation form
- `dashboard.html`: joined/suggested/upcoming sections
- `create_group.html`: new group creation form
- `browse_groups.html`: filter and join/leave interactions
- `profile.html`: editable user profile

## 12. Static Assets

- `static/style.css`
  - global design tokens and components
  - responsive layout for navbar, dashboard, auth forms, cards

- `static/script.js`
  - simple animation-delay setup for staged fade-in effects

## 13. Database Notes

- Runtime ORM tables are named:
  - `user`
  - `study_group`
  - `group_member`
- `database/schema.sql` contains a SQL Server style schema (`Users`, `StudyGroups`, `GroupMembers`) that is useful as a reference but is not used directly by SQLAlchemy `create_all()` in current local SQLite flow.

## 14. Commands and Local Development

From project root (`study-group-finder`):

1. Create venv

```powershell
python -m venv .venv
```

2. Activate venv

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install deps

```powershell
pip install -r requirements.txt
```

4. Run app

```powershell
python app.py
```

5. Optional DB init/seed

```powershell
$env:FLASK_APP = "app.py"
flask init-db
flask seed-db
```

## 15. Known Behaviors and Constraints

- Browse and profile pages require logged-in session.
- Join operations are POST-only and guarded by membership/full-capacity checks.
- Matching is keyword/overlap based (heuristic), not ML-based.
- Seeding runs only when there are no users.

## 16. Suggested Enhancements

- Add unit and integration tests for route behavior.
- Add pagination to browse page for large datasets.
- Persist recommendation scores for analytics.
- Add API mode (JSON endpoints) for future mobile/client integration.
- Integrate AI study assistant using a dedicated blueprint and provider SDK.

## 17. Quick Troubleshooting

- Styling looks broken:
  - verify network access to Bootstrap CDN
  - hard refresh browser cache
- Template assertion errors:
  - ensure each template has one `extends` and one block definition per block name
- Login redirects unexpectedly:
  - verify `SECRET_KEY` stability and session cookie behavior
- Seed command reports skipped:
  - database already has users (expected behavior)
