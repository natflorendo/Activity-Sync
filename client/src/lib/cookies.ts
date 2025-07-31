/**
 * Retrieves the value of a specific cookie by name.
 * 
 * @param name - The name of the cookie to retrieve
 * @returns The decoded value of the cookie, or null if not found
 */
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