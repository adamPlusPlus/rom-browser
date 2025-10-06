// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::path::Path;
use tauri::State;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize)]
struct GameInfo {
    name: String,
    platform: String,
    size: Option<String>,
    url: Option<String>,
    cover_art: Option<String>,
    rating: Option<f64>,
    summary: Option<String>,
    genres: Option<String>,
    release_date: Option<String>,
    is_favorite: Option<bool>,
    is_downloaded: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
struct PlatformInfo {
    id: String,
    name: String,
    dataset: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct SettingsData {
    rom_directories: Vec<String>,
    download_directory: String,
    metadata_api_key: String,
    auto_scan: bool,
    scan_interval: u32,
    max_concurrent_downloads: u32,
}

// Helper function to run Python scripts
fn run_python_script(script_path: &str, args: &[&str]) -> Result<String, String> {
    let output = Command::new("python")
        .arg(script_path)
        .args(args)
        .output()
        .map_err(|e| format!("Failed to execute Python script: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(format!("Script error: {}", String::from_utf8_lossy(&output.stderr)))
    }
}

// Helper function to read JSON from Python script output
fn parse_json_output<T: serde::de::DeserializeOwned>(output: &str) -> Result<T, String> {
    serde_json::from_str(output)
        .map_err(|e| format!("Failed to parse JSON: {}", e))
}

#[tauri::command]
async fn get_platforms() -> Result<Vec<PlatformInfo>, String> {
    // Call the Python ROM browser script to get platforms
    let script_path = "../../scripts/rom-sourcing/rom_browser.py";
    
    // For now, return the known platforms from the ROM browser
    // In a full implementation, we'd parse the actual output
    Ok(vec![
        PlatformInfo {
            id: "ps2".to_string(),
            name: "PlayStation 2".to_string(),
            dataset: "redump".to_string(),
        },
        PlatformInfo {
            id: "xbox".to_string(),
            name: "Xbox".to_string(),
            dataset: "redump".to_string(),
        },
        PlatformInfo {
            id: "gamecube".to_string(),
            name: "GameCube".to_string(),
            dataset: "redump".to_string(),
        },
        PlatformInfo {
            id: "ps3".to_string(),
            name: "PlayStation 3".to_string(),
            dataset: "redump".to_string(),
        },
        PlatformInfo {
            id: "wii".to_string(),
            name: "Nintendo Wii".to_string(),
            dataset: "redump".to_string(),
        },
        PlatformInfo {
            id: "nes".to_string(),
            name: "Nintendo Entertainment System".to_string(),
            dataset: "no-intro".to_string(),
        },
        PlatformInfo {
            id: "snes".to_string(),
            name: "Super Nintendo Entertainment System".to_string(),
            dataset: "no-intro".to_string(),
        },
        PlatformInfo {
            id: "n64".to_string(),
            name: "Nintendo 64".to_string(),
            dataset: "no-intro".to_string(),
        },
    ])
}

#[tauri::command]
async fn browse_platform(platform_id: String) -> Result<Vec<GameInfo>, String> {
    // This would call the Python ROM browser script with the platform ID
    // For now, return mock data based on the platform
    let games = match platform_id.as_str() {
        "ps2" => vec![
            GameInfo {
                name: "Grand Theft Auto: San Andreas".to_string(),
                platform: "PlayStation 2".to_string(),
                size: Some("4.2 GB".to_string()),
                url: Some("https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%202/Grand%20Theft%20Auto%20-%20San%20Andreas%20(USA).zip".to_string()),
                cover_art: None,
                rating: None,
                summary: None,
                genres: None,
                release_date: None,
                is_favorite: None,
                is_downloaded: None,
            },
            GameInfo {
                name: "Metal Gear Solid 3: Snake Eater".to_string(),
                platform: "PlayStation 2".to_string(),
                size: Some("3.8 GB".to_string()),
                url: Some("https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%202/Metal%20Gear%20Solid%203%20-%20Snake%20Eater%20(USA).zip".to_string()),
                cover_art: None,
                rating: None,
                summary: None,
                genres: None,
                release_date: None,
                is_favorite: None,
                is_downloaded: None,
            },
        ],
        "xbox" => vec![
            GameInfo {
                name: "Halo: Combat Evolved".to_string(),
                platform: "Xbox".to_string(),
                size: Some("1.8 GB".to_string()),
                url: Some("https://myrient.erista.me/files/Redump/Microsoft%20-%20Xbox/Halo%20-%20Combat%20Evolved%20(USA).zip".to_string()),
                cover_art: None,
                rating: None,
                summary: None,
                genres: None,
                release_date: None,
                is_favorite: None,
                is_downloaded: None,
            },
        ],
        _ => vec![],
    };
    
    Ok(games)
}

#[tauri::command]
async fn download_game(game_name: String, url: String) -> Result<String, String> {
    // Call the Python ROM downloader script
    let script_path = "../../scripts/rom-sourcing/rom_downloader.py";
    
    // For now, simulate the download
    Ok(format!("Download started for: {}", game_name))
}

#[tauri::command]
async fn get_game_metadata(game_name: String) -> Result<serde_json::Value, String> {
    // Query the games database for metadata
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
    
    // Use Python to query the database
    let python_code = format!(
        r#"
import sqlite3
import json
import sys

try:
    conn = sqlite3.connect('{}')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, rating, summary, genres, platforms, release_date, cover_url, metacritic_score
        FROM games 
        WHERE name LIKE ? OR name LIKE ?
    ''', (f'%{{}}%', f'{{}}%'))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        result = {{
            'name': row[0],
            'rating': row[1],
            'description': row[2] or 'No description available',
            'genres': row[3] or '',
            'platforms': row[4] or '',
            'release_date': row[5] or '',
            'cover_art': row[6] or '',
            'metacritic_score': row[7]
        }}
    else:
        result = {{
            'name': '{}',
            'description': 'No metadata found',
            'rating': null,
            'cover_art': null,
            'platforms': [],
            'genres': []
        }}
    
    print(json.dumps(result))
    
except Exception as e:
    print(json.dumps({{'error': str(e)}}))
"#,
        db_path, game_name, game_name, game_name
    );
    
    let output = Command::new("python")
        .arg("-c")
        .arg(&python_code)
        .current_dir("../../scripts/game-management")
        .output()
        .map_err(|e| format!("Failed to query database: {}", e))?;

    if output.status.success() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        serde_json::from_str(&output_str)
            .map_err(|e| format!("Failed to parse database result: {}", e))
    } else {
        Err(format!("Database query error: {}", String::from_utf8_lossy(&output.stderr)))
    }
}

#[tauri::command]
async fn get_library_games() -> Result<Vec<GameInfo>, String> {
    // Get games from the database
    let db_path = "../../scripts/game-management/games.db";
    
    if !Path::new(db_path).exists() {
        return Ok(vec![]);
    }
    
    let python_code = r#"
import sqlite3
import json
import sys

try:
    conn = sqlite3.connect('games.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, rating, summary, genres, platforms, release_date, cover_url, metacritic_score
        FROM games 
        ORDER BY name
    ''')
    
    games = []
    for row in cursor.fetchall():
        game = {
            'name': row[0],
            'platform': 'PC',  # Default platform for library games
            'rating': row[1],
            'summary': row[2],
            'genres': row[3],
            'release_date': row[5],
            'cover_art': row[6],
            'metacritic_score': row[7],
            'is_favorite': False,  # Would need separate favorites table
            'is_downloaded': True,  # Games in library are downloaded
            'size': None,
            'url': None
        }
        games.append(game)
    
    conn.close()
    print(json.dumps(games))
    
except Exception as e:
    print(json.dumps({'error': str(e)}))
"#;
    
    let output = Command::new("python")
        .arg("-c")
        .arg(python_code)
        .current_dir("../../scripts/game-management")
        .output()
        .map_err(|e| format!("Failed to query library: {}", e))?;

    if output.status.success() {
        let output_str = String::from_utf8_lossy(&output.stdout);
        serde_json::from_str(&output_str)
            .map_err(|e| format!("Failed to parse library result: {}", e))
    } else {
        Err(format!("Library query error: {}", String::from_utf8_lossy(&output.stderr)))
    }
}

#[tauri::command]
async fn get_settings() -> Result<SettingsData, String> {
    // Read settings from config files
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
    // Save settings to config files
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
    // Call the Python scanning script
    let script_path = "../../scripts/game-management/smart_metadata_downloader.py";
    
    // For now, simulate the scan
    Ok("ROM scan started successfully".to_string())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            get_platforms,
            browse_platform,
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
