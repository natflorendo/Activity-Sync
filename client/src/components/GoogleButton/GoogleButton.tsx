import { logout } from "../../lib/auth";
import './GoogleButton.css';

interface GoogleButtonProps {
    accessToken: string | null;
    setAccessToken: (token: string | null) => void;
    setIsStravaConnected: (isConnected: boolean) => void;
}

export default function GoogleButton({ accessToken, setAccessToken, setIsStravaConnected }: GoogleButtonProps) {
    const handleLogout = () => {
        logout();
        setAccessToken(null);
        setIsStravaConnected(false);
    }
    
    return (
        <div className="google">
            <button className='google-btn' 
                disabled={accessToken !== null}
                onClick={() => {
                window.location.href = `${import.meta.env.VITE_API_URL}/google/login`
                }}
            >
            Sign into Google
            </button>
            
            {accessToken && 
                <button onClick={handleLogout}>Log out</button>
            }
        </div>
    );
};