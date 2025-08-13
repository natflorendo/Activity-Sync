"""
services/strava.py

Business logic for syncing Strava activities with Google Calendar.

Coordinates workflows that combine database access, 
Strava API calls, and Google Calendar API calls.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from schemas.calendar import CalendarEventCreate
from models.strava_user import StravaUser
from utils.time import format_duration
import integrations.google_calendar_api as calendar_utils
from integrations.strava_api import get_strava_activities, get_strava_activity
from datetime import datetime, timedelta, timezone
import httpx

async def save_activities(strava_user: StravaUser, activities: list[dict]):
    """
    Saves Strava activities to the user's Google Calendar.

    Converts Strava activity data into Google Calendar event format, 
    checks for duplicates, and either updates existing events 
    or creates new ones for activities that haven't been synced yet.

     Args:
        strava_user (StravaUser): The StravaUser object containing OAuth tokens.
        activities (list[dict]): List of activity data from Strava.

    Returns:
        datetime | None: UTC datetime of the latest activity's end time if any activities were processed,
                         otherwise None.
    """
    latest_end_utc: datetime | None = strava_user.last_synced_at

    if not activities:
        return latest_end_utc

    try:
        user = strava_user.user
        google_data = user.google_data

        for activity in activities:
            # Convert meters to miles
            distance = round(activity["distance"] / 1609.34, 2)
            # Convert ISO 8601 timestamp into a timezone-aware Python datetime object
            start_time = datetime.fromisoformat(activity["start_date"].replace("Z", "+00:00"))
            end_time=start_time + timedelta(seconds=activity["elapsed_time"])
            duration = format_duration(activity["elapsed_time"])
            if latest_end_utc is None or end_time.astimezone(timezone.utc) > latest_end_utc:
                latest_end_utc = end_time.astimezone(timezone.utc)
            
            event = CalendarEventCreate(
                summary=f"({distance} mi) {activity['name']}",
                description=(
                    f"{distance} miles\n"
                    f"Duration: {duration}\n\n"
                    f"View on Strava: https://www.strava.com/activities/{activity['id']}"    
                ),
                start_time=start_time,
                end_time=end_time,
                time_zone=activity["timezone"]
            )
            event_data_json = calendar_utils.build_event_data(event)
            
            # Tag event data with Strava activity id for updating
            event_data_json.setdefault("extendedProperties", {}).setdefault("private", {})[
                "strava_activity_id"
            ] = activity["id"]

            existing_event_id = await calendar_utils.find_event_by_strava_id(
                google_data.access_token, user.calendar_id, activity["id"]
            )
            if existing_event_id:
                # Update existing event
                print(f"⚠️⚠️⚠️ {existing_event_id} ⚠️⚠️⚠️")
                await calendar_utils.update_google_calendar_event(
                    google_data.access_token, user.calendar_id, existing_event_id, event_data_json
                )
                print(f"🔁 Event updated for activity: {event.summary} {event.start_time}")
            else:
                # Create new event
                await calendar_utils.create_google_calendar_event(
                    google_data.access_token, user.calendar_id, event_data_json
                )
                print(f"✅ Event created for activity: {event.summary} {event.start_time}")
        
        return latest_end_utc if latest_end_utc else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⚠️ Failed to save activity {activity.get('id')}: {str(e)}")


async def sync_strava_data(strava_user: StravaUser, db: Session):
    """
    Syncs Strava activities to the user's Google Calendar

    Fetches activities from Strava after the last synced timestamp,
    converts them into Google Calendar events, and updates last_synced_at.

    Args:
        strava_user (StravaUser): The StravaUser object containing OAuth tokens and last_synced_at timestamp.
        db (Session): The database session.

    Returns:
        None
    """
    user = strava_user.user
    google_data = user.google_data

    try:
        # Strava's `after` parameter must be a UNIX timestamp (int), not a datetime.
        # Avoids timezone/formatting issues and makes filtering faster.
        after = int(strava_user.last_synced_at.timestamp()) if strava_user.last_synced_at else None
        activities = await get_strava_activities(strava_user.access_token, after)

        user.calendar_id = await calendar_utils.get_or_create_strava_calendar(google_data.access_token)

        latest_time_utc = await save_activities(strava_user, activities)
        strava_user.last_synced_at = latest_time_utc
        db.commit()
        db.refresh(strava_user)
    except Exception as e:
        db.rollback()
        if e.response.status_code in (400, 401):
            raise HTTPException(status_code=401, detail="google_unauthorized: token refresh failed")
        raise HTTPException(status_code=500, detail=f"Failed to sync Strava data: {str(e)}")

async def update_strava_activity(strava_user: StravaUser, activity_id: int):
    """
    Fetches a single Strava activity by ID and syncs updated details to user's Google Calendar
    
    Args:
        strava_user (StravaUser): The StravaUser object containing OAuth tokens.
        activity_id (int): The ID of the activity to update.
        db (Session): The database session.

    Returns:
        None

    Notes:
        Does NOT modify last_synced_at, as updates do not affect the sync window.
    """
    try:
        activity = await get_strava_activity(strava_user, activity_id)

        await save_activities(strava_user, [activity])
    except Exception as e:
        if e.response.status_code in (400, 401):
            raise HTTPException(status_code=401, detail="google_unauthorized: token refresh failed")
        raise HTTPException(status_code=500, detail=f"Failed to update Strava activity {activity_id}: {str(e)}")
    
async def delete_strava_activity(strava_user: StravaUser, activity_id: int, db: Session):
    """
    Remove the Google Calendar event linked to the given Strava activity.
    
    Args:
        strava_user (StravaUser): The StravaUser object containing OAuth tokens.
        activity_id (int): The ID of the Strava activity to remove.
        db (Session): The database session.

    Returns:
        dict: Status indicating whether the event was deleted or not found.

    Notes:
        Does NOT modify last_synced_at, as deletions do not affect the sync window.
    """
    user = strava_user.user
    google_data = user.google_data

    try:
        # Reset last synced at to the start of the day
        strava_user.last_synced_at = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        db.commit()
        db.refresh(strava_user)
        
        existing_event_id = await calendar_utils.find_event_by_strava_id(
            google_data.access_token, user.calendar_id, activity_id
        )

        if not existing_event_id:
            # Nothing to delete (treated as success)
            return {"status": "no event"}
        
        # Delete the event
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"https://www.googleapis.com/calendar/v3/calendars/{user.calendar_id}/events/{existing_event_id}",
                headers={"Authorization": f"Bearer {google_data.access_token}"}
            )
            response.raise_for_status()

        print(f"‼️ Event deleted: {existing_event_id}, {activity_id}")
    except Exception as e:
        db.rollback()
        if e.response.status_code in (400, 401):
            raise HTTPException(status_code=401, detail="google_unauthorized: token refresh failed")
        raise HTTPException(status_code=500, detail=f"Unexpected error while deleting activity {activity_id}: {str(e)}")