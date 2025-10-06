import React, { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'
import { Search, Download, Filter, RefreshCw, Globe } from 'lucide-react'

interface Platform {
  id: string
  name: string
  dataset: string
}

interface Game {
  name: string
  platform: string
  size?: string
  url?: string
}

interface MyrientBrowserProps {
  // Props for browser-specific functionality
}

export const MyrientBrowser: React.FC<MyrientBrowserProps> = () => {
  const [platforms, setPlatforms] = useState<Platform[]>([])
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null)
  const [games, setGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [downloadingGames, setDownloadingGames] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadPlatforms()
  }, [])

  const loadPlatforms = async () => {
    try {
      setLoading(true)
      const result = await invoke<Platform[]>('get_platforms')
      setPlatforms(result)
    } catch (error) {
      console.error('Failed to load platforms:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePlatformSelect = async (platform: Platform) => {
    try {
      setLoading(true)
      setSelectedPlatform(platform)
      const result = await invoke<Game[]>('browse_platform', { platformId: platform.id })
      setGames(result)
    } catch (error) {
      console.error('Failed to browse platform:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleGameDownload = async (game: Game) => {
    if (!game.url) return
    
    try {
      setDownloadingGames(prev => new Set(prev).add(game.name))
      const result = await invoke<string>('download_game', { 
        gameName: game.name, 
        url: game.url 
      })
      console.log(result)
      
      // Remove from downloading set after a delay
      setTimeout(() => {
        setDownloadingGames(prev => {
          const newSet = new Set(prev)
          newSet.delete(game.name)
          return newSet
        })
      }, 2000)
    } catch (error) {
      console.error('Failed to download game:', error)
      setDownloadingGames(prev => {
        const newSet = new Set(prev)
        newSet.delete(game.name)
        return newSet
      })
    }
  }

  const filteredGames = games.filter(game =>
    game.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="page-content">
      <div className="page-header">
        <h2>
          <Globe size={24} />
          Myrient Browser
        </h2>
        <p>Browse and download ROMs from Myrient.erista.me</p>
      </div>

      <div className="browser-layout">
        <div className="platform-sidebar">
          <div className="sidebar-header">
            <h3>
              <i className="fas fa-list"></i>
              Platforms
            </h3>
            <button className="btn btn-sm" onClick={loadPlatforms}>
              <RefreshCw size={16} />
            </button>
          </div>
          
          <div className="platforms-list">
            {loading ? (
              <div className="loading">
                <div className="loading-spinner">
                  <div className="spinner"></div>
                  <p>Loading platforms...</p>
                </div>
              </div>
            ) : (
              platforms.map((platform) => (
                <div
                  key={platform.id}
                  className={`platform-item ${
                    selectedPlatform?.id === platform.id ? 'selected' : ''
                  }`}
                  onClick={() => handlePlatformSelect(platform)}
                >
                  <div className="platform-name">{platform.name}</div>
                  <div className="platform-dataset">{platform.dataset}</div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="browser-main">
          <div className="browser-controls">
            <div className="search-section">
              <div className="search-container">
                <Search size={20} />
                <input
                  type="text"
                  placeholder="Search games..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
              </div>
            </div>

            {selectedPlatform && (
              <div className="platform-info">
                <h3>
                  <i className="fas fa-gamepad"></i>
                  {selectedPlatform.name} Games
                </h3>
                <p className="platform-details">
                  Dataset: {selectedPlatform.dataset} • {filteredGames.length} games found
                </p>
              </div>
            )}
          </div>

          {!selectedPlatform ? (
            <div className="welcome-message">
              <Globe size={64} />
              <h3>Welcome to Myrient Browser</h3>
              <p>Select a platform from the sidebar to start browsing games</p>
            </div>
          ) : loading ? (
            <div className="loading">
              <div className="loading-spinner">
                <div className="spinner"></div>
                <p>Loading games...</p>
              </div>
            </div>
          ) : (
            <div className="games-grid">
              {filteredGames.map((game, index) => (
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
                    className={`download-btn ${
                      downloadingGames.has(game.name) ? 'downloading' : ''
                    }`}
                    onClick={() => handleGameDownload(game)}
                    disabled={!game.url || downloadingGames.has(game.name)}
                  >
                    <Download size={16} />
                    {downloadingGames.has(game.name) ? 'Downloading...' : 'Download'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {selectedPlatform && filteredGames.length === 0 && !loading && (
            <div className="empty-state">
              <i className="fas fa-search fa-3x"></i>
              <h3>No games found</h3>
              <p>Try adjusting your search query</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
