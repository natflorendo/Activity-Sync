import axios from "axios";

export const getCookie = (name: string) => {
    // document.cookie returns a string of all cookies available to JavaScript
    // beginning of the string or a space: (^| ) 
    // + the cookie name and =: access_token= 
    // + any characters that are not ; (the cookie value): ([^;]+)
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)') )
    
    // match[0] is the full match (e.g. "access_token=abc123")
    // match[1] is the prefix ("" or " ")
    // match[2] is the cookie value ("abc123")
    return match ? decodeURIComponent(match[2]) : null;
}

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
    } catch {
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
    } catch (err){
        console.error("Logout failed", err)
    }
}