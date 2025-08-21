# Activity Sync

## Table of Contents
* [Overview](#overview)
* [Live Demo](#live-demo)
* [Features](#features)
* [Requirements](#requirements)
* [How To Run Locally](#how-to-run-locally)
* [Tech Stack](#tech-stack)
* [Visuals](#visuals)
* [Desired Future Improvements](#desired-future-improvements)
* [Helpful Resources](#helpful-resources)

---

## Overview
Activity Sync is a full-stack integration platform that automatically syncs your Strava activities to Google calendar, giving you an accurate record of when you actually worked out so you can plan your time more effectively. By making real workout times visible on your calendar, it’s easier to spot patterns like consistent delays between when you planned to work out and when you actually started so you can reduce “dead time” and plan more realistically. 

Once you connect your Strava and Google accounts the app listens for new or updated Strava activities through Strava’s webhook system, processes them through a Cloudflare Worker proxy for retry resilience, and creates Google Calendar events that include distance, duration, activity name, and a direct link to the Strava activity. It also keeps your calendar in sync by updating and deleting calendar events when your Strava activities change or are removed.

---

## Live Demo
https://activitysync-client.onrender.com/

---

## Features
* **Strava OAuth Integration**: Link your Strava account to allow automated activity syncing.
* **Google OAuth Integration**: Connect your Google accoutn so the app can create, update, and delete events in your calendar.
* **Real-Time Webhook Sync**: Listens to Strava webhook events for activty creation, updates, and deletion.
* **Cloudflare Worker Proxy with Retry Proxy**: Handles webhood forwarding to ensure events aren't lost if the beackend is temporarily unavailable.
    * Mainly to handle cases where Render puts the backend to sleep after 15 minutes of inactivity (with the free plan).
* **Activity-to-Calendar Mapping**: Automatically formates distance (miles), duration, and activity name for calendar events.
* **Token Refresh Handling**: Stores and refreshes tokens to maintain long-term sync without manual reauthorization.
    * *Note*: If the backend is asleep (e.g., when Render puts it into idle mode), the frontend may show you as logged out until the server wakes up.
* **Database Integration**: All user account data is stored in a PostgreSQL databbase using SQLAlchemy ORM.

---

## Requirements
Before running the repository locally, ensure you have the following installed:
* **Python** (3.11+): Required to run the FastAPI backend
* **Node.js** (v20+): Required to run the frontend and Cloudflare Worker.
* **npm** (comes with Node.js): Used to install project dependencies.
* **PostgreSQL** (v17+): A relational database used to store user accounts and OAuth tokens.
* **Git**: To clone the repository and manage code.
* **Optional - VS Code** (or your preferred code editor): Recommended for development, debugging, and running scripts easily.
---

## How To Run Locally
### 3. Option A: One-command Setup (Recommended)
Use this to install all dependencies (frontend, backend, and root-level) with a single command:
```bash
npm run setup
```
This will:
* Install backend dependencies (*server*)
* Install frontend dependencies (*client*)
* Install *root-level* dependencies

Once setup is complete, you can run the app concurrently:
```bash
npm run dev
```

**⚠️ Avoid using slashes (/) in parent folder names.**
If you clone or move this project into a folder with a name like `CS 440/442`, your shell will interpret that as a nested folder structure, which can break scripts that rely on npx, ts-node, or prisma.

### 4. Option B: Run Backend and Frontend Concurrently (Manual Setup - One Terminal)
```bash
# Step 1: Install dependencies in backend
cd server
python3 -m venv .venv
source .venv/bin/activate      # (Windows: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt

# Step 2: Install dependencies in frontend
cd ../client
npm install

# Step 3: Install root-level dependencies and run both
cd ..
npm install
npm run dev
```


### 5. Option C: Run Backend and Frontend Separately (Requires Two Terminals)
#### In Terminal 1 – Setup Backend:
```bash
cd server
python3 -m venv .venv
source .venv/bin/activate     # (Windows: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### In Terminal 2 – Setup Frontend
```bash
cd client
npm install
npm run dev
```

---

## Tech Stack
| Layer        | Tech Used                             |
|--------------|---------------------------------------|
| Language     | Python, TypeScript                    |
| Frontend     | React (Vite) + Axios                  |
| Backend      | FastAPI                               |
| Worker Proxy | Cloudflare Workers                    |
| Database     | PostgreSQL + SQLAlchemy ORM           |
| Auth	       | JWT + OAuth 2.0 (Google, Strava)      |
| DevOps       | Gunicorn/Uvicorn workers              |

---

## Visuals
Coming Soon
### Google Sign In Flow
### Strava Sign In Flow
### Google Calendar Event

---

## Desired Future Improvements
Here is a list of some features and enchancements I'd like to expand upon in the future:
* **Sleep Data Integration** - Add support for pulling sleep metrics alongside workouts for a more complete calendar view. (Couldn't find any official free options; Unofficial option - [python-garminconnect](https://github.com/cyberjunky/python-garminconnect))
* **Improved UI** - Display a clear message when the backend is asleep, so users know that they may appear logged out temporarily
* **Email Notifications** - Automatically notify users via email if their account becomes disconnected from Strava or Google
* **Advanced Analytics Dashboard** - Provides users with more in depth insights, such as trends in workout timing, consistency, and weekly/monthly summaries.
* **Account Management Enhancements** - Expand to have user settings that include account deletion and more self-service managemnt options
* **Updated Testing** - Add frontend and backend tests via vitest and pytest. (Initial tests existed but were not maintained during development)
* **User Customization Options** - Allow users to configure how synced event appear in Google Calendar:
    * Customize event title and description format.
    * Choose between miles or kilometers.
    * Configure calendar timezone (currently hardcoded to Chicago).
    * *Note*: the direct link to the Strava activity will remain required for all events.

---

## Helpful Resources
* Install Node.js:
    * [Macbook](https://www.youtube.com/watch?v=l53HbzbSwxQ)
    * [Windows](https://www.youtube.com/watch?v=kC56yUZCKu4)
* Set up PostgresSQL:
    * [Macbook](https://www.youtube.com/watch?v=wTqosS71Dc4)
    * [Windows](https://www.youtube.com/watch?v=IYHx0ovvxPs)
* [Strava API – Getting Started](https://developers.strava.com/docs/getting-started/) – Overview of Strava API setup and registration.
* [Strava OAuth 2.0 Overview](https://developers.strava.com/docs/authentication/#oauthoverview) – Details on the OAuth authorization process.
* [OAuth 2.0 Authorization Code Flow (RFC 6749 4.1.1)](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.1) – Official spec on attaching tokens to URLs (I used for state parameter).
* [Authlib – Starlette Client Integration](https://docs.authlib.org/en/latest/client/starlette.html) – How to implement OAuth with Starlette/FastAPI.
* [Google OAuth Consent Screen](https://developers.google.com/workspace/guides/configure-oauth-consent#scope_categories) – Scope Categories – Understanding Google’s consent screen scopes.
* [Google OAuth 2.0 Scopes](https://developers.google.com/identity/protocols/oauth2/scopes) – Full list of Google OAuth scopes.
* [Strava API – Get Logged-In Athlete Activities](https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities) – Endpoint for fetching a user’s recent activities.
* [Strava Webhooks Guide](https://developers.strava.com/docs/webhooks/) – How to subscribe, verify, and receive webhook events from Strava.
* [Cloudflare Workers Runtime API – ctx](https://developers.cloudflare.com/workers/runtime-apis/context/) – How to use context for async tasks and background work.
* [Cloudflare Workers – Environment Variables](https://developers.cloudflare.com/workers/configuration/environment-variables/) – Storing and using environment variables securely.