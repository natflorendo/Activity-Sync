import { tryRefreshToken } from "./auth";
import axios from "axios";

/**
 * Initiates the OAuth login flow for Strava by requesting a redirect URL from the backend.
 * Then navigates the user to Strava's login screen.
 * 
 * @param accessToken - The Google login access token used for authorization
 */
export const connectStrava = async (accessToken: string | null) => {
    if (!accessToken) {
        console.error("No access token provided");
        return;
    }
  
    try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/strava/login`, {
            headers: {
                Authorization: `Bearer ${accessToken}`
            },
        });

        // Redirect user to Strava Oauth
        window.location.href = res.data.url;
    } catch (err: any) {
        console.error("Failed to connect to Strava:", err.response?.data);
    }
}

/**
 * Checks if the current user has a connected Strava account.
 * 
 * @param accessToken - The Google login access token
 * @param setIsStravaConnected - A state setter to update the frontend connection status
 */
export const checkStravaConnected = async (
    accessToken: string | null,
    setIsStravaConnected: (connected: boolean) => void
) => {
    if (!accessToken) {
        console.error("No access token provided");
        return;
    }

    try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/strava/status`, {
            headers: {
                Authorization: `Bearer ${accessToken}`
            },
        });
        setIsStravaConnected(res.data.connected);
    } catch(err: any) {
        console.error("Failed to check Strava status:", err.response?.data);
        setIsStravaConnected(false);
    }
}

/**
 * Sends a POST request to the backend to disconnect the user's Strava account.
 * 
 * @param accessToken - The user's current Google access token (may be stale)
 */
const tryDisconnect = async (
    accessToken: string | null, 
    setAccessToken: (token: string | null ) => void
) => {
    tryRefreshToken(setAccessToken);
    return axios.post(`${import.meta.env.VITE_API_URL}/strava/disconnect`, 
        {}, 
        {
        withCredentials: true,
        headers: {
            Authorization: `Bearer ${accessToken}`,
        }
    });
}

/**
 * Disconnects the user's Strava account on the backend and updates frontend state.
 * 
 * @param accessToken - The user's Google access token
 * @param setIsStravaConnected - A state setter to update the frontend connection status
 */
export const disconnectStrava = async (
    accessToken: string | null,
    setAccessToken: (token: string | null ) => void,
    setIsStravaConnected: (connected: boolean) => void
) => {
    try {
        await tryDisconnect(accessToken, setAccessToken);
        setIsStravaConnected(false);
    } catch (err: any) {
        if(err.response?.status === 401) {
            console.warn("Access token expired, attempting to refresh...");
            
            try {
                const res = await axios.post(`${import.meta.env.VITE_API_URL}/auth/refresh`, {}, {
                    withCredentials: true,
                });
            
                await tryDisconnect(res.data.access_token, setAccessToken);
                setIsStravaConnected(false);
            } catch (refreshErr: any) {
                console.error("Token refresh failed:", refreshErr.response?.data);
            }
        }

        console.warn("Strava logout failed:", err.response?.data);
    }
}