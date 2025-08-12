import { useState, useEffect } from 'react'
import { loadAccessToken, validateAccessToken} from './lib/auth';
import { checkStravaConnected } from './lib/strava';
import GoogleButton from './components/GoogleButton/GoogleButton';
import StravaButton from './components/StravaButton/StravaButton';
import './App.css'

function App() {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isStravaConnected, setIsStravaConnected] = useState<boolean>(false);

  // Attempt to load access token from cookie and if no cookie is found, 
  // try to validate the token from localStorage or refresh it
  useEffect(() => {
    const loaded = loadAccessToken(setAccessToken);
    if(!loaded) {
      validateAccessToken(setAccessToken);
    }
  }, []);

  // Whenever accessToken is updated (after login or refresh), check if Strava is connected
  useEffect(() => {
    if(accessToken) {
      checkStravaConnected(accessToken, setAccessToken, setIsStravaConnected);
    }
  }, [accessToken]);

  return (
    <div className="main">
      <img className="app-logo" src="/ActivitySync.png"/>
      <h1>Activity Sync</h1>
      <span>Automacially sync your Strava activities to Google Calendar!</span>
      <div className="services">
          <GoogleButton 
            accessToken={accessToken}
            setAccessToken={setAccessToken}
            setIsStravaConnected={setIsStravaConnected}
          />

          <StravaButton
            accessToken={accessToken}
            isStravaConnected={isStravaConnected}
            setAccessToken={setAccessToken}
            setIsStravaConnected={setIsStravaConnected}
          />
      </div>
    </div>
  )
}

export default App;
