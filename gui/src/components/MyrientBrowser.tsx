import React, { useState, useEffect, useCallback } from 'react'
import { invoke } from '@tauri-apps/api/tauri'

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
  is_directory: boolean
  path?: string
  cover_art?: string
  rating?: number
  summary?: string
  genres?: string
  release_date?: string
  is_favorite?: boolean
  is_downloaded?: boolean
}

interface DownloadItem {
  name: string
  url: string
  platform: string
  status: 'pending' | 'downloading' | 'completed' | 'failed'
  progress: number
  error?: string
}

interface Breadcrumb {
  name: string
  path: string
}

interface TreeNode {
  name: string
  path: string
  isDirectory: boolean
  size?: string
  url?: string
  children?: TreeNode[]
  expanded?: boolean
  level: number
}

export const MyrientBrowser: React.FC = () => {
  const [platforms, setPlatforms] = useState<Platform[]>([])
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null)
  const [games, setGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredPlatforms, setFilteredPlatforms] = useState<Platform[]>([])
  const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumb[]>([])
  const [downloadQueue, setDownloadQueue] = useState<DownloadItem[]>([])
  const [showDownloadQueue, setShowDownloadQueue] = useState(false)
  const [treeView, setTreeView] = useState<TreeNode[]>([])
  const [viewMode, setViewMode] = useState<'list' | 'tree'>('list')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(50) // Items per page
  const [totalItems, setTotalItems] = useState(0)
  const [isLoadingPage, setIsLoadingPage] = useState(false)

  // Load platforms on component mount
  useEffect(() => {
    loadPlatforms()
  }, [])

  // Filter platforms based on search query
  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = platforms.filter(platform =>
        platform.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        platform.dataset.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredPlatforms(filtered)
    } else {
      setFilteredPlatforms(platforms)
    }
  }, [searchQuery, platforms])

  const loadPlatforms = async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await invoke<Platform[]>('get_platforms')
      setPlatforms(result)
      setFilteredPlatforms(result)
    } catch (error) {
      console.error('Failed to load platforms:', error)
      setError('Failed to load platforms')
    } finally {
      setLoading(false)
    }
  }

  const convertGamesToTree = (games: Game[], level: number = 0): TreeNode[] => {
    return games.map(game => ({
      name: game.name,
      path: game.path || '',
      isDirectory: game.is_directory,
      size: game.size,
      url: game.url,
      level,
      expanded: false,
      children: []
    }))
  }

  const loadDirectoryIntoTree = async (platformId: string, path: string, parentNode?: TreeNode) => {
    try {
      const result = await invoke<Game[]>('browse_directory', { 
        platformId, 
        path 
      })
      
      const treeNodes = convertGamesToTree(result, (parentNode?.level || 0) + 1)
      
      if (parentNode) {
        parentNode.children = treeNodes
        parentNode.expanded = true
      } else {
        setTreeView(treeNodes)
      }
      
      return treeNodes
    } catch (error) {
      console.error('Failed to load directory into tree:', error)
      return []
    }
  }

  const loadPage = async (platformId: string, path: string = '', page: number = 1) => {
    try {
      setIsLoadingPage(true)
      setError(null)
      
      const result = await invoke<{games: Game[], total: number}>('browse_platform_paginated', { 
        platformId, 
        path,
        page,
        pageSize 
      })
      
      setGames(result.games)
      setTotalItems(result.total)
      setCurrentPage(page)
      
      // Update tree view for current page
      if (viewMode === 'tree') {
        const treeNodes = convertGamesToTree(result.games)
        setTreeView(treeNodes)
      }
    } catch (error) {
      console.error('Failed to load page:', error)
      setError('Failed to load page')
    } finally {
      setIsLoadingPage(false)
    }
  }

  const handlePlatformSelect = async (platform: Platform) => {
    try {
      setLoading(true)
      setSelectedPlatform(platform)
      setError(null)
      setBreadcrumbs([{ name: platform.name, path: '' }])
      setCurrentPage(1)
      
      await loadPage(platform.id, '', 1)
    } catch (error) {
      console.error('Failed to browse platform:', error)
      setError('Failed to load platform directory')
    } finally {
      setLoading(false)
    }
  }

  const handleDirectoryClick = async (game: Game) => {
    if (!game.is_directory || !game.path || !selectedPlatform) {
      return
    }

    try {
      setLoading(true)
      setError(null)
      setCurrentPage(1)
      
      await loadPage(selectedPlatform.id, game.path, 1)
      
      // Update breadcrumbs
      const newBreadcrumb = { name: game.name, path: game.path }
      setBreadcrumbs(prev => [...prev, newBreadcrumb])
    } catch (error) {
      console.error('Failed to browse directory:', error)
      setError('Failed to load directory')
    } finally {
      setLoading(false)
    }
  }

  const handleBreadcrumbClick = async (index: number) => {
    if (index === 0) {
      // Go back to platform root
      if (selectedPlatform) {
        await handlePlatformSelect(selectedPlatform)
        setBreadcrumbs([{ name: selectedPlatform.name, path: '' }])
      }
    } else {
      // Navigate to specific breadcrumb level
      const path = breadcrumbs.slice(1, index + 1).map(b => b.path).join('')
      
      try {
        setLoading(true)
        setError(null)
        setCurrentPage(1)
        
        await loadPage(selectedPlatform!.id, path, 1)
        setBreadcrumbs(breadcrumbs.slice(0, index + 1))
      } catch (error) {
        console.error('Failed to navigate to directory:', error)
        setError('Failed to navigate to directory')
      } finally {
        setLoading(false)
      }
    }
  }

  const handlePageChange = async (newPage: number) => {
    if (!selectedPlatform || isLoadingPage) return
    
    const currentPath = breadcrumbs.length > 1 
      ? breadcrumbs.slice(1).map(b => b.path).join('')
      : ''
    
    await loadPage(selectedPlatform.id, currentPath, newPage)
  }

  const getPaginationInfo = () => {
    const startItem = (currentPage - 1) * pageSize + 1
    const endItem = Math.min(currentPage * pageSize, totalItems)
    const totalPages = Math.ceil(totalItems / pageSize)
    
    return { startItem, endItem, totalPages }
  }

  const handleTreeNodeClick = async (node: TreeNode) => {
    if (!selectedPlatform) return

    if (node.isDirectory) {
      if (!node.expanded && (!node.children || node.children.length === 0)) {
        // Load children for this directory
        await loadDirectoryIntoTree(selectedPlatform.id, node.path, node)
      } else {
        // Toggle expansion
        node.expanded = !node.expanded
        setTreeView([...treeView])
      }
    } else if (node.url) {
      // Download the file
      await handleDownloadFromNode(node)
    }
  }

  const handleDownloadFromNode = async (node: TreeNode) => {
    if (!node.url) return

    const downloadItem: DownloadItem = {
      name: node.name,
      url: node.url,
      platform: selectedPlatform?.name || '',
      status: 'pending',
      progress: 0
    }

    setDownloadQueue(prev => [...prev, downloadItem])
    setShowDownloadQueue(true)

    try {
      setDownloadQueue(prev => 
        prev.map(item => 
          item.name === node.name ? { ...item, status: 'downloading' as const } : item
        )
      )

      const result = await invoke<string>('download_game', { 
        gameName: node.name, 
        url: node.url 
      })

      setDownloadQueue(prev => 
        prev.map(item => 
          item.name === node.name ? { ...item, status: 'completed' as const, progress: 100 } : item
        )
      )
    } catch (error) {
      console.error('Download failed:', error)
      setDownloadQueue(prev => 
        prev.map(item => 
          item.name === node.name ? { 
            ...item, 
            status: 'failed' as const, 
            error: error instanceof Error ? error.message : 'Download failed' 
          } : item
        )
      )
    }
  }

  const handleDownload = async (game: Game) => {
    if (!game.url) return

    const downloadItem: DownloadItem = {
      name: game.name,
      url: game.url,
      platform: game.platform,
      status: 'pending',
      progress: 0
    }

    setDownloadQueue(prev => [...prev, downloadItem])
    setShowDownloadQueue(true)

    try {
      // Update status to downloading
      setDownloadQueue(prev => 
        prev.map(item => 
          item.name === game.name ? { ...item, status: 'downloading' as const } : item
        )
      )

      const result = await invoke<string>('download_game', { 
        gameName: game.name, 
        url: game.url 
      })

      // Update status to completed
      setDownloadQueue(prev => 
        prev.map(item => 
          item.name === game.name ? { ...item, status: 'completed' as const, progress: 100 } : item
        )
      )
    } catch (error) {
      console.error('Download failed:', error)
      setDownloadQueue(prev => 
        prev.map(item => 
          item.name === game.name ? { 
            ...item, 
            status: 'failed' as const, 
            error: error instanceof Error ? error.message : 'Download failed' 
          } : item
        )
      )
    }
  }

  const handleBatchDownload = async (games: Game[]) => {
    const filesToDownload = games.filter(game => !game.is_directory && game.url)
    
    for (const game of filesToDownload) {
      await handleDownload(game)
      // Add small delay between downloads
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }

  const clearDownloadQueue = () => {
    setDownloadQueue([])
  }

  const removeFromQueue = (name: string) => {
    setDownloadQueue(prev => prev.filter(item => item.name !== name))
  }

  const formatFileSize = (size?: string) => {
    if (!size) return ''
    const bytes = parseInt(size)
    if (isNaN(bytes)) return size
    
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let unitIndex = 0
    let sizeValue = bytes
    
    while (sizeValue >= 1024 && unitIndex < units.length - 1) {
      sizeValue /= 1024
      unitIndex++
    }
    
    return `${sizeValue.toFixed(1)} ${units[unitIndex]}`
  }

  const getStatusColor = (status: DownloadItem['status']) => {
    switch (status) {
      case 'pending': return '#ebcb8b'
      case 'downloading': return '#5e81ac'
      case 'completed': return '#a3be8c'
      case 'failed': return '#bf616a'
      default: return '#88c0d0'
    }
  }

  const renderTreeNode = (node: TreeNode, index: number) => {
    const indent = node.level * 20
    const hasChildren = node.isDirectory && node.children && node.children.length > 0
    
    return (
      <div key={index}>
        <div
          style={{
            padding: '8px 16px',
            paddingLeft: `${16 + indent}px`,
            cursor: 'pointer',
            backgroundColor: index % 2 === 0 ? '#3b4252' : '#434c5e',
            borderBottom: '1px solid #4c566a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            transition: 'background-color 0.2s ease'
          }}
          onClick={() => handleTreeNodeClick(node)}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#4c566a'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = index % 2 === 0 ? '#3b4252' : '#434c5e'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
            {node.isDirectory && (
              <span style={{ fontSize: '12px', color: '#88c0d0', minWidth: '12px' }}>
                {node.expanded ? '▼' : '▶'}
              </span>
            )}
            {!node.isDirectory && (
              <span style={{ fontSize: '12px', color: '#88c0d0', minWidth: '12px' }}>•</span>
            )}
            
            <span style={{ fontSize: '16px', marginRight: '8px' }}>
              {node.isDirectory ? '📁' : '📄'}
            </span>
            
            <div style={{ flex: 1 }}>
              <div style={{ 
                fontWeight: '500',
                color: '#ffffff',
                marginBottom: '2px'
              }}>
                {node.name}
              </div>
              {node.size && (
                <div style={{ 
                  fontSize: '12px', 
                  color: '#88c0d0' 
                }}>
                  {formatFileSize(node.size)}
                </div>
              )}
            </div>
          </div>
          
          {!node.isDirectory && node.url && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDownloadFromNode(node)
              }}
              style={{
                backgroundColor: '#a3be8c',
                color: '#2e3440',
                border: 'none',
                padding: '4px 8px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px',
                fontWeight: '500'
              }}
            >
              Download
            </button>
          )}
        </div>
        
        {node.expanded && node.children && node.children.map((child, childIndex) => 
          renderTreeNode(child, `${index}-${childIndex}`)
        )}
      </div>
    )
  }

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#2e3440', 
      color: '#ffffff', 
      minHeight: '100vh',
      fontFamily: 'Segoe UI, sans-serif'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ 
          color: '#5e81ac', 
          fontSize: '24px', 
          fontWeight: 'bold',
          margin: 0 
        }}>
          Myrient Browser & Downloader
        </h1>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={() => setShowDownloadQueue(!showDownloadQueue)}
            style={{
              backgroundColor: downloadQueue.length > 0 ? '#5e81ac' : '#4c566a',
              color: '#ffffff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Download Queue ({downloadQueue.length})
          </button>
          
          <button
            onClick={loadPlatforms}
            style={{
              backgroundColor: '#4c566a',
              color: '#ffffff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: '#bf616a', 
          color: '#ffffff', 
          padding: '12px', 
          marginBottom: '20px',
          borderRadius: '4px',
          border: '1px solid #bf616a'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {(loading || isLoadingPage) && (
        <div style={{ 
          padding: '40px', 
          textAlign: 'center',
          color: '#88c0d0'
        }}>
          <div style={{ fontSize: '18px' }}>
            {loading ? 'Loading...' : 'Loading page...'}
          </div>
        </div>
      )}

      {!selectedPlatform ? (
        <div>
          <div style={{ marginBottom: '20px' }}>
            <input
              type="text"
              placeholder="Search platforms..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px',
                backgroundColor: '#3b4252',
                color: '#ffffff',
                border: '1px solid #4c566a',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </div>

          <h2 style={{ color: '#e5e9f0', marginBottom: '20px' }}>Select a Platform</h2>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', 
            gap: '15px' 
          }}>
            {filteredPlatforms.map((platform) => (
              <div
                key={platform.id}
                style={{
                  backgroundColor: '#3b4252',
                  border: '1px solid #4c566a',
                  padding: '20px',
                  cursor: 'pointer',
                  borderRadius: '8px',
                  transition: 'all 0.2s ease',
                  ':hover': {
                    backgroundColor: '#4c566a',
                    borderColor: '#5e81ac'
                  }
                }}
                onClick={() => handlePlatformSelect(platform)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#4c566a'
                  e.currentTarget.style.borderColor = '#5e81ac'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#3b4252'
                  e.currentTarget.style.borderColor = '#4c566a'
                }}
              >
                <div style={{ 
                  fontWeight: 'bold', 
                  fontSize: '16px',
                  color: '#ffffff',
                  marginBottom: '8px'
                }}>
                  {platform.name}
                </div>
                <div style={{ 
                  fontSize: '14px', 
                  color: '#88c0d0',
                  textTransform: 'capitalize'
                }}>
                  {platform.dataset}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div>
          {/* Breadcrumb Navigation */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {breadcrumbs.map((breadcrumb, index) => (
                <React.Fragment key={index}>
                  <button
                    onClick={() => handleBreadcrumbClick(index)}
                    style={{
                      backgroundColor: 'transparent',
                      color: index === breadcrumbs.length - 1 ? '#ffffff' : '#5e81ac',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '14px',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontWeight: index === breadcrumbs.length - 1 ? 'bold' : 'normal'
                    }}
                  >
                    {breadcrumb.name}
                  </button>
                  {index < breadcrumbs.length - 1 && (
                    <span style={{ color: '#4c566a' }}>/</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Search within platform and view mode toggle */}
          <div style={{ marginBottom: '20px', display: 'flex', gap: '15px', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Search files and folders..."
              style={{
                flex: 1,
                maxWidth: '400px',
                padding: '10px',
                backgroundColor: '#3b4252',
                color: '#ffffff',
                border: '1px solid #4c566a',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
            
            <div style={{ display: 'flex', gap: '5px' }}>
              <button
                onClick={() => setViewMode('list')}
                style={{
                  backgroundColor: viewMode === 'list' ? '#5e81ac' : '#4c566a',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: '500'
                }}
              >
                📋 List
              </button>
              <button
                onClick={() => setViewMode('tree')}
                style={{
                  backgroundColor: viewMode === 'tree' ? '#5e81ac' : '#4c566a',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: '500'
                }}
              >
                🌳 Tree
              </button>
            </div>
          </div>

          {/* Pagination Info */}
          {totalItems > pageSize && (
            <div style={{ 
              marginBottom: '15px', 
              padding: '10px 15px',
              backgroundColor: '#3b4252',
              border: '1px solid #4c566a',
              borderRadius: '6px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ color: '#88c0d0', fontSize: '14px' }}>
                {(() => {
                  const { startItem, endItem, totalPages } = getPaginationInfo()
                  return `Showing ${startItem}-${endItem} of ${totalItems} items (Page ${currentPage} of ${totalPages})`
                })()}
              </div>
              
              <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1 || isLoadingPage}
                  style={{
                    backgroundColor: currentPage <= 1 ? '#4c566a' : '#5e81ac',
                    color: '#ffffff',
                    border: 'none',
                    padding: '6px 10px',
                    borderRadius: '4px',
                    cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
                    fontSize: '12px',
                    opacity: currentPage <= 1 ? 0.5 : 1
                  }}
                >
                  ← Previous
                </button>
                
                <span style={{ color: '#e5e9f0', fontSize: '12px', padding: '0 10px' }}>
                  {currentPage} / {getPaginationInfo().totalPages}
                </span>
                
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= getPaginationInfo().totalPages || isLoadingPage}
                  style={{
                    backgroundColor: currentPage >= getPaginationInfo().totalPages ? '#4c566a' : '#5e81ac',
                    color: '#ffffff',
                    border: 'none',
                    padding: '6px 10px',
                    borderRadius: '4px',
                    cursor: currentPage >= getPaginationInfo().totalPages ? 'not-allowed' : 'pointer',
                    fontSize: '12px',
                    opacity: currentPage >= getPaginationInfo().totalPages ? 0.5 : 1
                  }}
                >
                  Next →
                </button>
              </div>
            </div>
          )}

          {/* File/Folder List or Tree View */}
          <div style={{ 
            backgroundColor: '#3b4252', 
            border: '1px solid #4c566a', 
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            {viewMode === 'list' ? (
              games.map((game, index) => (
                <div
                  key={index}
                  style={{
                    padding: '12px 16px',
                    borderBottom: index < games.length - 1 ? '1px solid #4c566a' : 'none',
                    cursor: game.is_directory ? 'pointer' : 'default',
                    backgroundColor: index % 2 === 0 ? '#3b4252' : '#434c5e',
                    transition: 'background-color 0.2s ease'
                  }}
                  onClick={() => {
                    if (game.is_directory) {
                      handleDirectoryClick(game)
                    }
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#4c566a'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = index % 2 === 0 ? '#3b4252' : '#434c5e'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                      <span style={{ fontSize: '18px' }}>
                        {game.is_directory ? '📁' : '📄'}
                      </span>
                      <div style={{ flex: 1 }}>
                        <div style={{ 
                          fontWeight: '500',
                          color: '#ffffff',
                          marginBottom: '2px'
                        }}>
                          {game.name}
                        </div>
                        {game.size && (
                          <div style={{ 
                            fontSize: '12px', 
                            color: '#88c0d0' 
                          }}>
                            {formatFileSize(game.size)}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {!game.is_directory && game.url && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDownload(game)
                        }}
                        style={{
                          backgroundColor: '#a3be8c',
                          color: '#2e3440',
                          border: 'none',
                          padding: '6px 12px',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}
                      >
                        Download
                      </button>
                    )}
                  </div>
                </div>
              ))
            ) : (
              treeView.map((node, index) => renderTreeNode(node, index))
            )}
          </div>
        </div>
      )}

      {/* Download Queue Modal */}
      {showDownloadQueue && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: '#2e3440',
            border: '1px solid #4c566a',
            borderRadius: '8px',
            padding: '20px',
            maxWidth: '600px',
            width: '90%',
            maxHeight: '80%',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ color: '#5e81ac', margin: 0 }}>Download Queue</h3>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={clearDownloadQueue}
                  style={{
                    backgroundColor: '#bf616a',
                    color: '#ffffff',
                    border: 'none',
                    padding: '6px 12px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Clear All
                </button>
                <button
                  onClick={() => setShowDownloadQueue(false)}
                  style={{
                    backgroundColor: '#4c566a',
                    color: '#ffffff',
                    border: 'none',
                    padding: '6px 12px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Close
                </button>
              </div>
            </div>

            {downloadQueue.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#88c0d0', padding: '40px' }}>
                No downloads in queue
              </div>
            ) : (
              <div>
                {downloadQueue.map((item, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '12px',
                      border: '1px solid #4c566a',
                      borderRadius: '4px',
                      marginBottom: '10px',
                      backgroundColor: '#3b4252'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: '500', color: '#ffffff', marginBottom: '4px' }}>
                          {item.name}
                        </div>
                        <div style={{ fontSize: '12px', color: '#88c0d0' }}>
                          {item.platform}
                        </div>
                        {item.error && (
                          <div style={{ fontSize: '12px', color: '#bf616a', marginTop: '4px' }}>
                            Error: {item.error}
                          </div>
                        )}
                      </div>
                      
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{
                          width: '60px',
                          height: '4px',
                          backgroundColor: '#4c566a',
                          borderRadius: '2px',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${item.progress}%`,
                            height: '100%',
                            backgroundColor: getStatusColor(item.status),
                            transition: 'width 0.3s ease'
                          }} />
                        </div>
                        
                        <span style={{
                          fontSize: '12px',
                          color: getStatusColor(item.status),
                          fontWeight: '500',
                          minWidth: '80px',
                          textAlign: 'right'
                        }}>
                          {item.status}
                        </span>
                        
                        {item.status === 'completed' || item.status === 'failed' ? (
                          <button
                            onClick={() => removeFromQueue(item.name)}
                            style={{
                              backgroundColor: 'transparent',
                              color: '#bf616a',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '16px',
                              padding: '4px'
                            }}
                          >
                            ×
                          </button>
                        ) : null}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}