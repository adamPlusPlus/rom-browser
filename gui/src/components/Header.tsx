import React from 'react'
import { Search } from 'lucide-react'

interface HeaderProps {
  onSearch?: (query: string) => void
}

export const Header: React.FC<HeaderProps> = ({ onSearch }) => {
  const [searchQuery, setSearchQuery] = React.useState('')

  const handleSearch = () => {
    if (onSearch) {
      onSearch(searchQuery)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <header className="header">
      <div className="header-content">
        <h1>
          <i className="fas fa-gamepad"></i>
          ROM Browser
        </h1>
        <div className="search-container">
          <input
            type="text"
            placeholder="Search games..."
            className="search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button className="search-btn" onClick={handleSearch}>
            <Search size={16} />
          </button>
        </div>
      </div>
    </header>
  )
}
