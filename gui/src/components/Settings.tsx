import React, { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'
import { Settings as SettingsIcon, FolderOpen, Database, Download, RefreshCw, Save } from 'lucide-react'

interface SettingsData {
  romDirectories: string[]
  downloadDirectory: string
  metadataApiKey: string
  autoScan: boolean
  scanInterval: number
  maxConcurrentDownloads: number
}

interface SettingsProps {
  // Props for settings-specific functionality
}

export const Settings: React.FC<SettingsProps> = () => {
  const [settings, setSettings] = useState<SettingsData>({
    romDirectories: [],
    downloadDirectory: '',
    metadataApiKey: '',
    autoScan: true,
    scanInterval: 30,
    maxConcurrentDownloads: 3
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setLoading(true)
      // This will load settings from your config files
      // For now, use default values
      console.log('Loading settings...')
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveSettings = async () => {
    try {
      setSaving(true)
      // This will save settings to your config files
      console.log('Saving settings:', settings)
      
      // Simulate save delay
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setSaving(false)
    }
  }

  const startScanning = async () => {
    try {
      setScanning(true)
      // This will trigger your Python scanning scripts
      console.log('Starting ROM directory scan...')
      
      // Simulate scan delay
      await new Promise(resolve => setTimeout(resolve, 2000))
    } catch (error) {
      console.error('Failed to start scanning:', error)
    } finally {
      setScanning(false)
    }
  }

  const addRomDirectory = () => {
    setSettings(prev => ({
      ...prev,
      romDirectories: [...prev.romDirectories, '']
    }))
  }

  const updateRomDirectory = (index: number, value: string) => {
    setSettings(prev => ({
      ...prev,
      romDirectories: prev.romDirectories.map((dir, i) => i === index ? value : dir)
    }))
  }

  const removeRomDirectory = (index: number) => {
    setSettings(prev => ({
      ...prev,
      romDirectories: prev.romDirectories.filter((_, i) => i !== index)
    }))
  }

  return (
    <div className="page-content">
      <div className="page-header">
        <h2>
          <SettingsIcon size={24} />
          Settings
        </h2>
        <p>Configure ROM directories, downloads, and scanning options</p>
      </div>

      <div className="settings-container">
        <div className="settings-section">
          <div className="section-header">
            <h3>
              <FolderOpen size={20} />
              ROM Directories
            </h3>
            <p>Configure where your ROM files are stored</p>
          </div>

          <div className="settings-group">
            <label className="setting-label">ROM Directories</label>
            <div className="directory-list">
              {settings.romDirectories.map((directory, index) => (
                <div key={index} className="directory-item">
                  <input
                    type="text"
                    value={directory}
                    onChange={(e) => updateRomDirectory(index, e.target.value)}
                    placeholder="Enter ROM directory path..."
                    className="directory-input"
                  />
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => removeRomDirectory(index)}
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button className="btn btn-secondary" onClick={addRomDirectory}>
                Add Directory
              </button>
            </div>
          </div>

          <div className="settings-group">
            <label className="setting-label">Download Directory</label>
            <div className="input-group">
              <input
                type="text"
                value={settings.downloadDirectory}
                onChange={(e) => setSettings(prev => ({ ...prev, downloadDirectory: e.target.value }))}
                placeholder="Enter download directory path..."
                className="setting-input"
              />
              <button className="btn btn-secondary">
                <FolderOpen size={16} />
                Browse
              </button>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <div className="section-header">
            <h3>
              <Database size={20} />
              Metadata & APIs
            </h3>
            <p>Configure metadata sources and API keys</p>
          </div>

          <div className="settings-group">
            <label className="setting-label">IGDB API Key</label>
            <input
              type="password"
              value={settings.metadataApiKey}
              onChange={(e) => setSettings(prev => ({ ...prev, metadataApiKey: e.target.value }))}
              placeholder="Enter your IGDB API key..."
              className="setting-input"
            />
            <p className="setting-help">
              Get your free API key from <a href="https://api.igdb.com/" target="_blank">IGDB</a>
            </p>
          </div>
        </div>

        <div className="settings-section">
          <div className="section-header">
            <h3>
              <RefreshCw size={20} />
              Scanning & Downloads
            </h3>
            <p>Configure automatic scanning and download behavior</p>
          </div>

          <div className="settings-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={settings.autoScan}
                onChange={(e) => setSettings(prev => ({ ...prev, autoScan: e.target.checked }))}
              />
              <span>Enable automatic ROM directory scanning</span>
            </label>
          </div>

          <div className="settings-group">
            <label className="setting-label">Scan Interval (minutes)</label>
            <input
              type="number"
              value={settings.scanInterval}
              onChange={(e) => setSettings(prev => ({ ...prev, scanInterval: parseInt(e.target.value) || 30 }))}
              min="1"
              max="1440"
              className="setting-input"
            />
          </div>

          <div className="settings-group">
            <label className="setting-label">Max Concurrent Downloads</label>
            <input
              type="number"
              value={settings.maxConcurrentDownloads}
              onChange={(e) => setSettings(prev => ({ ...prev, maxConcurrentDownloads: parseInt(e.target.value) || 3 }))}
              min="1"
              max="10"
              className="setting-input"
            />
          </div>
        </div>

        <div className="settings-actions">
          <button
            className="btn btn-primary"
            onClick={startScanning}
            disabled={scanning}
          >
            <RefreshCw size={16} />
            {scanning ? 'Scanning...' : 'Start ROM Scan'}
          </button>

          <button
            className="btn btn-success"
            onClick={saveSettings}
            disabled={saving}
          >
            <Save size={16} />
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
