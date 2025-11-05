# SalesMailerV1

SalesMailer now ships with a **static management portal** that runs entirely in the browser. Configure brands, features, templates, campaigns, and preview confirmation emails without any backend dependency. Because the app is pure HTML/CSS/JS, it can be hosted directly from GitHub Pages – when someone visits the repository URL (or the configured Pages domain) the dashboard loads instantly.

## What lives where?

- `docs/` – the static site served by GitHub Pages. It contains `index.html`, `styles.css`, and `app.js`.
- `app/` – the original FastAPI project (optional). You can keep it for future automation work or remove it if you only need the browser portal.
- `pyproject.toml` – Python tooling metadata from the API project. It is not required to run the static portal.

## Features of the browser portal

- 🏷️ **Brand setup** – capture sender details, tone, and default subject per brand.
- ✨ **Feature library** – store reusable highlights with optional assets and CTAs.
- 🔗 **Brand ↔ Feature mapping** – link highlights to each brand for easy selection.
- 🧩 **Template library** – manage HTML and subject templates with simple `{{ placeholders }}`.
- 🎯 **Campaign planning** – record tone and goal guidance for each send.
- 🧲 **Lead collection** – stash incoming leads to personalise previews.
- ✉️ **Live preview** – mix and match brand assets, templates, campaigns, and features to render an email preview instantly.
- 💾 **Local-first** – everything is stored in `localStorage`, with import/export buttons for backup or collaboration.

## Publish (and run) on GitHub Pages

1. Push this repository to GitHub with the `docs/` folder on the default branch.
2. In the GitHub UI, open **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**.
4. Select the default branch (e.g. `main`) and the `/docs` folder, then click **Save**.

That’s it! GitHub Pages will build the site automatically and, once it finishes (usually under a minute), anyone can load the app by visiting:

```
https://<username>.github.io/<repository>/
```

No servers, terminals, or local runtime are required—the entire dashboard is delivered and executed straight from GitHub’s CDN.

## Optional local preview

If you would like to try changes before pushing, you can open `docs/index.html` directly in a browser or use any static file server. For example:

```bash
python -m http.server --directory docs 8000
```

Then visit [http://localhost:8000](http://localhost:8000) to see the dashboard exactly as it will appear on GitHub Pages.

## Migrating existing workspaces

- Use **Export data** before wiping `localStorage` or moving to a new browser.
- To restore a workspace, click **Import data** and select the exported JSON file.
- The JSON format mirrors the internal state so it is easy to edit manually if you need to seed data.

## Optional backend (FastAPI)

If you still need the automation pipeline (database, OpenAI, Gmail, REST API) the original FastAPI project is intact. Run it with:

```bash
pip install -e .
uvicorn app.main:app --reload
```

This is entirely optional – the Pages-ready dashboard works on its own.

## Tech stack

- Vanilla JavaScript modules for state management and templating.
- CSS with a light/dark friendly palette, optimised for readability.
- No build step required; GitHub Pages serves the files as-is.

Enjoy sending beautiful confirmation emails straight from the browser!
