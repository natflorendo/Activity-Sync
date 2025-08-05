# utils calendar.py
from schemas.calendar import CalendarEventCreate
from datetime import timezone
import httpx

async def get_or_create_strava_calendar(access_token: str):
    """"Return the calendar ID for a 'Strava' calendar. If it doesn't exist, create it."""
    try:
        async with httpx.AsyncClient() as client:
            # List calendars
            response = await client.get(
                "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            # Raises an exception if the HTTP response is not a 2xx status code
            response.raise_for_status()
            # Extracts the items list with empty list as default
            calendars = response.json().get("items", [])

            # Look for an exsiting calendar named strava
            for calendar in calendars:
                if calendar.get("summary", "").lower() == "strava":
                    return calendar["id"]
                
            # If not found, create Strava Calendar
            create_response = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "summary": "Strava",
                    "timeZone": "America/Chicago" # not sure how to give user control over this
                }
            )
            create_response.raise_for_status()
            calendar_id = create_response.json()["id"]

            # Google does not allow setting the calendar color during creation.
            # Using PATCH to partially update a resource (change calendar color)
            # 4 is Tangerine (didn't see documentation so just did guess and check)
            await client.patch(
                f"https://www.googleapis.com/calendar/v3/users/me/calendarList/{calendar_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"colorId": "4"}
            )

            return calendar_id
    except Exception as e:
        print(f"Unexpected error in get_or_create_strava_calendar: {str(e)}")

    
def build_event_data( event_data: CalendarEventCreate ):
    """Convert raw input into Google Calendar event JSON format"""
    return {
        "summary": event_data.summary,
        "description": event_data.description,
        "start": {
            "dateTime": event_data.start_time.isoformat(),
            "timeZone": event_data.time_zone
        },
        "end": {
            "dateTime": event_data.end_time.isoformat(),
            "timeZone": event_data.time_zone
        },
        "reminders": {
            "useDefault": True
        }
    }

async def event_exists(
    access_token: str,
    calendar_id: str,
    event_data: CalendarEventCreate
) -> bool:
    """Check if an event with the same name and start time already exists"""
    try:
        async with httpx.AsyncClient() as client:
            params = {
                # Use .astimezone(timezone.utc) to ensure datetimes are timezone-aware
                # Needed because there is not calendar model that has timezone=true
                # Filters events that start after or at this datetime.
                "timeMin": event_data.start_time.astimezone(timezone.utc).isoformat(),
                # Filters events that start before or at this datetime.
                "timeMax": event_data.end_time.astimezone(timezone.utc).isoformat(),
                # Expands recurring events into individual instances.
                "singleEvents": True,
                "orderBy": "startTime"
            }
            response = await client.get(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            response.raise_for_status()
            events = response.json().get("items", [])

            for event in events:
                if (event.get("summary") == event_data.summary and
                    event.get("description") == event_data.description):
                    return True
        return False
    except Exception as e:
        print(f"Error checking existing events: {str(e)}")
        return False
    
async def create_google_calendar_event(access_token: str, calendar_id: str, event_data_json: dict):
    """Create an event on a given Google Calendar"""
    try:
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=event_data_json
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Unexpected error in create_google_calendar_event: {str(e)}")

#DELETE ME
from datetime import datetime, timedelta
def get_dummy_data():
    now = datetime.now()
    return CalendarEventCreate(
        summary="Test Run",
        description="30-minute jog to test calendar sync",
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=1, minutes=30),
        time_zone="America/Chicago"
    )

# DELETE ME
async def test_event_flow(access_token: str):
    calendar_id = await get_or_create_strava_calendar(access_token)

    dummy_event = get_dummy_data()

    # Check for duplicates first
    if await event_exists(access_token, calendar_id, dummy_event):
        print("⚠️⚠️⚠️ Event already exists, skipping creation. ⚠️⚠️⚠️")
        return

    event_payload = build_event_data(dummy_event)

    # Create event if no duplicate
    created_event = await create_google_calendar_event(
        access_token=access_token,
        calendar_id=calendar_id,
        event_data_json=event_payload
    )

    print("✅ Event Created Successfully:", created_event)