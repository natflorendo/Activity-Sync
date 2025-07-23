import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import { loadAccessToken, logout, validateAccessToken } from './App'
import './App.css'

function App() {
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    const loaded = loadAccessToken(setAccessToken);
    if(!loaded) {
      validateAccessToken(setAccessToken);
    }
  }, []);

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button 
          className='google-btn'
          disabled={accessToken !== null}
          onClick={() => {
            window.location.href = `${import.meta.env.VITE_API_URL}/google/login`
          }}
        >
          Sign into Google
        </button>
        {accessToken && 
          <>
            <button
              onClick={() => {
                logout();
                setAccessToken(null);
              }}
            >
              Logout
            </button>
            <p style={{ marginTop: '1rem' }}>✅ Logged in!</p>
          </>
          }
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
