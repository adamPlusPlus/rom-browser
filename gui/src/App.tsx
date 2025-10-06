import React, { useState } from 'react'
import { Navigation, Page } from './components/Navigation'
import { MyLibrary } from './components/MyLibrary'
import { MyrientBrowser } from './components/MyrientBrowser'
import { Settings } from './components/Settings'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('library')

  const renderPage = () => {
    switch (currentPage) {
      case 'library':
        return <MyLibrary />
      case 'browser':
        return <MyrientBrowser />
      case 'settings':
        return <Settings />
      default:
        return <MyLibrary />
    }
  }

  return (
    <div className="app">
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <div className="app-content">
        {renderPage()}
      </div>
    </div>
  )
}

export default App
