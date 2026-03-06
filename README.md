# Route Map Web App

A Python web app that lets you enter a natural-language driving route (e.g. "Skyline Blvd from 92 to 17" or "Calaveras to Felter to Sierra"). The app parses the query with **Google Gemini 2.5 Pro**, geocodes waypoints, computes the route, and displays it on a map with total distance and drive time. The API also returns an optional primary road name (`via_road`) when available.

## Setup

**Requirements:** [uv](https://docs.astral.sh/uv/) for package management.

1. Clone the repo and go to the project directory.

2. Create a virtual environment and install dependencies with uv:

   ```bash
   uv sync
   ```

3. Copy `.env.example` to `.env` and set your API key:

   ```bash
   cp .env.example .env
   ```

   Edit `.env`:

   - **GEMINI_API_KEY** (required): Get a key at [Google AI Studio](https://aistudio.google.com/apikey). Used by Gemini 2.5 Pro to parse natural-language route queries.
   - **GOOGLE_MAPS_API_KEY** (optional): If set, the app uses Google Geocoding and Directions for better US road name resolution; otherwise it uses Nominatim and OSRM. You can also set **OSRM_BASE_URL**, **NOMINATIM_BASE_URL**, **NOMINATIM_USER_AGENT**, and **NOMINATIM_DELAY_SECONDS** in `.env` to tune the free tier (see `app/config.py`).

## Run

Start the server:

```bash
uv run python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in a browser, enter a route description, and click "Get route".

## Docker

Build the image:

```bash
docker build -t map-routes .
```

Run the container (pass your Gemini API key):

```bash
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key map-routes
```

To use a `.env` file instead of inline env vars:

```bash
docker run -p 8000:8000 --env-file .env map-routes
```

Then open `http://localhost:8000`. Optional env vars (e.g. **GOOGLE_MAPS_API_KEY**) are documented in the Setup section; pass them with `-e` or via `--env-file`.

## API

- **POST /api/route** — Request body: `{ "query": "natural-language route description" }`. Returns waypoints (name, lat, lng), summary (distance in miles, duration in minutes), polyline (GeoJSON-style `[lng, lat]` pairs), and optional `via_road` (primary road name when available).

## Tests

Run the test suite:

```bash
uv run python -m pytest
```

Run with verbose output:

```bash
uv run python -m pytest -v
```

**Note (Windows/Git Bash):** Use `uv run python -m <script>` instead of `uv run <script>` (e.g. `python -m uvicorn` and `python -m pytest`). Otherwise you may see "uv trampoline failed to canonicalize script path".

## Project structure

- **app/main.py** – FastAPI app, CORS, static files, API routes
- **app/config.py** – Environment config (API keys, service URLs)
- **app/schemas.py** – Pydantic request/response models
- **app/routes/route_api.py** – `POST /api/route` endpoint
- **app/services/llm.py** – Gemini parsing of natural-language route to waypoints
- **app/services/geocode.py** – Geocoding (Nominatim or Google)
- **app/services/routing.py** – Routing (OSRM or Google Directions)
- **static/** – Frontend (index.html, app.js) with Leaflet map
