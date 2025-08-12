"""
routes/strava_webhook.py

API routes for handling Strava webhook verification and activity events.

Defines HTTP endpoints, parses incoming requests from Strava, 
and delegates processing to service layers.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from models.strava_user import StravaUser
from dependencies import get_db
from services.user import refresh_strava_token
from services.strava import sync_strava_data, update_strava_activity, delete_strava_activity
import os

router = APIRouter()

# NOTE:
# This verification route is currently unused because Strava's GET 
# verification is handled by the Cloudflare Worker. The Worker exists purely to avoid Render's
# 15-minute idle sleep delay, ensuring Strava always gets an instant 200 OK.
# I want to keep this route in case the app ever migrates away from the Worker in the future.
# The strava webhook subscription uses the Worker () as the callback URL
# (instead of https://activitysync-api.onrender.com/strava/webhook)
@router.get("/")
async def verify_webhook(request: Request):
    """
    Strava Subscription Validation Request. Strava calls this once at subscription time.
    This is so that Strava sees that URL exists and that the app is expecting a subscription from Strava
    hub.challenge - Random string the callback address must echo back to verify its existence
    """
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")
    verify_token = request.query_params.get("hub.verify_token")

    if hub_mode == "subscribe" and hub_challenge and verify_token == os.getenv("STRAVA_VERIFY_TOKEN"):
        return {"hub.challenge": hub_challenge}
    
    # Return empty object if not because the response should indicate status code 200.
    # If it returned error it may consider the webhook endpoint unavailable or misconfigured
    # and might have to manually trigger another subscription request 
    return {}

@router.post("/")
async def recieve_strava_event(payload: dict, db: Session = Depends(get_db)):
    if payload.get("object_type") != "activity":
        # Perminent skip
        return {"status": "ignored"}
    
    # For development
    print("🔥🔥🔥", payload)
    
    aspect_type = payload.get("aspect_type")
    athlete_id = payload.get("owner_id")
    activity_id = payload.get("object_id")

    if not aspect_type or athlete_id is None or activity_id is None:
        # Allows fail and retry
        raise HTTPException(status_code=400, detail="Missing required Strava webhook fields")

    strava_user = db.query(StravaUser).filter_by(athlete_id=str(athlete_id)).first()

    if not strava_user:
        return {"status": "no_user"}

    try: 
        user = strava_user.user
        if not user or not user.google_data:
            raise HTTPException(status_code=400, detail="User is not connected to Google Calendar")

        refresh_strava_token(user, db)

        if aspect_type == "create":
            await sync_strava_data(strava_user, db)
        elif aspect_type == "update":
            await update_strava_activity(strava_user, activity_id)
        elif aspect_type == "delete":
            await delete_strava_activity(strava_user, activity_id, db)
        else:
            return {"status": f"ignored - Unhandled aspect_type: {aspect_type}"}
        
        return {"status": "processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed to process activity {activity_id}: {str(e)}")