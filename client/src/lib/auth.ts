import axios from "axios";
import { getCookie } from "./cookies";

/**
 * Load the access token from a cookie and move it to localStorage.
 * Used when user first logs in
 * 
 * @param setAccessToken - React state setter for access token
 * @returns true if token was loaded from cookie, false otherwise
 */

export const loadAccessToken = (setAccessToken: (token: string | null) => void) => {
    const token = getCookie('access_token');
    if(token) {
        localStorage.setItem('access_token', token);
        setAccessToken(token);
      
        // Delete cookie
        document.cookie = 'access_token=; Max-Age=0; path=/';

        return true;
    }
    return false;
}

/**
 * Validate the current access token stored in localStorage by calling the backend.
 * If it’s invalid or expired, try to refresh it using the refresh token cookie.
 * Used whenever user refreshes screen
 * 
 * @param setAccessToken - React state setter for access token
 */
export const validateAccessToken = async (setAccessToken: (token: string | null ) => void) => {
    const stored = localStorage.getItem('access_token');
    if (!stored) {
        console.warn("No access token in localStorage");
        await tryRefreshToken(setAccessToken);
        return;
    }

    try {
        await axios.get(`${import.meta.env.VITE_API_URL}/auth/validate`, {
            headers: { Authorization: `Bearer ${stored}`},
        });
        setAccessToken(stored);
    } catch (err: any) {
        console.error(err.response?.data);
        if(err.response?.status === 401) {
            await tryRefreshToken(setAccessToken);
            console.log("Refreshed Access Token");
        } else {
            logout();
            setAccessToken(null);
        }
    }
}

/**
 * Attempt to refresh the access token using the HttpOnly refresh token stored in a cookie.
 * If successful, store the new token in localStorage and update state.
 * If it fails (ex: no cookie) then assume user is logged out.
 * 
 * @param setAccessToken - React state setter for access token
 */
export const tryRefreshToken = async (setAccessToken: (token: string | null ) => void) => {
    try {
        const res = await axios.post(
            `${import.meta.env.VITE_API_URL}/auth/refresh`, 
            {}, // no body needed because refresh token is in cookie
            { withCredentials: true} // ensures cookies are sent
        );
        const new_access_token = res.data.access_token;
        localStorage.setItem('access_token', new_access_token);
        setAccessToken(new_access_token);
    } catch (err: any) {
        if (err.response?.status === 401) {
            console.info("No refresh token cookie — user likely not logged in");
        } else {
            console.error("Unexpected error during refresh:", err);
        }
        logout();
        setAccessToken(null);
    }
}

export const logout = async () => {
    localStorage.removeItem("access_token");

    try {
        // {} is the request body
        await axios.post(`${import.meta.env.VITE_API_URL}/auth/logout`, {},{
            withCredentials: true, // sends HttpOnly cookies
        });
    } catch (err: any){
        console.error("Logout failed", err)
    }
}