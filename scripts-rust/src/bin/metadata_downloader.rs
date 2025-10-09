use anyhow::Result;
use clap::Parser;
use rom_browser_scripts::{
    Config, GameMetadata, SteamGameData, RawgGameData, GogProduct, ScreenscraperGame,
    SteamGenre, SteamReleaseDate, RawgGenre, RawgPlatform, RawgPlatformInfo,
    RawgDeveloper, RawgPublisher, RawgScreenshot, GogGenre, GogDeveloper, GogPublisher,
    ScreenscraperDates, ScreenscraperMedia,
    get_popular_games_ratings, get_game_name_suffixes,
};
use rusqlite::{Connection, Result as SqlResult};
use serde_json;
use std::collections::HashMap;
use std::path::PathBuf;
use tracing::{info, warn, error};
use chrono::Utc;

/// Game Metadata Downloader
/// Downloads game metadata and cover art from various APIs
#[derive(Parser)]
#[command(name = "metadata-downloader")]
#[command(about = "Downloads game metadata and cover art")]
struct Args {
    /// Game name to search for
    #[arg(short, long)]
    game: Option<String>,
    
    /// Database path
    #[arg(short, long, default_value = "games.db")]
    db_path: PathBuf,
    
    /// Metadata directory
    #[arg(short, long, default_value = "metadata")]
    metadata_dir: PathBuf,
    
    /// Covers directory
    #[arg(short, long, default_value = "covers")]
    covers_dir: PathBuf,
    
    /// API key for IGDB
    #[arg(short, long)]
    igdb_key: Option<String>,
    
    /// Screenscraper username
    #[arg(short, long)]
    screenscraper_user: Option<String>,
    
    /// Screenscraper password
    #[arg(short, long)]
    screenscraper_pass: Option<String>,
    
    /// RAWG API key
    #[arg(short, long)]
    rawg_key: Option<String>,
    
    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

struct GameMetadataDownloader {
    config: Config,
    db_path: PathBuf,
    metadata_dir: PathBuf,
    covers_dir: PathBuf,
    igdb_key: Option<String>,
    screenscraper_user: Option<String>,
    screenscraper_pass: Option<String>,
    rawg_key: Option<String>,
    popular_games: HashMap<String, f64>,
}

impl GameMetadataDownloader {
    fn new(
        db_path: PathBuf,
        metadata_dir: PathBuf,
        covers_dir: PathBuf,
        igdb_key: Option<String>,
        screenscraper_user: Option<String>,
        screenscraper_pass: Option<String>,
        rawg_key: Option<String>,
    ) -> Self {
        Self {
            config: Config::default(),
            db_path,
            metadata_dir,
            covers_dir,
            igdb_key,
            screenscraper_user,
            screenscraper_pass,
            rawg_key,
            popular_games: get_popular_games_ratings(),
        }
    }

    fn init_database(&self) -> Result<()> {
        let conn = Connection::open(&self.db_path)?;
        
        conn.execute(
            "CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                igdb_id INTEGER,
                cover_url TEXT,
                cover_path TEXT,
                rating REAL,
                rating_count INTEGER,
                summary TEXT,
                genres TEXT,
                platforms TEXT,
                release_date TEXT,
                developer TEXT,
                publisher TEXT,
                steam_id INTEGER,
                metacritic_score INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )",
            [],
        )?;
        
        Ok(())
    }

    fn clean_game_name_for_search(&self, name: &str) -> String {
        let mut clean_name = name.to_string();
        
        for suffix in get_game_name_suffixes() {
            clean_name = clean_name.replace(suffix, " ");
        }
        
        clean_name.split_whitespace().collect::<Vec<&str>>().join(" ")
    }

    fn assign_basic_rating(&self, game_name: &str, genres: &[String]) -> f64 {
        let mut rating = 7.0; // Base rating
        
        let game_lower = game_name.to_lowercase();
        for (keyword, score) in &self.popular_games {
            if game_lower.contains(keyword) {
                rating = *score;
                break;
            }
        }
        
        // Adjust based on genres
        for genre in genres {
            let genre_lower = genre.to_lowercase();
            if genre_lower.contains("rpg") {
                rating += 0.5;
            } else if genre_lower.contains("strategy") {
                rating += 0.3;
            } else if genre_lower.contains("indie") {
                rating += 0.2;
            } else if genre_lower.contains("action") {
                rating += 0.1;
            }
        }
        
        // Cap rating between 5.0 and 10.0
        rating.max(5.0).min(10.0)
    }

    async fn search_steam(&self, game_name: &str) -> Result<Option<SteamGameData>> {
        let clean_name = self.clean_game_name_for_search(game_name);
        
        let client = reqwest::Client::new();
        let params = [
            ("term", clean_name.as_str()),
            ("category1", "998"), // Games
            ("cc", "us"),
            ("l", "english"),
        ];
        
        let response = client
            .get("https://store.steampowered.com/api/storesearch")
            .query(&params)
            .send()
            .await?;
        
        if response.status().is_success() {
            let data: serde_json::Value = response.json().await?;
            if let Some(items) = data.get("items").and_then(|v| v.as_array()) {
                if let Some(first_item) = items.first() {
                    if let Some(steam_id) = first_item.get("id").and_then(|v| v.as_i64()) {
                        return self.get_steam_game_details(steam_id, first_item).await;
                    }
                }
            }
        }
        
        Ok(None)
    }

    async fn get_steam_game_details(&self, steam_id: i64, basic_data: &serde_json::Value) -> Result<Option<SteamGameData>> {
        let client = reqwest::Client::new();
        let params = [
            ("appids", &steam_id.to_string()),
            ("cc", &"us".to_string()),
            ("l", &"english".to_string()),
        ];
        
        let response = client
            .get("https://store.steampowered.com/api/appdetails")
            .query(&params)
            .send()
            .await?;
        
        if response.status().is_success() {
            let data: serde_json::Value = response.json().await?;
            if let Some(game_data) = data.get(&steam_id.to_string())
                .and_then(|v| v.get("success"))
                .and_then(|v| v.as_bool())
                .filter(|&success| success)
                .and_then(|_| data.get(&steam_id.to_string()).and_then(|v| v.get("data"))) {
                
                return Ok(Some(SteamGameData {
                    steam_appid: Some(steam_id),
                    name: game_data.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                    header_image: game_data.get("header_image").and_then(|v| v.as_str()).map(|s| s.to_string()),
                    short_description: game_data.get("short_description").and_then(|v| v.as_str()).map(|s| s.to_string()),
                    genres: game_data.get("genres")
                        .and_then(|v| v.as_array())
                        .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| SteamGenre {
                            description: obj.get("description").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                        }).collect())
                        .unwrap_or_default(),
                    release_date: game_data.get("release_date")
                        .and_then(|v| v.as_object())
                        .map(|obj| SteamReleaseDate {
                            date: obj.get("date").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                        }),
                    developers: game_data.get("developers")
                        .and_then(|v| v.as_array())
                        .map(|arr| arr.iter().filter_map(|v| v.as_str()).map(|s| s.to_string()).collect())
                        .unwrap_or_default(),
                    publishers: game_data.get("publishers")
                        .and_then(|v| v.as_array())
                        .map(|arr| arr.iter().filter_map(|v| v.as_str()).map(|s| s.to_string()).collect())
                        .unwrap_or_default(),
                }));
            }
        }
        
        // Fallback to basic data
        Ok(Some(SteamGameData {
            steam_appid: Some(steam_id),
            name: basic_data.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            header_image: basic_data.get("tiny_image").and_then(|v| v.as_str()).map(|s| s.to_string()),
            short_description: None,
            genres: Vec::new(),
            release_date: None,
            developers: Vec::new(),
            publishers: Vec::new(),
        }))
    }

    async fn search_rawg(&self, game_name: &str) -> Result<Option<RawgGameData>> {
        let Some(rawg_key) = &self.rawg_key else {
            return Ok(None);
        };
        
        let clean_name = self.clean_game_name_for_search(game_name);
        
        let client = reqwest::Client::new();
        let params = [
            ("key", rawg_key.as_str()),
            ("search", clean_name.as_str()),
            ("page_size", "1"),
        ];
        
        let response = client
            .get("https://api.rawg.io/api/games")
            .query(&params)
            .send()
            .await?;
        
        if response.status().is_success() {
            let data: serde_json::Value = response.json().await?;
            if let Some(results) = data.get("results").and_then(|v| v.as_array()) {
                if let Some(first_result) = results.first() {
                    if let Some(game_id) = first_result.get("id").and_then(|v| v.as_i64()) {
                        return self.get_rawg_game_details(game_id, first_result).await;
                    } else {
                        return Ok(Some(self.convert_rawg_to_metadata(first_result)?));
                    }
                }
            }
        }
        
        Ok(None)
    }

    async fn get_rawg_game_details(&self, game_id: i64, basic_data: &serde_json::Value) -> Result<Option<RawgGameData>> {
        let Some(rawg_key) = &self.rawg_key else {
            return Ok(None);
        };
        
        let client = reqwest::Client::new();
        let params = [("key", rawg_key.as_str())];
        
        let response = client
            .get(&format!("https://api.rawg.io/api/games/{}", game_id))
            .query(&params)
            .send()
            .await?;
        
        if response.status().is_success() {
            let detailed_data: serde_json::Value = response.json().await?;
            return Ok(Some(self.convert_rawg_to_metadata(&detailed_data)?));
        }
        
        // Fallback to basic data
        Ok(Some(self.convert_rawg_to_metadata(basic_data)?))
    }

    fn convert_rawg_to_metadata(&self, rawg_data: &serde_json::Value) -> Result<RawgGameData> {
        Ok(RawgGameData {
            id: rawg_data.get("id").and_then(|v| v.as_i64()).unwrap_or(0),
            name: rawg_data.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            background_image: rawg_data.get("background_image").and_then(|v| v.as_str()).map(|s| s.to_string()),
            rating: rawg_data.get("rating").and_then(|v| v.as_f64()),
            ratings_count: rawg_data.get("ratings_count").and_then(|v| v.as_i64()),
            description_raw: rawg_data.get("description_raw").and_then(|v| v.as_str()).map(|s| s.to_string()),
            genres: rawg_data.get("genres")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| RawgGenre {
                    name: obj.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                }).collect())
                .unwrap_or_default(),
            platforms: rawg_data.get("platforms")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| RawgPlatform {
                    platform: RawgPlatformInfo {
                        name: obj.get("platform").and_then(|v| v.as_object())
                            .and_then(|p| p.get("name").and_then(|v| v.as_str()))
                            .unwrap_or("").to_string(),
                    },
                }).collect())
                .unwrap_or_default(),
            released: rawg_data.get("released").and_then(|v| v.as_str()).map(|s| s.to_string()),
            developers: rawg_data.get("developers")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| RawgDeveloper {
                    name: obj.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                }).collect())
                .unwrap_or_default(),
            publishers: rawg_data.get("publishers")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| RawgPublisher {
                    name: obj.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                }).collect())
                .unwrap_or_default(),
            short_screenshots: rawg_data.get("short_screenshots")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| RawgScreenshot {
                    image: obj.get("image").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                }).collect())
                .unwrap_or_default(),
        })
    }

    async fn search_gog_database(&self, game_name: &str) -> Result<Option<GogProduct>> {
        let clean_name = self.clean_game_name_for_search(game_name);
        
        let client = reqwest::Client::new();
        let params = [
            ("search", clean_name.as_str()),
            ("limit", "5"),
            ("page", "1"),
            ("sort", "relevance"),
        ];
        
        let response = client
            .get("https://www.gog.com/games/ajax/filtered")
            .query(&params)
            .header("Accept", "application/json")
            .header("User-Agent", "GameLauncher/1.0")
            .header("Referer", "https://www.gog.com/")
            .send()
            .await?;
        
        if response.status().is_success() {
            let data: serde_json::Value = response.json().await?;
            if let Some(products) = data.get("products").and_then(|v| v.as_array()) {
                if let Some(first_product) = products.first() {
                    return Ok(Some(self.convert_gog_to_metadata(first_product)?));
                }
            }
        }
        
        Ok(None)
    }

    fn convert_gog_to_metadata(&self, gog_data: &serde_json::Value) -> Result<GogProduct> {
        Ok(GogProduct {
            id: gog_data.get("id").and_then(|v| v.as_i64()).unwrap_or(0),
            title: gog_data.get("title").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            description: gog_data.get("description").and_then(|v| v.as_str()).map(|s| s.to_string()),
            image: gog_data.get("image").and_then(|v| v.as_str()).map(|s| s.to_string()),
            gallery: gog_data.get("gallery")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_str()).map(|s| s.to_string()).collect()),
            rating: gog_data.get("rating").and_then(|v| v.as_f64()),
            genres: gog_data.get("genres")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| GogGenre {
                    name: obj.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                }).collect()),
            developers: gog_data.get("developers")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| GogDeveloper {
                    name: obj.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                }).collect()),
            publishers: gog_data.get("publishers")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| GogPublisher {
                    name: obj.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                }).collect()),
            release_date: gog_data.get("releaseDate").and_then(|v| v.as_str()).map(|s| s.to_string()),
        })
    }

    async fn search_screenscraper(&self, game_name: &str) -> Result<Option<ScreenscraperGame>> {
        let (Some(username), Some(password)) = (&self.screenscraper_user, &self.screenscraper_pass) else {
            return Ok(None);
        };
        
        let clean_name = self.clean_game_name_for_search(game_name);
        
        let client = reqwest::Client::new();
        let search_params = [
            ("devid", username.as_str()),
            ("devpassword", password.as_str()),
            ("softname", "testlaunchapp"),
            ("output", "json"),
            ("systemeid", "1"), // PC games
            ("recherche", clean_name.as_str()),
        ];
        
        let response = client
            .get("https://www.screenscraper.fr/api2/jeuRecherche.php")
            .query(&search_params)
            .header("Accept", "application/json")
            .header("User-Agent", "GameLauncher/1.0")
            .send()
            .await?;
        
        if response.status().is_success() {
            let data: serde_json::Value = response.json().await?;
            if let Some(response_data) = data.get("response") {
                if let Some(jeux) = response_data.get("jeux").and_then(|v| v.as_array()) {
                    if let Some(first_jeu) = jeux.first() {
                        if let Some(jeu_id) = first_jeu.get("id").and_then(|v| v.as_i64()) {
                            return self.get_screenscraper_game_details(jeu_id, username, password).await;
                        }
                    }
                }
            }
        }
        
        Ok(None)
    }

    async fn get_screenscraper_game_details(&self, jeu_id: i64, username: &str, password: &str) -> Result<Option<ScreenscraperGame>> {
        let client = reqwest::Client::new();
        let info_params = [
            ("devid", username),
            ("devpassword", password),
            ("softname", "testlaunchapp"),
            ("output", "json"),
            ("id", &jeu_id.to_string()),
        ];
        
        let response = client
            .get("https://www.screenscraper.fr/api2/jeuInfos.php")
            .query(&info_params)
            .header("Accept", "application/json")
            .header("User-Agent", "GameLauncher/1.0")
            .send()
            .await?;
        
        if response.status().is_success() {
            let data: serde_json::Value = response.json().await?;
            if let Some(response_data) = data.get("response") {
                if let Some(jeu) = response_data.get("jeu") {
                    return Ok(Some(self.convert_screenscraper_to_metadata(jeu)?));
                }
            }
        }
        
        Ok(None)
    }

    fn convert_screenscraper_to_metadata(&self, screenscraper_data: &serde_json::Value) -> Result<ScreenscraperGame> {
        Ok(ScreenscraperGame {
            id: screenscraper_data.get("id").and_then(|v| v.as_i64()).unwrap_or(0),
            nom: screenscraper_data.get("nom").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            synopsis: screenscraper_data.get("synopsis").and_then(|v| v.as_str()).map(|s| s.to_string()),
            genre: screenscraper_data.get("genre").and_then(|v| v.as_str()).map(|s| s.to_string()),
            developpeur: screenscraper_data.get("developpeur").and_then(|v| v.as_str()).map(|s| s.to_string()),
            editeur: screenscraper_data.get("editeur").and_then(|v| v.as_str()).map(|s| s.to_string()),
            dates: screenscraper_data.get("dates")
                .and_then(|v| v.as_object())
                .map(|obj| ScreenscraperDates {
                    us: obj.get("us").and_then(|v| v.as_str()).map(|s| s.to_string()),
                }),
            medias: screenscraper_data.get("medias")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|v| v.as_object()).map(|obj| ScreenscraperMedia {
                    r#type: obj.get("type").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                    region: obj.get("region").and_then(|v| v.as_str()).map(|s| s.to_string()),
                    url: obj.get("url").and_then(|v| v.as_str()).map(|s| s.to_string()),
                }).collect()),
        })
    }

    async fn download_cover_art(&self, cover_url: &str, game_name: &str) -> Result<Option<String>> {
        if cover_url.is_empty() {
            return Ok(None);
        }
        
        let safe_name = self.safe_filename(game_name);
        let cover_path = self.covers_dir.join(format!("{}.jpg", safe_name));
        
        // Skip if already downloaded
        if cover_path.exists() {
            return Ok(Some(cover_path.to_string_lossy().to_string()));
        }
        
        let mut url = cover_url.to_string();
        if url.starts_with("//") {
            url = format!("https:{}", url);
        } else if url.starts_with('/') {
            url = format!("https://www.screenscraper.fr{}", url);
        } else if !url.starts_with("http") {
            url = format!("https://www.screenscraper.fr{}", url);
        }
        
        let client = reqwest::Client::new();
        let response = client.get(&url).send().await?;
        
        if response.status().is_success() {
            let bytes = response.bytes().await?;
            tokio::fs::write(&cover_path, bytes).await?;
            return Ok(Some(cover_path.to_string_lossy().to_string()));
        }
        
        Ok(None)
    }

    fn safe_filename(&self, filename: &str) -> String {
        let invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*'];
        let mut safe_name = filename.to_string();
        
        for char in invalid_chars {
            safe_name = safe_name.replace(char, "_");
        }
        
        if safe_name.len() > 100 {
            safe_name.truncate(100);
        }
        
        safe_name
    }

    async fn create_placeholder_cover(&self, game_name: &str) -> Result<Option<String>> {
        let safe_name = self.safe_filename(game_name);
        let placeholder_path = self.covers_dir.join(format!("{}_placeholder.jpg", safe_name));
        
        // Create a simple placeholder image using the image crate
        let img = image::RgbImage::new(200, 250);
        let mut img_buffer: Vec<u8> = Vec::new();
        let mut cursor = std::io::Cursor::new(&mut img_buffer);
        
        // For now, just create an empty file - in a real implementation,
        // you'd generate an actual placeholder image with text
        tokio::fs::write(&placeholder_path, b"").await?;
        
        Ok(Some(placeholder_path.to_string_lossy().to_string()))
    }

    async fn search_game(&self, game_name: &str) -> Result<Option<GameMetadata>> {
        // Try Steam API first
        if let Some(steam_data) = self.search_steam(game_name).await? {
            if let Some(summary) = &steam_data.short_description {
                if !summary.starts_with("Game: ") {
                    return Ok(Some(self.convert_steam_to_metadata(&steam_data)));
                }
            }
        }
        
        // Try GOG Database
        if let Some(gog_data) = self.search_gog_database(game_name).await? {
            if let Some(description) = &gog_data.description {
                if !description.starts_with("Game: ") {
                    return Ok(Some(self.convert_gog_to_game_metadata(&gog_data)));
                }
            }
        }
        
        // Try RAWG API
        if let Some(rawg_data) = self.search_rawg(game_name).await? {
            if let Some(summary) = &rawg_data.description_raw {
                if !summary.starts_with("Game: ") {
                    return Ok(Some(self.convert_rawg_to_game_metadata(&rawg_data)));
                }
            }
        }
        
        // Try Screenscraper.fr
        if let Some(screenscraper_data) = self.search_screenscraper(game_name).await? {
            if let Some(summary) = &screenscraper_data.synopsis {
                if !summary.starts_with("Game: ") {
                    return Ok(Some(self.convert_screenscraper_to_game_metadata(&screenscraper_data)));
                }
            }
        }
        
        // If all fail, create basic metadata
        Ok(Some(self.create_basic_metadata(game_name).await?))
    }

    fn convert_steam_to_metadata(&self, steam_data: &SteamGameData) -> GameMetadata {
        let rating = self.assign_basic_rating(&steam_data.name, &steam_data.genres.iter().map(|g| g.description.clone()).collect::<Vec<_>>());
        
        GameMetadata {
            id: None,
            name: steam_data.name.clone(),
            igdb_id: None,
            cover_url: steam_data.header_image.clone(),
            cover_path: None,
            rating: Some(rating),
            rating_count: None,
            summary: steam_data.short_description.clone(),
            genres: steam_data.genres.iter().map(|g| g.description.clone()).collect(),
            platforms: vec!["PC".to_string()],
            release_date: steam_data.release_date.as_ref().map(|r| r.date.clone()),
            developer: steam_data.developers.clone(),
            publisher: steam_data.publishers.clone(),
            steam_id: steam_data.steam_appid,
            metacritic_score: None,
            last_updated: Some(Utc::now()),
        }
    }

    fn convert_gog_to_game_metadata(&self, gog_data: &GogProduct) -> GameMetadata {
        GameMetadata {
            id: None,
            name: gog_data.title.clone(),
            igdb_id: None,
            cover_url: gog_data.image.clone(),
            cover_path: None,
            rating: gog_data.rating,
            rating_count: None,
            summary: gog_data.description.clone(),
            genres: gog_data.genres.as_ref().map(|genres| genres.iter().map(|g| g.name.clone()).collect()).unwrap_or_default(),
            platforms: vec!["PC".to_string()],
            release_date: gog_data.release_date.clone(),
            developer: gog_data.developers.as_ref().map(|devs| devs.iter().map(|d| d.name.clone()).collect()).unwrap_or_default(),
            publisher: gog_data.publishers.as_ref().map(|pubs| pubs.iter().map(|p| p.name.clone()).collect()).unwrap_or_default(),
            steam_id: None,
            metacritic_score: None,
            last_updated: Some(Utc::now()),
        }
    }

    fn convert_rawg_to_game_metadata(&self, rawg_data: &RawgGameData) -> GameMetadata {
        GameMetadata {
            id: None,
            name: rawg_data.name.clone(),
            igdb_id: None,
            cover_url: rawg_data.background_image.clone(),
            cover_path: None,
            rating: rawg_data.rating,
            rating_count: rawg_data.ratings_count,
            summary: rawg_data.description_raw.clone(),
            genres: rawg_data.genres.iter().map(|g| g.name.clone()).collect(),
            platforms: rawg_data.platforms.iter().map(|p| p.platform.name.clone()).collect(),
            release_date: rawg_data.released.clone(),
            developer: rawg_data.developers.iter().map(|d| d.name.clone()).collect(),
            publisher: rawg_data.publishers.iter().map(|p| p.name.clone()).collect(),
            steam_id: None,
            metacritic_score: None,
            last_updated: Some(Utc::now()),
        }
    }

    fn convert_screenscraper_to_game_metadata(&self, screenscraper_data: &ScreenscraperGame) -> GameMetadata {
        let mut cover_url = None;
        if let Some(medias) = &screenscraper_data.medias {
            for media in medias {
                if media.r#type == "ss" && media.region.as_ref().map(|r| r == "us").unwrap_or(false) {
                    cover_url = media.url.clone();
                    break;
                }
            }
        }
        
        GameMetadata {
            id: None,
            name: screenscraper_data.nom.clone(),
            igdb_id: None,
            cover_url,
            cover_path: None,
            rating: None,
            rating_count: None,
            summary: screenscraper_data.synopsis.clone(),
            genres: screenscraper_data.genre.as_ref().map(|g| vec![g.clone()]).unwrap_or_default(),
            platforms: vec!["PC".to_string()],
            release_date: screenscraper_data.dates.as_ref().and_then(|d| d.us.clone()),
            developer: screenscraper_data.developpeur.as_ref().map(|d| vec![d.clone()]).unwrap_or_default(),
            publisher: screenscraper_data.editeur.as_ref().map(|p| vec![p.clone()]).unwrap_or_default(),
            steam_id: None,
            metacritic_score: None,
            last_updated: Some(Utc::now()),
        }
    }

    async fn create_basic_metadata(&self, game_name: &str) -> Result<GameMetadata> {
        let cover_path = self.create_placeholder_cover(game_name).await?;
        
        Ok(GameMetadata {
            id: None,
            name: game_name.to_string(),
            igdb_id: None,
            cover_url: None,
            cover_path,
            rating: None,
            rating_count: None,
            summary: Some(format!("Game: {}\n\nNo detailed information available. Install API credentials to get full metadata.", game_name)),
            genres: Vec::new(),
            platforms: vec!["PC".to_string()],
            release_date: None,
            developer: Vec::new(),
            publisher: Vec::new(),
            steam_id: None,
            metacritic_score: None,
            last_updated: Some(Utc::now()),
        })
    }

    fn store_game_metadata(&self, metadata: &GameMetadata) -> Result<()> {
        let conn = Connection::open(&self.db_path)?;
        
        conn.execute(
            "INSERT OR REPLACE INTO games 
            (name, igdb_id, cover_url, cover_path, rating, rating_count, summary,
             genres, platforms, release_date, developer, publisher, steam_id,
             metacritic_score, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                &metadata.name,
                metadata.igdb_id,
                metadata.cover_url.as_ref(),
                metadata.cover_path.as_ref(),
                metadata.rating,
                metadata.rating_count,
                metadata.summary.as_ref(),
                serde_json::to_string(&metadata.genres)?,
                serde_json::to_string(&metadata.platforms)?,
                metadata.release_date.as_ref(),
                serde_json::to_string(&metadata.developer)?,
                serde_json::to_string(&metadata.publisher)?,
                metadata.steam_id,
                metadata.metacritic_score,
                metadata.last_updated,
            ),
        )?;
        
        Ok(())
    }

    async fn get_game_metadata(&self, game_name: &str) -> Result<Option<GameMetadata>> {
        // Check if we already have this game in the database
        let conn = Connection::open(&self.db_path)?;
        let mut stmt = conn.prepare("SELECT * FROM games WHERE name = ?")?;
        let mut rows = stmt.query([game_name])?;
        
        if let Some(row) = rows.next()? {
            // Return existing metadata
            return Ok(Some(self.row_to_metadata(row)?));
        }
        
        // Download new metadata
        if let Some(mut metadata) = self.search_game(game_name).await? {
            // Download cover art if available
            if let Some(cover_url) = &metadata.cover_url {
                if let Some(cover_path) = self.download_cover_art(cover_url, game_name).await? {
                    metadata.cover_path = Some(cover_path);
                }
            }
            
            // Store in database
            self.store_game_metadata(&metadata)?;
            
            Ok(Some(metadata))
        } else {
            Ok(None)
        }
    }

    fn row_to_metadata(&self, row: &rusqlite::Row) -> Result<GameMetadata> {
        Ok(GameMetadata {
            id: row.get(0)?,
            name: row.get(1)?,
            igdb_id: row.get(2)?,
            cover_url: row.get(3)?,
            cover_path: row.get(4)?,
            rating: row.get(5)?,
            rating_count: row.get(6)?,
            summary: row.get(7)?,
            genres: serde_json::from_str(&row.get::<_, String>(8)?)?,
            platforms: serde_json::from_str(&row.get::<_, String>(9)?)?,
            release_date: row.get(10)?,
            developer: serde_json::from_str(&row.get::<_, String>(11)?)?,
            publisher: serde_json::from_str(&row.get::<_, String>(12)?)?,
            steam_id: row.get(13)?,
            metacritic_score: row.get(14)?,
            last_updated: row.get(15)?,
        })
    }

    async fn batch_download_metadata(&self, game_names: &[String]) -> Result<Vec<Option<GameMetadata>>> {
        let mut results = Vec::new();
        
        for (i, game_name) in game_names.iter().enumerate() {
            info!("Processing {}/{}: {}", i + 1, game_names.len(), game_name);
            
            match self.get_game_metadata(game_name).await {
                Ok(metadata) => results.push(metadata),
                Err(e) => {
                    error!("Error processing {}: {}", game_name, e);
                    results.push(None);
                }
            }
            
            // Rate limiting
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        }
        
        Ok(results)
    }

    async fn run(&mut self, args: Args) -> Result<()> {
        if args.verbose {
            tracing_subscriber::fmt::init();
        }

        // Create directories
        tokio::fs::create_dir_all(&self.metadata_dir).await?;
        tokio::fs::create_dir_all(&self.covers_dir).await?;
        
        // Initialize database
        self.init_database()?;

        if let Some(game_name) = args.game {
            // Single game mode
            if let Some(metadata) = self.get_game_metadata(&game_name).await? {
                println!("Game: {}", metadata.name);
                println!("Rating: {:?}", metadata.rating);
                println!("Genres: {}", metadata.genres.join(", "));
                println!("Cover: {:?}", metadata.cover_path);
            } else {
                println!("Failed to get metadata for: {}", game_name);
            }
        } else {
            // Test with a few games
            let test_games = vec![
                "SkyrimSE".to_string(),
                "Stardew Valley".to_string(),
                "Elden Ring".to_string(),
                "The Witcher 3".to_string(),
            ];
            
            println!("Testing metadata downloader...");
            let results = self.batch_download_metadata(&test_games).await?;
            
            for result in results {
                if let Some(metadata) = result {
                    println!("\nGame: {}", metadata.name);
                    println!("Rating: {:?}", metadata.rating);
                    println!("Genres: {}", metadata.genres.join(", "));
                    println!("Cover: {:?}", metadata.cover_path);
                } else {
                    println!("Failed to get metadata");
                }
            }
        }

        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let mut downloader = GameMetadataDownloader::new(
        args.db_path.clone(),
        args.metadata_dir.clone(),
        args.covers_dir.clone(),
        args.igdb_key.clone(),
        args.screenscraper_user.clone(),
        args.screenscraper_pass.clone(),
        args.rawg_key.clone(),
    );
    downloader.run(args).await
}
