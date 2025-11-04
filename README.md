# SalesMailerV1

SalesMailerV1 is a FastAPI powered portal for managing confirmation emails for incoming leads. It enables marketing teams to configure brand-specific assets, feature highlights, and email templates so confirmations can be generated and sent automatically once a lead is received from an external source (e.g. Google Apps Script).

## Key Capabilities

- **Brand configuration** – define sender identities, tone, OpenAI styling guidance, and default subjects.
- **Reusable features** – capture product/service features once and attach brand-specific assets, CTAs, and links.
- **Campaign management** – group features into monthly campaigns and mark the active campaign per brand.
- **Template library** – manage HTML templates per brand with subject placeholders powered by Jinja2.
- **Automated lead ingestion** – accept leads via a REST endpoint and instantly craft tailored confirmation emails using the selected campaign features and OpenAI generated copy.
- **Email delivery** – optional Gmail API integration to send confirmations from brand inboxes.

## Project Structure

```
app/
├── config.py                # Environment driven configuration
├── database.py              # SQLModel engine and session helpers
├── dependencies.py          # FastAPI dependencies for services
├── main.py                  # FastAPI application entrypoint
├── models.py                # SQLModel ORM models
├── routers/                 # Feature-specific API routers
│   ├── brands.py
│   ├── campaigns.py
│   ├── features.py
│   ├── leads.py
│   └── templates.py
├── schemas.py               # Pydantic schemas for request/response bodies
└── services/                # Supporting service classes
    ├── email_renderer.py
    ├── gmail_client.py
    └── openai_client.py
```

## Getting Started

1. **Install dependencies**

   ```bash
   pip install -e .
   ```

2. **Configure environment variables** (optional but recommended): copy `.env.example` to `.env` and populate OpenAI/Gmail secrets. At minimum set `OPENAI_API_KEY` to enable AI-powered copywriting.

3. **Run the API**

   ```bash
   uvicorn app.main:app --reload
   ```

4. **Explore the docs** at [http://localhost:8000/docs](http://localhost:8000/docs).

## Deployment & Hosting

This project is a FastAPI backend that must be running on a Python server to expose its web interface. Publishing the repository on GitHub alone (including GitHub Pages) does **not** execute the application, so visiting the repository URL will only show the source code.

To make the management portal available at a public URL you need to deploy it to a platform that can run FastAPI applications. A few options:

- **Render/ Railway/ Fly.io** – create a new web service, point it to this repository, set the start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and add the necessary environment variables (OpenAI, Gmail, etc.).
- **Docker container** – package the app with Uvicorn and deploy it to any container platform (Azure Web Apps, Google Cloud Run, AWS App Runner, etc.).
- **Self-hosted server** – run `uvicorn app.main:app --host 0.0.0.0 --port 8000` on a VM or bare-metal server and expose port 8000 through a reverse proxy such as Nginx.

If you want a static landing page on GitHub Pages, you can host documentation there that links to the deployed backend URL, but the API itself must live on a server that can execute Python code.

## API Overview

- `POST /brands` – create brands and configure sender/tone defaults.
- `POST /features` – add reusable feature definitions.
- `POST /features/brand` – attach features to brands with asset URLs and CTAs.
- `POST /campaigns` – create campaigns, mark active ones per brand, and assign features.
- `POST /templates` – upload HTML templates (Jinja2 syntax supported).
- `POST /leads` – ingest leads (from Google Apps Script) and automatically generate confirmation emails.
- `POST /leads/{lead_id}/preview` – regenerate previews after adjusting settings.
- `POST /leads/send` – deliver generated emails through Gmail (if configured).

## Email Personalisation

Emails are rendered by combining:

- Lead data delivered to `/leads`.
- Active campaign for the relevant brand (feature highlights, tone overrides).
- Jinja2 HTML template selected for the brand.
- OpenAI generated summary paragraph (fallback text is used when no API key is configured).

Rendered emails are stored and available for review before sending. The Gmail integration logs a warning instead of sending when credentials are not provided, keeping local development safe.

## Development Notes

- SQLite (`salesmailer.db`) is created automatically on startup.
- SQLModel relationships are eager-loaded via `selectinload` to minimise queries during email generation.
- The default HTML template ensures the system works out-of-the-box; replace it by uploading templates per brand.

