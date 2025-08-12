import { connectStrava, disconnectStrava } from '../../lib/strava';
import './StravaButton.css'

interface StravaButtonProps {
    accessToken: string | null;
    isStravaConnected: boolean;
    setAccessToken: (token: string | null) => void;
    setIsStravaConnected: (isConnected: boolean) => void;
}

export default function StravaButton ({
    accessToken, isStravaConnected, setAccessToken, setIsStravaConnected
} : StravaButtonProps) {
    return (
        <div className="strava">
            <button className='strava-btn' 
                disabled={accessToken === null || isStravaConnected === true}
                onClick={() => { connectStrava(accessToken); }}
            >
                Connect Strava
            </button>

            {isStravaConnected && 
            <button
              onClick={() => {
                disconnectStrava(accessToken, setAccessToken, setIsStravaConnected);
              }}
            >
              Disconnect
            </button>
          }
        </div>
    );
};