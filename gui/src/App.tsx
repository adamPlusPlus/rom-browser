import React, { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'
import { GameBrowser } from './components/GameBrowser'
import { PlatformSidebar } from './components/PlatformSidebar'
import { Header } from './components/Header'
import './App.css'

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

function App() {
  const [platforms, setPlatforms] = useState<Platform[]>([])
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null)
  const [games, setGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(false)

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
      const result = await invoke<string>('download_game', { 
        gameName: game.name, 
        url: game.url 
      })
      console.log(result)
    } catch (error) {
      console.error('Failed to download game:', error)
    }
  }

  return (
    <div className="app">
      <Header />
      <div className="app-content">
        <PlatformSidebar 
          platforms={platforms}
          onPlatformSelect={handlePlatformSelect}
          selectedPlatform={selectedPlatform}
          loading={loading}
        />
        <GameBrowser 
          games={games}
          selectedPlatform={selectedPlatform}
          onGameDownload={handleGameDownload}
          loading={loading}
        />
      </div>
    </div>
  )
}

export default App
