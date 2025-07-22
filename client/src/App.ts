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

export const logout = async () => {
    localStorage.removeItem("access_token");

    try {
        // {} is the request body
        await axios.post(`${import.meta.env.VITE_API_URL}/google/auth/logout`, {},{
            withCredentials: true, // sends HttpOnly cookies
        });
    } catch (err){
        console.error("Logout failed", err)
    }
}