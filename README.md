# Vraa

This is a simple Django project for a family vacation home called **Vraa**. The site is
designed as a single‑page layout with a side navigation panel and a main content area.
The pages available from the sidebar include:

* **Frontpage** – the landing page for the site.
* **Information** – general information about the summerhouse.
* **Referater** – minutes or notes from meetings.
* **Vedtaegter** – statutes or rules governing the property.
* **Kalender** – a calendar or schedule page.

Each page currently contains a placeholder paragraph of text; these can be updated
with real content as needed.

## Prerequisites

* Python 3.11 or higher
* Django 4.x (see `requirements.txt` for installation)

## Installation

To set up the project locally:

1. Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations and start the development server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

4. Navigate to `http://127.0.0.1:8000/` in your web browser to view the site.

## Deployment

For production deployment (e.g. on DigitalOcean), configure environment variables such
as `SECRET_KEY`, set `DEBUG = False` in `settings.py`, and update `ALLOWED_HOSTS` with
the domain or IP address of your server. You may also want to serve static files
through a web server like Nginx and use `gunicorn` or similar as the application server.
