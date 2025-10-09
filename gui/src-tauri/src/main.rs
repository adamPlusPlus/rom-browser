// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use rom_browser_scripts::{
    GameInfo, PlatformInfo, SettingsData, GameMetadata, DirectoryItem,
    get_platform_mappings,
};
use rusqlite::{Connection, Result as SqlResult};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use std::sync::Mutex;
use tokio::sync::Mutex as TokioMutex;

// Global state for the application
struct AppState {
    rom_browser: TokioMutex<RomBrowserService>,
}

struct RomBrowserService {
    client: reqwest::Client,
    platforms: HashMap<String, String>,
}

impl RomBrowserService {
    fn new() -> Self {
        Self {
            client: reqwest::Client::new(),
            platforms: get_platform_mappings(),
        }
    }

    fn url_encode(&self, text: &str) -> String {
        text.replace(' ', "%20")
            .replace('(', "%28")
            .replace(')', "%29")
            .replace('+', "%2B")
            .replace('&', "%26")
            .replace('\'', "%27")
            .replace(',', "%2C")
    }

    fn url_decode(&self, text: &str) -> String {
        text.replace("%20", " ")
            .replace("%28", "(")
            .replace("%29", ")")
            .replace("%2B", "+")
            .replace("%26", "&")
            .replace("%27", "'")
            .replace("%2C", ",")
    }

    async fn download_index(&self, url: &str) -> Result<String, String> {
        let response = self.client
            .get(url)
            .header("User-Agent", "Mozilla/5.0 (ROM Browser GUI)")
            .send()
            .await
            .map_err(|e| format!("Failed to download index: {}", e))?;

        let content = response.text().await
            .map_err(|e| format!("Failed to read response: {}", e))?;

        Ok(content)
    }

    fn parse_items_from_index(&self, content: &str) -> Result<Vec<DirectoryItem>, String> {
        let mut items = Vec::new();

        // Parse directories
        let dir_pattern = regex::Regex::new(r#"href="([^"]+/)"#)
            .map_err(|e| format!("Failed to create regex: {}", e))?;
        
        for cap in dir_pattern.captures_iter(content) {
            let href = &cap[1];
            if href.contains("?C=") || href == "../" || href.starts_with('/') || href.starts_with("http") {
                continue;
            }

            let clean_href = href.trim_end_matches('/');
            let display_name = self.url_decode(clean_href);

            items.push(DirectoryItem {
                name: display_name,
                href: href.to_string(),
                item_type: "directory".to_string(),
                size: None,
            });
        }

        // Parse files
        let file_pattern = regex::Regex::new(r#"href="([^"]+\.(?:zip|7z))""#)
            .map_err(|e| format!("Failed to create regex: {}", e))?;
        
        for cap in file_pattern.captures_iter(content) {
            let href = &cap[1];
            if href.contains("?C=") || href.starts_with('/') || href.starts_with("http") {
                continue;
            }

            let display_name = self.url_decode(href);

            items.push(DirectoryItem {
                name: display_name,
                href: href.to_string(),
                item_type: "file".to_string(),
                size: None,
            });
        }

        Ok(items)
    }

    async fn get_platforms(&self) -> Result<Vec<PlatformInfo>, String> {
        let files_url = "https://myrient.erista.me/files/";
        let content = self.download_index(files_url).await?;
        let items = self.parse_items_from_index(&content)?;

        let mut platforms = Vec::new();
        for item in items {
            if item.item_type == "directory" {
                let dataset = if item.name.to_lowercase().contains("redump") {
                    "redump"
                } else if item.name.to_lowercase().contains("no-intro") {
                    "no-intro"
                } else {
                    "unknown"
                };

                platforms.push(PlatformInfo {
                    id: self.url_encode(&item.name),
                    name: item.name,
                    dataset: dataset.to_string(),
                });
            }
        }

        Ok(platforms)
    }

    async fn browse_platform(&self, platform_id: &str, path: Option<&str>) -> Result<Vec<GameInfo>, String> {
        // First get the platform list to find the correct URL
        let files_url = "https://myrient.erista.me/files/";
        let content = self.download_index(files_url).await?;
        let items = self.parse_items_from_index(&content)?;

        let mut platform_url = None;
        let mut platform_name = None;

        // Find the platform by ID or name
        for item in items {
            if item.item_type == "directory" {
                let encoded_id = self.url_encode(&item.name);
                if encoded_id == platform_id || item.name == platform_id {
                    platform_name = Some(item.name);
                    platform_url = Some(format!("{}{}", files_url, item.href));
                    break;
                }
            }
        }

        let platform_url = platform_url.ok_or_else(|| format!("Platform not found: {}", platform_id))?;
        let platform_name = platform_name.ok_or_else(|| format!("Platform not found: {}", platform_id))?;

        // Build the target URL
        let target_url = if let Some(path) = path {
            format!("{}{}/", platform_url, path)
        } else {
            platform_url
        };

        // Browse the directory
        let content = self.download_index(&target_url).await?;
        let items = self.parse_items_from_index(&content)?;

        let mut games = Vec::new();
        for item in items {
            games.push(GameInfo {
                name: item.name,
                platform: platform_name.clone(),
                size: item.size,
                url: if item.item_type == "file" {
                    Some(format!("{}{}", target_url, item.href))
                } else {
                    None
                },
                cover_art: None,
                rating: None,
                summary: None,
                genres: None,
                release_date: None,
                is_favorite: None,
                is_downloaded: None,
                is_directory: Some(item.item_type == "directory"),
                path: if item.item_type == "directory" {
                    Some(item.href)
                } else {
                    None
                },
            });
        }

        Ok(games)
    }

    async fn search_platforms(&self, query: &str) -> Result<Vec<PlatformInfo>, String> {
        let mut platforms = Vec::new();

        // Search Redump
        let redump_url = "https://myrient.erista.me/files/Redump/";
        let content = self.download_index(redump_url).await?;
        let items = self.parse_items_from_index(&content)?;

        for item in items {
            if item.item_type == "directory" && item.name.to_lowercase().contains(&query.to_lowercase()) {
                platforms.push(PlatformInfo {
                    id: self.url_encode(&item.name),
                    name: item.name,
                    dataset: "redump".to_string(),
                });
            }
        }

        // Search No-Intro
        let nointro_url = "https://myrient.erista.me/files/No-Intro/";
        let content = self.download_index(nointro_url).await?;
        let items = self.parse_items_from_index(&content)?;

        for item in items {
            if item.item_type == "directory" && item.name.to_lowercase().contains(&query.to_lowercase()) {
                platforms.push(PlatformInfo {
                    id: self.url_encode(&item.name),
                    name: item.name,
                    dataset: "no-intro".to_string(),
                });
            }
        }

        Ok(platforms)
    }
}

#[tauri::command]
async fn get_platforms(state: tauri::State<'_, AppState>) -> Result<Vec<PlatformInfo>, String> {
    let browser = state.rom_browser.lock().await;
    browser.get_platforms().await
}

#[tauri::command]
async fn browse_platform(
    platform_id: String,
    state: tauri::State<'_, AppState>,
) -> Result<Vec<GameInfo>, String> {
    let browser = state.rom_browser.lock().await;
    browser.browse_platform(&platform_id, None).await
}

#[tauri::command]
async fn browse_platform_paginated(
    platform_id: String,
    path: String,
    page: u32,
    page_size: u32,
    state: tauri::State<'_, AppState>,
) -> Result<serde_json::Value, String> {
    let browser = state.rom_browser.lock().await;
    let games = browser.browse_platform(&platform_id, Some(&path)).await?;
    
    let total_items = games.len();
    let start_idx = ((page - 1) * page_size) as usize;
    let end_idx = (start_idx + page_size as usize).min(total_items);
    
    let paginated_games = games[start_idx..end_idx].to_vec();
    
    let result = serde_json::json!({
        "games": paginated_games,
        "total": total_items,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_items as f64 / page_size as f64).ceil() as u32
    });
    
    Ok(result)
}

#[tauri::command]
async fn browse_directory(
    platform_id: String,
    path: String,
    state: tauri::State<'_, AppState>,
) -> Result<Vec<GameInfo>, String> {
    let browser = state.rom_browser.lock().await;
    browser.browse_platform(&platform_id, Some(&path)).await
}

#[tauri::command]
async fn search_platforms(
    query: String,
    state: tauri::State<'_, AppState>,
) -> Result<Vec<PlatformInfo>, String> {
    let browser = state.rom_browser.lock().await;
    browser.search_platforms(&query).await
}

#[tauri::command]
async fn download_game(game_name: String, url: String) -> Result<String, String> {
    // This would integrate with the ROM downloader
    // For now, just return a success message
    Ok(format!("Download started for: {}", game_name))
}

#[tauri::command]
async fn get_game_metadata(game_name: String) -> Result<serde_json::Value, String> {
    let db_path = "../../scripts/game-management/games.db";
    
    if !Path::new(db_path).exists() {
        return Ok(serde_json::json!({
            "name": game_name,
            "description": "No metadata available",
            "rating": null,
            "cover_art": null,
            "platforms": [],
            "genres": []
        }));
    }
    
    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT name, rating, summary, genres, platforms, release_date, cover_url, metacritic_score
         FROM games 
         WHERE name LIKE ? OR name LIKE ?"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;
    
    let mut rows = stmt.query([
        &format!("%{}%", game_name),
        &format!("{}%", game_name),
    ]).map_err(|e| format!("Failed to query database: {}", e))?;
    
    if let Some(row) = rows.next().map_err(|e| format!("Failed to get row: {}", e))? {
        let result = serde_json::json!({
            "name": row.get::<_, String>(0).unwrap_or_default(),
            "rating": row.get::<_, Option<f64>>(1).unwrap_or(None),
            "description": row.get::<_, Option<String>>(2).unwrap_or(None),
            "genres": row.get::<_, Option<String>>(3).unwrap_or(None)
                .and_then(|s| serde_json::from_str::<Vec<String>>(&s).ok())
                .unwrap_or_default(),
            "platforms": row.get::<_, Option<String>>(4).unwrap_or(None)
                .and_then(|s| serde_json::from_str::<Vec<String>>(&s).ok())
                .unwrap_or_default(),
            "release_date": row.get::<_, Option<String>>(5).unwrap_or(None),
            "cover_art": row.get::<_, Option<String>>(6).unwrap_or(None),
            "metacritic_score": row.get::<_, Option<i64>>(7).unwrap_or(None)
        });
        Ok(result)
    } else {
        Ok(serde_json::json!({
            "name": game_name,
            "description": "No metadata found",
            "rating": null,
            "cover_art": null,
            "platforms": [],
            "genres": []
        }))
    }
}

#[tauri::command]
async fn get_library_games() -> Result<Vec<GameInfo>, String> {
    let db_path = "../../scripts/game-management/games.db";
    
    if !Path::new(db_path).exists() {
        return Ok(vec![]);
    }
    
    let conn = Connection::open(db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;
    
    let mut stmt = conn.prepare(
        "SELECT name, rating, summary, genres, platforms, release_date, cover_url, metacritic_score
         FROM games 
         ORDER BY name"
    ).map_err(|e| format!("Failed to prepare statement: {}", e))?;
    
    let mut games = Vec::new();
    let mut rows = stmt.query([]).map_err(|e| format!("Failed to query database: {}", e))?;
    
    while let Some(row) = rows.next().map_err(|e| format!("Failed to get row: {}", e))? {
        let game = GameInfo {
            name: row.get::<_, String>(0).unwrap_or_default(),
            platform: "PC".to_string(),
            rating: row.get::<_, Option<f64>>(1).unwrap_or(None),
            summary: row.get::<_, Option<String>>(2).unwrap_or(None),
            genres: row.get::<_, Option<String>>(3).unwrap_or(None)
                .and_then(|s| serde_json::from_str(&s).ok()),
            release_date: row.get::<_, Option<String>>(5).unwrap_or(None),
            cover_art: row.get::<_, Option<String>>(6).unwrap_or(None),
            is_favorite: Some(false),
            is_downloaded: Some(true),
            size: None,
            url: None,
            is_directory: Some(false),
            path: None,
        };
        games.push(game);
    }
    
    Ok(games)
}

#[tauri::command]
async fn get_settings() -> Result<SettingsData, String> {
    let config_path = "../../config/game_directories.conf";
    let mut rom_directories = Vec::new();
    
    if Path::new(config_path).exists() {
        if let Ok(content) = std::fs::read_to_string(config_path) {
            for line in content.lines() {
                let line = line.trim();
                if !line.is_empty() && !line.starts_with('#') && !line.starts_with("OUTPUT_DIR") {
                    rom_directories.push(line.to_string());
                }
            }
        }
    }
    
    Ok(SettingsData {
        rom_directories,
        download_directory: "../../downloads".to_string(),
        metadata_api_key: "".to_string(),
        auto_scan: true,
        scan_interval: 30,
        max_concurrent_downloads: 3,
    })
}

#[tauri::command]
async fn save_settings(settings: SettingsData) -> Result<String, String> {
    let config_path = "../../config/game_directories.conf";
    
    let mut content = String::new();
    content.push_str("# Game Shortcut Creator Configuration\n");
    content.push_str("# This file contains all game installation directories across all drives\n");
    content.push_str("# Format: One directory per line, comments start with #\n\n");
    
    for dir in &settings.rom_directories {
        content.push_str(&format!("{}\n", dir));
    }
    
    content.push_str(&format!("\n# Output directory for shortcuts\nOUTPUT_DIR = {}\n", settings.download_directory));
    
    std::fs::write(config_path, content)
        .map_err(|e| format!("Failed to save settings: {}", e))?;
    
    Ok("Settings saved successfully".to_string())
}

#[tauri::command]
async fn start_rom_scan() -> Result<String, String> {
    // This would integrate with the smart metadata downloader
    // For now, just return a success message
    Ok("ROM scan completed successfully".to_string())
}

fn main() {
    let app_state = AppState {
        rom_browser: TokioMutex::new(RomBrowserService::new()),
    };

    tauri::Builder::default()
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            get_platforms,
            browse_platform,
            browse_platform_paginated,
            browse_directory,
            search_platforms,
            download_game,
            get_game_metadata,
            get_library_games,
            get_settings,
            save_settings,
            start_rom_scan
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}