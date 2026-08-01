# 0xExp

0xExp is a web-based donation management platform that connects donors, NGOs, and administrators to streamline food donation workflows. The system allows donors to publish available food items, NGOs to review and accept donations, and admins to manage verification and platform operations.

## Overview

This project is built with Flask and provides role-based dashboards for:

- Donors who want to contribute food donations
- NGOs that receive and manage donations
- Administrators who oversee users, verification, and platform activity

## Key Features

- User authentication for donors, NGOs, and admins
- Role-based dashboards and access control
- Donation creation, tracking, and management
- NGO verification and status handling
- Notification and email support
- Secure form handling with CSRF protection
- Database support for SQLite by default, with MySQL configuration available

## Tech Stack

- Python 3.10+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Migrate
- Flask-Mail
- Jinja2 Templates
- SQLite / MySQL

## Project Structure

- app.py — application factory and app initialization
- config.py — configuration and environment-based settings
- models/ — database models for users, donations, NGOs, and notifications
- routes/ — application blueprints for public, auth, donor, NGO, and admin flows
- templates/ — HTML templates for all user-facing pages
- static/ — CSS, JavaScript, and uploaded assets
- tests/ — application test cases
- migrations/ — database migration files

## Prerequisites

Make sure you have the following installed:

- Python 3.10 or newer
- pip
- Optional: MySQL server if you want to use MySQL instead of SQLite

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd 0xExp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   ```

   Windows:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the project root with settings such as:

```env
SECRET_KEY=your-secret-key
MAIL_SERVER=localhost
MAIL_PORT=25
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_USE_TLS=false
MAIL_USE_SSL=false
MAIL_DEFAULT_SENDER=noreply@fooddonation.local
```

### Database Options

- Default behavior: SQLite database stored in the instance folder
- To use MySQL, set one of the following:
  ```env
  DATABASE_URL=mysql+pymysql://user:password@host:3306/database
  ```
  or provide the individual MySQL variables used by the app configuration.

## Running the Application

Start the development server:

```bash
python app.py
```

Then open your browser at:

```text
http://127.0.0.1:5000/
```

## Running Tests

If you have pytest installed, you can run:

```bash
pytest
```

## License

This project is intended for educational and community use. Please review the repository’s licensing terms before deployment or redistribution.

## Contributing

Contributions are welcome. If you would like to improve the project:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request
