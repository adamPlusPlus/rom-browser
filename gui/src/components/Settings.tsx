import React, { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'
import { Settings as SettingsIcon, FolderOpen, Database, Download, RefreshCw, Save } from 'lucide-react'

interface SettingsData {
  rom_directories: string[]
  download_directory: string
  metadata_api_key: string
  auto_scan: boolean
  scan_interval: number
  max_concurrent_downloads: number
}

interface SettingsProps {
  // Props for settings-specific functionality
}

export const Settings: React.FC<SettingsProps> = () => {
  const [settings, setSettings] = useState<SettingsData>({
    rom_directories: [],
    download_directory: '',
    metadata_api_key: '',
    auto_scan: true,
    scan_interval: 30,
    max_concurrent_downloads: 3
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
      const result = await invoke<SettingsData>('get_settings')
      setSettings(result)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveSettings = async () => {
    try {
      setSaving(true)
      const result = await invoke<string>('save_settings', { settings })
      console.log(result)
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setSaving(false)
    }
  }

  const startScanning = async () => {
    try {
      setScanning(true)
      const result = await invoke<string>('start_rom_scan')
      console.log(result)
    } catch (error) {
      console.error('Failed to start scanning:', error)
    } finally {
      setScanning(false)
    }
  }

  const addRomDirectory = () => {
    setSettings(prev => ({
      ...prev,
      rom_directories: [...prev.rom_directories, '']
    }))
  }

  const updateRomDirectory = (index: number, value: string) => {
    setSettings(prev => ({
      ...prev,
      rom_directories: prev.rom_directories.map((dir, i) => i === index ? value : dir)
    }))
  }

  const removeRomDirectory = (index: number) => {
    setSettings(prev => ({
      ...prev,
      rom_directories: prev.rom_directories.filter((_, i) => i !== index)
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
              {settings.rom_directories.map((directory, index) => (
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
                value={settings.download_directory}
                onChange={(e) => setSettings(prev => ({ ...prev, download_directory: e.target.value }))}
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
              value={settings.metadata_api_key}
              onChange={(e) => setSettings(prev => ({ ...prev, metadata_api_key: e.target.value }))}
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
                checked={settings.auto_scan}
                onChange={(e) => setSettings(prev => ({ ...prev, auto_scan: e.target.checked }))}
              />
              <span>Enable automatic ROM directory scanning</span>
            </label>
          </div>

          <div className="settings-group">
            <label className="setting-label">Scan Interval (minutes)</label>
            <input
              type="number"
              value={settings.scan_interval}
              onChange={(e) => setSettings(prev => ({ ...prev, scan_interval: parseInt(e.target.value) || 30 }))}
              min="1"
              max="1440"
              className="setting-input"
            />
          </div>

          <div className="settings-group">
            <label className="setting-label">Max Concurrent Downloads</label>
            <input
              type="number"
              value={settings.max_concurrent_downloads}
              onChange={(e) => setSettings(prev => ({ ...prev, max_concurrent_downloads: parseInt(e.target.value) || 3 }))}
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