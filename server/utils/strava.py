# utils strava.py
from schemas.calendar import CalendarEventCreate
from models.strava_user import StravaUser
import utils.calendar as calendar_utils
from datetime import datetime, timedelta
import httpx

async def get_strava_activities(access_token: str, after: int | None = None):
    params = {"per_page": 10} # Get the last 10 activities

    if after:
        params["after"] = after

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.strava.com/api/v3/athlete/activities",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Unexpected error: {e}")

def format_duration(seconds: int):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

async def save_activities(strava_user: StravaUser, activities: list[dict]):
    """Saves Strava activities to the user's Google Calendar.
    Converts Strava activity data into Google Calendar event format, 
    checks for duplicates, and creates new events for activities 
    that haven't been synced yet.
    """
    if not activities:
        return

    try:
        user = strava_user.user
        google_data = user.google_data
        for activity in activities:
            # Convert meters to miles
            distance = round(activity["distance"] / 1609.34, 2)
            # Convert ISO 8601 timestamp into a timezone-aware Python datetime object
            start_time = datetime.fromisoformat(activity["start_date"].replace("Z", "+00:00"))
            duration = format_duration(activity["elapsed_time"])
            
            event = CalendarEventCreate(
                summary=f"({distance} mi) {activity['name']}",
                description=(
                    f"{distance} miles\n"
                    f"Duration: {duration}\n\n"
                    f"View on Strava: https://www.strava.com/activities/{activity['id']}"    
                ),
                start_time=start_time,
                end_time=start_time + timedelta(seconds=activity["elapsed_time"]),
                time_zone=activity["timezone"]
            )
            event_data_json = calendar_utils.build_event_data(event)
            
            if await calendar_utils.event_exists(google_data.access_token, user.calendar_id, event):
                print("⚠️⚠️⚠️ Event already exists, skipping creation. ⚠️⚠️⚠️")
                continue
            
            await calendar_utils.create_google_calendar_event(google_data.access_token, user.calendar_id, event_data_json)
            print(f"✅ Event created for activity: {event.summary} {event.start_time}")
    except Exception as e:
        print(f"⚠️ Failed to save activity {activity.get('id')}: {e}")


async def sync_strava_data(strava_user: StravaUser, access_token: str):
    """Syncs Strava activities to the user's Google Calendar"""
    # Strava's `after` parameter must be a UNIX timestamp (int), not a datetime.
    # Avoids timezone/formatting issues and makes filtering faster.
    after = int(strava_user.last_synced_at.timestamp()) if strava_user.last_synced_at else None
    activities = await get_strava_activities(access_token, after)
    
    user = strava_user.user
    google_data = user.google_data
    
    user.calendar_id = await calendar_utils.get_or_create_strava_calendar(google_data.access_token)
    await save_activities(strava_user, activities)
