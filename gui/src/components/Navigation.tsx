import React from 'react'
import { Library, Globe, Settings } from 'lucide-react'

export type Page = 'library' | 'browser' | 'settings'

interface NavigationProps {
  currentPage: Page
  onPageChange: (page: Page) => void
}

export const Navigation: React.FC<NavigationProps> = ({ currentPage, onPageChange }) => {
  const pages = [
    { id: 'library' as Page, label: 'My Library', icon: Library },
    { id: 'browser' as Page, label: 'Myrient Browser', icon: Globe },
    { id: 'settings' as Page, label: 'Settings', icon: Settings },
  ]

  return (
    <nav className="navigation">
      <div className="nav-content">
        <div className="nav-brand">
          <h1>
            <i className="fas fa-gamepad"></i>
            ROM Browser
          </h1>
        </div>
        <div className="nav-tabs">
          {pages.map((page) => {
            const Icon = page.icon
            return (
              <button
                key={page.id}
                className={`nav-tab ${currentPage === page.id ? 'active' : ''}`}
                onClick={() => onPageChange(page.id)}
              >
                <Icon size={20} />
                <span>{page.label}</span>
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
