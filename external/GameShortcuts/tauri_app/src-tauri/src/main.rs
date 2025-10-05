#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Serialize, Deserialize)]
struct BackendResult {
    success: bool,
    message: Option<String>,
    games: Option<serde_json::Value>,
}

#[tauri::command]
fn call_backend(command: String, args: Vec<String>) -> Result<String, String> {
    let output = Command::new("python")
        .arg("../../backend_integration.py")
        .arg(command)
        .args(args)
        .output()
        .map_err(|e| format!("exec error: {}", e))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![call_backend])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}


