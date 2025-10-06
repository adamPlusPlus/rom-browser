import React, { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'
import { Search, Filter, Grid, List, Download, Heart, Star } from 'lucide-react'

interface Game {
  name: string
  platform: string
  size?: string
  url?: string
  coverArt?: string
  rating?: number
  isFavorite?: boolean
  isDownloaded?: boolean
}

interface MyLibraryProps {
  // Props for library-specific functionality
}

export const MyLibrary: React.FC<MyLibraryProps> = () => {
  const [games, setGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterPlatform, setFilterPlatform] = useState<string>('all')
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)

  useEffect(() => {
    loadLibraryGames()
  }, [])

  const loadLibraryGames = async () => {
    try {
      setLoading(true)
      // This will integrate with your local game database
      // For now, return mock data
      const mockGames: Game[] = [
        {
          name: "Grand Theft Auto: San Andreas",
          platform: "PlayStation 2",
          size: "4.2 GB",
          coverArt: "https://example.com/cover1.jpg",
          rating: 9.5,
          isFavorite: true,
          isDownloaded: true
        },
        {
          name: "Halo: Combat Evolved",
          platform: "Xbox",
          size: "1.8 GB",
          coverArt: "https://example.com/cover2.jpg",
          rating: 9.0,
          isFavorite: false,
          isDownloaded: true
        },
        {
          name: "Super Mario Sunshine",
          platform: "GameCube",
          size: "1.4 GB",
          coverArt: "https://example.com/cover3.jpg",
          rating: 8.8,
          isFavorite: true,
          isDownloaded: false
        }
      ]
      setGames(mockGames)
    } catch (error) {
      console.error('Failed to load library games:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredGames = games.filter(game => {
    const matchesSearch = game.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesPlatform = filterPlatform === 'all' || game.platform === filterPlatform
    const matchesFavorites = !showFavoritesOnly || game.isFavorite
    
    return matchesSearch && matchesPlatform && matchesFavorites
  })

  const toggleFavorite = async (game: Game) => {
    // This will integrate with your favorites system
    console.log('Toggle favorite:', game.name)
  }

  const downloadGame = async (game: Game) => {
    // This will integrate with your download system
    console.log('Download game:', game.name)
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <h2>
          <i className="fas fa-book"></i>
          My Library
        </h2>
        <p>Manage your downloaded games and favorites</p>
      </div>

      <div className="library-controls">
        <div className="search-section">
          <div className="search-container">
            <Search size={20} />
            <input
              type="text"
              placeholder="Search your library..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
        </div>

        <div className="filter-section">
          <div className="filter-group">
            <Filter size={16} />
            <select
              value={filterPlatform}
              onChange={(e) => setFilterPlatform(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Platforms</option>
              <option value="PlayStation 2">PlayStation 2</option>
              <option value="Xbox">Xbox</option>
              <option value="GameCube">GameCube</option>
            </select>
          </div>

          <div className="filter-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={showFavoritesOnly}
                onChange={(e) => setShowFavoritesOnly(e.target.checked)}
              />
              <Heart size={16} />
              Favorites Only
            </label>
          </div>

          <div className="view-controls">
            <button
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
            >
              <Grid size={16} />
            </button>
            <button
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
            >
              <List size={16} />
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading your library...</p>
          </div>
        </div>
      ) : (
        <div className={`games-container ${viewMode}`}>
          {filteredGames.map((game, index) => (
            <div key={index} className={`game-card ${viewMode}`}>
              {game.coverArt && (
                <div className="game-cover">
                  <img src={game.coverArt} alt={game.name} />
                </div>
              )}
              
              <div className="game-info">
                <h3 className="game-title">{game.name}</h3>
                <p className="game-platform">{game.platform}</p>
                {game.size && <p className="game-size">{game.size}</p>}
                
                {game.rating && (
                  <div className="game-rating">
                    <Star size={14} />
                    <span>{game.rating}/10</span>
                  </div>
                )}
              </div>

              <div className="game-actions">
                <button
                  className={`action-btn favorite ${game.isFavorite ? 'active' : ''}`}
                  onClick={() => toggleFavorite(game)}
                >
                  <Heart size={16} />
                </button>
                
                {!game.isDownloaded && (
                  <button
                    className="action-btn download"
                    onClick={() => downloadGame(game)}
                  >
                    <Download size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {filteredGames.length === 0 && !loading && (
        <div className="empty-state">
          <i className="fas fa-gamepad fa-3x"></i>
          <h3>No games found</h3>
          <p>Try adjusting your search or filters</p>
        </div>
      )}
    </div>
  )
}
