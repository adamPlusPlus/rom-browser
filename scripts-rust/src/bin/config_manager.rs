use anyhow::Result;
use clap::Parser;
use rom_browser_scripts::{Config, SettingsData};
use serde_json;
use std::collections::HashMap;
use std::path::PathBuf;
use tracing::{info, warn, error};

/// Application Configuration Manager
/// Handles loading and applying configuration settings for the game launcher
#[derive(Parser)]
#[command(name = "config-manager")]
#[command(about = "Manages application configuration")]
struct Args {
    /// Config file path
    #[arg(short, long, default_value = "app_config.json")]
    config_file: PathBuf,
    
    /// Get a specific config value
    #[arg(short, long)]
    get: Option<String>,
    
    /// Set a specific config value
    #[arg(short, long)]
    set: Option<String>,
    
    /// Value to set (used with --set)
    #[arg(short, long)]
    value: Option<String>,
    
    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct AppConfig {
    appearance: AppearanceConfig,
    behavior: BehaviorConfig,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct AppearanceConfig {
    theme: String,
    colors: HashMap<String, String>,
    fonts: HashMap<String, FontConfig>,
    game_list: GameListConfig,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct FontConfig {
    family: String,
    size: u32,
    weight: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct GameListConfig {
    row_height: u32,
    alternating_colors: bool,
    alternating_color: String,
    hover_color: String,
    selected_color: String,
    rating_color: String,
    custom_rating_color: String,
    favorite_color: String,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct BehaviorConfig {
    auto_refresh_ratings: bool,
    confirm_rating_changes: bool,
    rating_precision: u32,
    default_rating: f64,
    rating_range: RatingRange,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
struct RatingRange {
    min: f64,
    max: f64,
}

struct ConfigManager {
    config_file: PathBuf,
    config: AppConfig,
}

impl ConfigManager {
    fn new(config_file: PathBuf) -> Self {
        let config = Self::load_config(&config_file).unwrap_or_else(|_| Self::get_default_config());
        Self { config_file, config }
    }

    fn load_config(config_file: &PathBuf) -> Result<AppConfig> {
        if config_file.exists() {
            let content = std::fs::read_to_string(config_file)?;
            let config: AppConfig = serde_json::from_str(&content)?;
            Ok(config)
        } else {
            Ok(Self::get_default_config())
        }
    }

    fn get_default_config() -> AppConfig {
        let mut colors = HashMap::new();
        colors.insert("background".to_string(), "#1e1e1e".to_string());
        colors.insert("foreground".to_string(), "#ffffff".to_string());
        colors.insert("secondary_background".to_string(), "#2d2d2d".to_string());
        colors.insert("secondary_foreground".to_string(), "#cccccc".to_string());
        colors.insert("accent".to_string(), "#0078d4".to_string());
        colors.insert("accent_hover".to_string(), "#106ebe".to_string());
        colors.insert("success".to_string(), "#107c10".to_string());
        colors.insert("warning".to_string(), "#ff8c00".to_string());
        colors.insert("error".to_string(), "#d13438".to_string());
        colors.insert("border".to_string(), "#404040".to_string());
        colors.insert("selection".to_string(), "#0078d4".to_string());
        colors.insert("selection_background".to_string(), "#1a4a6b".to_string());

        let mut fonts = HashMap::new();
        fonts.insert("default".to_string(), FontConfig {
            family: "Segoe UI".to_string(),
            size: 9,
            weight: "normal".to_string(),
        });
        fonts.insert("heading".to_string(), FontConfig {
            family: "Segoe UI".to_string(),
            size: 10,
            weight: "bold".to_string(),
        });
        fonts.insert("small".to_string(), FontConfig {
            family: "Segoe UI".to_string(),
            size: 8,
            weight: "normal".to_string(),
        });
        fonts.insert("large".to_string(), FontConfig {
            family: "Segoe UI".to_string(),
            size: 12,
            weight: "normal".to_string(),
        });

        AppConfig {
            appearance: AppearanceConfig {
                theme: "dark".to_string(),
                colors,
                fonts,
                game_list: GameListConfig {
                    row_height: 20,
                    alternating_colors: true,
                    alternating_color: "#252525".to_string(),
                    hover_color: "#3a3a3a".to_string(),
                    selected_color: "#0078d4".to_string(),
                    rating_color: "#b0b0b0".to_string(),
                    custom_rating_color: "#ffd700".to_string(),
                    favorite_color: "#ffd700".to_string(),
                },
            },
            behavior: BehaviorConfig {
                auto_refresh_ratings: true,
                confirm_rating_changes: false,
                rating_precision: 1,
                default_rating: 7.0,
                rating_range: RatingRange {
                    min: 0.0,
                    max: 10.0,
                },
            },
        }
    }

    fn get_color(&self, path: &str) -> Option<&String> {
        let keys: Vec<&str> = path.split('.').collect();
        if keys.len() >= 2 && keys[0] == "appearance" && keys[1] == "colors" {
            self.config.appearance.colors.get(keys[2])
        } else {
            None
        }
    }

    fn get_font(&self, font_type: &str) -> Option<&FontConfig> {
        self.config.appearance.fonts.get(font_type)
    }

    fn save_config(&self) -> Result<()> {
        let content = serde_json::to_string_pretty(&self.config)?;
        std::fs::write(&self.config_file, content)?;
        Ok(())
    }

    fn set_value(&mut self, path: &str, value: &str) -> Result<()> {
        let keys: Vec<&str> = path.split('.').collect();
        
        match keys.as_slice() {
            ["appearance", "theme"] => {
                self.config.appearance.theme = value.to_string();
            },
            ["appearance", "colors", color_key] => {
                self.config.appearance.colors.insert(color_key.to_string(), value.to_string());
            },
            ["behavior", "auto_refresh_ratings"] => {
                self.config.behavior.auto_refresh_ratings = value.parse()?;
            },
            ["behavior", "confirm_rating_changes"] => {
                self.config.behavior.confirm_rating_changes = value.parse()?;
            },
            ["behavior", "rating_precision"] => {
                self.config.behavior.rating_precision = value.parse()?;
            },
            ["behavior", "default_rating"] => {
                self.config.behavior.default_rating = value.parse()?;
            },
            ["behavior", "rating_range", "min"] => {
                self.config.behavior.rating_range.min = value.parse()?;
            },
            ["behavior", "rating_range", "max"] => {
                self.config.behavior.rating_range.max = value.parse()?;
            },
            _ => {
                return Err(anyhow::anyhow!("Unknown config path: {}", path));
            }
        }
        
        self.save_config()?;
        Ok(())
    }

    fn get_value(&self, path: &str) -> Option<String> {
        let keys: Vec<&str> = path.split('.').collect();
        
        match keys.as_slice() {
            ["appearance", "theme"] => Some(self.config.appearance.theme.clone()),
            ["appearance", "colors", color_key] => self.config.appearance.colors.get(&color_key.to_string()).cloned(),
            ["behavior", "auto_refresh_ratings"] => Some(self.config.behavior.auto_refresh_ratings.to_string()),
            ["behavior", "confirm_rating_changes"] => Some(self.config.behavior.confirm_rating_changes.to_string()),
            ["behavior", "rating_precision"] => Some(self.config.behavior.rating_precision.to_string()),
            ["behavior", "default_rating"] => Some(self.config.behavior.default_rating.to_string()),
            ["behavior", "rating_range", "min"] => Some(self.config.behavior.rating_range.min.to_string()),
            ["behavior", "rating_range", "max"] => Some(self.config.behavior.rating_range.max.to_string()),
            _ => None,
        }
    }

    fn run(&mut self, args: Args) -> Result<()> {
        if args.verbose {
            tracing_subscriber::fmt::init();
        }

        if let Some(path) = args.get {
            if let Some(value) = self.get_value(&path) {
                println!("{}", value);
            } else {
                error!("Config path not found: {}", path);
                return Err(anyhow::anyhow!("Config path not found: {}", path));
            }
        } else if let Some(path) = args.set {
            if let Some(value) = args.value {
                self.set_value(&path, &value)?;
                info!("Set {} = {}", path, value);
            } else {
                error!("No value provided for --set");
                return Err(anyhow::anyhow!("No value provided for --set"));
            }
        } else {
            // Print current config
            println!("{}", serde_json::to_string_pretty(&self.config)?);
        }

        Ok(())
    }
}

fn main() -> Result<()> {
    let args = Args::parse();
    let mut manager = ConfigManager::new(args.config_file.clone());
    manager.run(args)
}
