import React from 'react'
import { RefreshCw } from 'lucide-react'

interface Platform {
  id: string
  name: string
  dataset: string
}

interface PlatformSidebarProps {
  platforms: Platform[]
  onPlatformSelect: (platform: Platform) => void
  selectedPlatform: Platform | null
  loading: boolean
}

export const PlatformSidebar: React.FC<PlatformSidebarProps> = ({
  platforms,
  onPlatformSelect,
  selectedPlatform,
  loading
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h3>
          <i className="fas fa-list"></i>
          Platforms
        </h3>
        <button className="btn btn-sm">
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
              onClick={() => onPlatformSelect(platform)}
            >
              <div className="platform-name">{platform.name}</div>
              <div className="platform-dataset">{platform.dataset}</div>
            </div>
          ))
        )}
      </div>
    </aside>
  )
}
