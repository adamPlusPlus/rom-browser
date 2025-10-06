import React from 'react'
import { Download, Gamepad2 } from 'lucide-react'

interface Game {
  name: string
  platform: string
  size?: string
  url?: string
}

interface Platform {
  id: string
  name: string
  dataset: string
}

interface GameBrowserProps {
  games: Game[]
  selectedPlatform: Platform | null
  onGameDownload: (game: Game) => void
  loading: boolean
}

export const GameBrowser: React.FC<GameBrowserProps> = ({
  games,
  selectedPlatform,
  onGameDownload,
  loading
}) => {
  if (!selectedPlatform) {
    return (
      <main className="main-content">
        <div className="welcome-message">
          <Gamepad2 size={64} />
          <h2>Welcome to ROM Browser</h2>
          <p>Select a platform from the sidebar to start browsing games</p>
        </div>
      </main>
    )
  }

  return (
    <main className="main-content">
      <div className="content-header">
        <h2>
          <i className="fas fa-gamepad"></i>
          {selectedPlatform.name} Games
        </h2>
        <p className="platform-info">
          Dataset: {selectedPlatform.dataset} • {games.length} games found
        </p>
      </div>

      {loading ? (
        <div className="loading">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading games...</p>
          </div>
        </div>
      ) : (
        <div className="games-grid">
          {games.map((game, index) => (
            <div key={index} className="game-card">
              <div className="game-title">{game.name}</div>
              <div className="game-platform">{game.platform}</div>
              {game.size && (
                <div className="game-size">
                  <i className="fas fa-hdd"></i>
                  {game.size}
                </div>
              )}
              <button
                className="download-btn"
                onClick={() => onGameDownload(game)}
                disabled={!game.url}
              >
                <Download size={16} />
                Download
              </button>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
