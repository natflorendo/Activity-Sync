"""
integrations/google_calendar_api.py

Functions for interacting with the Google Calendar API.

Contains direct HTTP calls to an external service and no application business logic.
"""
from fastapi import HTTPException
from schemas.calendar import CalendarEventCreate
from datetime import timezone
import httpx

async def get_or_create_strava_calendar(access_token: str):
    """"
    Return the calendar ID for a 'Strava' calendar. If it doesn't exist, create it.

    Args:
        access_token (str): The Google OAuth access token for the authenticated user.

    Returns:
        str: The ID of the "Strava" calendar.
    """
    try:
        async with httpx.AsyncClient() as client:
            # List all calendars
            response = await client.get(
                "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            # Raises an exception if the HTTP response is not a 2xx status code
            response.raise_for_status()
            # Extracts the items list with empty list as default
            calendars = response.json().get("items", [])

            # Look for an existing calendar named strava
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
        raise HTTPException(status_code=500, detail=f"Unexpected error in get_or_create_strava_calendar: {str(e)}")

    
def build_event_data( event_data: CalendarEventCreate ):
    """
    Convert raw input (CalendarEventCreate object) into Google Calendar event JSON format

    Args:
        event_data (CalendarEventCreate): The event data to convert.

    Returns:
        dict: A dictionary formatted for the Google Calendar API's event creation/update endpoints.
    """
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
    """
    Check if an event with the same name and start time already exists
    
    Args:
        access_token (str): The Google OAuth access token for the authenticated user.
        calendar_id (str): The Google Calendar ID.
        event_data (CalendarEventCreate): The event data to match.

    Returns:
        bool: True if an identical event exists, False otherwise.
    """
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
        raise HTTPException(status_code=500, detail=f"Error checking existing events: {str(e)}")
    
async def create_google_calendar_event(access_token: str, calendar_id: str, event_data_json: dict):
    """
    Create an event on a given Google Calendar
    
    Args:
        access_token (str): The Google OAuth access token for the authenticated user.
        calendar_id (str): The Google Calendar ID where the event will be created.
        event_data_json (dict): The event data in Google Calendar API JSON format.

    Returns:
        dict: The created event resource from Google Calendar.
    """
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
        raise HTTPException(status_code=500, detail=f"Unexpected error in create_google_calendar_event: {str(e)}")

async def update_google_calendar_event(
    access_token: str,
    calendar_id: str,
    event_id: str,
    event_data_json: dict
):
    """
    Update an existing Google Calendar event
    
    Args:
        access_token (str): The Google OAuth access token for the authenticated user.
        calendar_id (str): The Google Calendar ID containing the event.
        event_id (str): The ID of the event to update.
        event_data_json (dict): The updated event data in Google Calendar API JSON format.

    Returns:
        dict: The updated event resource from Google Calendar.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=event_data_json
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in update_google_calendar_event: {str(e)}")

async def find_event_by_strava_id(access_token: str, calendar_id: str, activity_id: int):
    """
    Return the Google event id that has the given Strava activity_id in private extendedProperties.
    
    Args:
        access_token (str): The Google OAuth access token for the authenticated user.
        calendar_id (str): The Google Calendar ID to search in.
        activity_id (int): The Strava activity ID to match in private extended properties.

    Returns:
        str | None: The Google Calendar event ID if found, otherwise None.

    Notes:
        - Used in services/strava.py
    """
    
    params = {
        "maxResults": 1,
        # Expands recurring events into individual instances.
        "singleEvents": True,
        "privateExtendedProperty": f"strava_activity_id={activity_id}"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        response.raise_for_status()
        events = response.json().get("items", [])
        return events[0]["id"] if events else None
