// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use std::path::Path;
use tauri::State;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct GameInfo {
    name: String,
    platform: String,
    size: Option<String>,
    url: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct PlatformInfo {
    id: String,
    name: String,
    dataset: String,
}

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn get_platforms() -> Result<Vec<PlatformInfo>, String> {
    // This will integrate with your Python scripts
    // For now, return mock data
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
    ])
}

#[tauri::command]
async fn browse_platform(platform_id: String) -> Result<Vec<GameInfo>, String> {
    // This will integrate with your Python scripts
    // For now, return mock data
    Ok(vec![
        GameInfo {
            name: "Sample Game 1".to_string(),
            platform: platform_id.clone(),
            size: Some("1.2 GB".to_string()),
            url: Some("https://example.com/game1.zip".to_string()),
        },
        GameInfo {
            name: "Sample Game 2".to_string(),
            platform: platform_id.clone(),
            size: Some("800 MB".to_string()),
            url: Some("https://example.com/game2.zip".to_string()),
        },
    ])
}

#[tauri::command]
async fn download_game(game_name: String, url: String) -> Result<String, String> {
    // This will integrate with your Python download scripts
    Ok(format!("Download started for: {}", game_name))
}

#[tauri::command]
async fn get_game_metadata(game_name: String) -> Result<serde_json::Value, String> {
    // This will integrate with your Python metadata scripts
    Ok(serde_json::json!({
        "name": game_name,
        "description": "A sample game description",
        "rating": 8.5,
        "cover_art": "https://example.com/cover.jpg",
        "platforms": ["PlayStation 2"],
        "genres": ["Action", "Adventure"]
    }))
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            greet,
            get_platforms,
            browse_platform,
            download_game,
            get_game_metadata
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
