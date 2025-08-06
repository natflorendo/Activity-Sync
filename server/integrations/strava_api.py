"""
integrations/strava.py

Functions for interacting with the Strava API.

Contains direct HTTP calls to an external service and no application business logic.
"""
from fastapi import HTTPException
from models.strava_user import StravaUser
import httpx

async def get_strava_activities(access_token: str, after: int | None = None):
    """
    Retrieve a list of recent Strava activities for the authenticated athlete.
    
    Args:
        access_token (str): The Strava OAuth access token for the athlete.
        after (int | None): Optional UNIX timestamp (in seconds) to only include activities after this time.

    Returns:
        list: JSON response containing activity summaries.
    """
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
        raise HTTPException(status_code=500, detail=f"Unexpected error in get_strava_activities: {str(e)}")

async def get_strava_activity(strava_user: StravaUser, activity_id: int):
    """
    Retrieve full details of a specific Strava activity by its ID.
    
    Args:
        strava_user (StravaUser): The StravaUser object containing OAuth tokens.
        activity_id (int): The ID of the activity to retrieve.

    Returns:
        dict: JSON response containing detailed activity data.
    """
    try:
        # Fetch full activity details
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}",
                headers={"Authorization": f"Bearer {strava_user.access_token}"},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error in get_strava_activity: {str(e)}")