use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

/// Configuration for ROM browser scripts
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub base_url_redump: String,
    pub base_url_no_intro: String,
    pub temp_dir: PathBuf,
    pub downloads_dir: PathBuf,
    pub log_file: PathBuf,
    pub queue_file: PathBuf,
    pub page_size: usize,
    pub filter_file: PathBuf,
    pub history_file: PathBuf,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            base_url_redump: "https://myrient.erista.me/files/Redump/".to_string(),
            base_url_no_intro: "https://myrient.erista.me/files/No-Intro/".to_string(),
            temp_dir: PathBuf::from("./temp"),
            downloads_dir: PathBuf::from("../downloads"),
            log_file: PathBuf::from("./rom-browse.log"),
            queue_file: PathBuf::from("./download_queue"),
            page_size: 50,
            filter_file: PathBuf::from("../config/rom-filter.txt"),
            history_file: PathBuf::from("./rom-browse-history.txt"),
        }
    }
}

/// Game metadata structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameMetadata {
    pub id: Option<i64>,
    pub name: String,
    pub igdb_id: Option<i64>,
    pub cover_url: Option<String>,
    pub cover_path: Option<String>,
    pub rating: Option<f64>,
    pub rating_count: Option<i64>,
    pub summary: Option<String>,
    pub genres: Vec<String>,
    pub platforms: Vec<String>,
    pub release_date: Option<String>,
    pub developer: Vec<String>,
    pub publisher: Vec<String>,
    pub steam_id: Option<i64>,
    pub metacritic_score: Option<i64>,
    pub last_updated: Option<chrono::DateTime<chrono::Utc>>,
}

/// Platform information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlatformInfo {
    pub id: String,
    pub name: String,
    pub dataset: String,
}

/// Game information for browsing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameInfo {
    pub name: String,
    pub platform: String,
    pub size: Option<String>,
    pub url: Option<String>,
    pub cover_art: Option<String>,
    pub rating: Option<f64>,
    pub summary: Option<String>,
    pub genres: Option<String>,
    pub release_date: Option<String>,
    pub is_favorite: Option<bool>,
    pub is_downloaded: Option<bool>,
    pub is_directory: Option<bool>,
    pub path: Option<String>,
}

/// Settings data structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SettingsData {
    pub rom_directories: Vec<String>,
    pub download_directory: String,
    pub metadata_api_key: String,
    pub auto_scan: bool,
    pub scan_interval: u32,
    pub max_concurrent_downloads: u32,
}

/// Directory item for browsing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DirectoryItem {
    pub name: String,
    pub href: String,
    pub item_type: String, // "directory" or "file"
    pub size: Option<String>,
}

/// Download progress information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DownloadProgress {
    pub filename: String,
    pub downloaded_bytes: u64,
    pub total_bytes: Option<u64>,
    pub percentage: f64,
    pub speed_bytes_per_sec: u64,
}

/// API response structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SteamGameData {
    pub steam_appid: Option<i64>,
    pub name: String,
    pub header_image: Option<String>,
    pub short_description: Option<String>,
    pub genres: Vec<SteamGenre>,
    pub release_date: Option<SteamReleaseDate>,
    pub developers: Vec<String>,
    pub publishers: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SteamGenre {
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SteamReleaseDate {
    pub date: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawgGameData {
    pub id: i64,
    pub name: String,
    pub background_image: Option<String>,
    pub rating: Option<f64>,
    pub ratings_count: Option<i64>,
    pub description_raw: Option<String>,
    pub genres: Vec<RawgGenre>,
    pub platforms: Vec<RawgPlatform>,
    pub released: Option<String>,
    pub developers: Vec<RawgDeveloper>,
    pub publishers: Vec<RawgPublisher>,
    pub short_screenshots: Vec<RawgScreenshot>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawgGenre {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawgPlatform {
    pub platform: RawgPlatformInfo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawgPlatformInfo {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawgDeveloper {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawgPublisher {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RawgScreenshot {
    pub image: String,
}

/// Screenscraper API structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenscraperResponse {
    pub response: ScreenscraperData,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenscraperData {
    pub jeux: Option<Vec<ScreenscraperGame>>,
    pub jeu: Option<ScreenscraperGame>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenscraperGame {
    pub id: i64,
    pub nom: String,
    pub synopsis: Option<String>,
    pub genre: Option<String>,
    pub developpeur: Option<String>,
    pub editeur: Option<String>,
    pub dates: Option<ScreenscraperDates>,
    pub medias: Option<Vec<ScreenscraperMedia>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenscraperDates {
    pub us: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenscraperMedia {
    pub r#type: String,
    pub region: Option<String>,
    pub url: Option<String>,
}

/// GOG API structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GogProduct {
    pub id: i64,
    pub title: String,
    pub description: Option<String>,
    pub image: Option<String>,
    pub gallery: Option<Vec<String>>,
    pub rating: Option<f64>,
    pub genres: Option<Vec<GogGenre>>,
    pub developers: Option<Vec<GogDeveloper>>,
    pub publishers: Option<Vec<GogPublisher>>,
    pub release_date: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GogGenre {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GogDeveloper {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GogPublisher {
    pub name: String,
}

/// Platform mappings
pub fn get_platform_mappings() -> HashMap<String, String> {
    let mut platforms = HashMap::new();
    
    platforms.insert("Nintendo - Nintendo Entertainment System".to_string(), "NES".to_string());
    platforms.insert("Nintendo - Super Nintendo Entertainment System".to_string(), "SNES".to_string());
    platforms.insert("Nintendo - Nintendo 64".to_string(), "N64".to_string());
    platforms.insert("Nintendo - Nintendo GameCube".to_string(), "NGC".to_string());
    platforms.insert("Nintendo - Nintendo Wii".to_string(), "WII".to_string());
    platforms.insert("Nintendo - Nintendo Wii U".to_string(), "WIIU".to_string());
    platforms.insert("Nintendo - Nintendo Switch".to_string(), "NSW".to_string());
    platforms.insert("Sony - PlayStation".to_string(), "PS1".to_string());
    platforms.insert("Sony - PlayStation 2".to_string(), "PS2".to_string());
    platforms.insert("Sony - PlayStation 3".to_string(), "PS3".to_string());
    platforms.insert("Sony - PlayStation 4".to_string(), "PS4".to_string());
    platforms.insert("Sony - PlayStation 5".to_string(), "PS5".to_string());
    platforms.insert("Sony - PlayStation Portable".to_string(), "PSP".to_string());
    platforms.insert("Sony - PlayStation Vita".to_string(), "PSV".to_string());
    platforms.insert("Microsoft - Xbox".to_string(), "XBOX".to_string());
    platforms.insert("Microsoft - Xbox 360".to_string(), "X360".to_string());
    platforms.insert("Microsoft - Xbox One".to_string(), "XONE".to_string());
    platforms.insert("Microsoft - Xbox Series X|S".to_string(), "XSX".to_string());
    platforms.insert("Sega - Master System".to_string(), "SMS".to_string());
    platforms.insert("Sega - Mega Drive - Genesis".to_string(), "MD".to_string());
    platforms.insert("Sega - Sega CD".to_string(), "SCD".to_string());
    platforms.insert("Sega - Sega 32X".to_string(), "32X".to_string());
    platforms.insert("Sega - Sega Saturn".to_string(), "SAT".to_string());
    platforms.insert("Sega - Dreamcast".to_string(), "DC".to_string());
    platforms.insert("Atari - 2600".to_string(), "A2600".to_string());
    platforms.insert("Atari - 5200".to_string(), "A5200".to_string());
    platforms.insert("Atari - 7800".to_string(), "A7800".to_string());
    platforms.insert("Atari - Jaguar".to_string(), "JAG".to_string());
    platforms.insert("Atari - Lynx".to_string(), "LYNX".to_string());
    platforms.insert("NEC - PC Engine - TurboGrafx-16".to_string(), "PCE".to_string());
    platforms.insert("NEC - PC Engine CD - TurboGrafx-CD".to_string(), "PCE-CD".to_string());
    platforms.insert("NEC - PC Engine SuperGrafx".to_string(), "SGX".to_string());
    platforms.insert("NEC - PC-FX".to_string(), "PCFX".to_string());
    platforms.insert("SNK - Neo Geo".to_string(), "NEO".to_string());
    platforms.insert("SNK - Neo Geo CD".to_string(), "NGCD".to_string());
    platforms.insert("SNK - Neo Geo Pocket".to_string(), "NGP".to_string());
    platforms.insert("SNK - Neo Geo Pocket Color".to_string(), "NGPC".to_string());
    platforms.insert("Bandai - WonderSwan".to_string(), "WS".to_string());
    platforms.insert("Bandai - WonderSwan Color".to_string(), "WSC".to_string());
    platforms.insert("Commodore - Amiga".to_string(), "AMIGA".to_string());
    platforms.insert("Commodore - Commodore 64".to_string(), "C64".to_string());
    platforms.insert("Commodore - Amiga CD32".to_string(), "CD32".to_string());
    platforms.insert("Apple - Apple II".to_string(), "APPLE2".to_string());
    platforms.insert("Apple - Macintosh".to_string(), "MAC".to_string());
    platforms.insert("IBM - PC".to_string(), "PC".to_string());
    platforms.insert("IBM - PC DOS".to_string(), "DOS".to_string());
    platforms.insert("IBM - PC Windows".to_string(), "WIN".to_string());
    platforms.insert("IBM - PC Linux".to_string(), "LINUX".to_string());
    platforms.insert("IBM - PC macOS".to_string(), "MACOS".to_string());
    platforms.insert("IBM - PC Android".to_string(), "ANDROID".to_string());
    platforms.insert("IBM - PC iOS".to_string(), "IOS".to_string());
    platforms.insert("IBM - PC Web".to_string(), "WEB".to_string());
    platforms.insert("IBM - PC VR".to_string(), "VR".to_string());
    platforms.insert("IBM - PC AR".to_string(), "AR".to_string());
    platforms.insert("IBM - PC Cloud".to_string(), "CLOUD".to_string());
    platforms.insert("IBM - PC Mobile".to_string(), "MOBILE".to_string());
    platforms.insert("IBM - PC Handheld".to_string(), "HANDHELD".to_string());
    platforms.insert("IBM - PC Console".to_string(), "CONSOLE".to_string());
    platforms.insert("IBM - PC Arcade".to_string(), "ARCADE".to_string());
    platforms.insert("IBM - PC Pinball".to_string(), "PINBALL".to_string());
    platforms.insert("IBM - PC Casino".to_string(), "CASINO".to_string());
    platforms.insert("IBM - PC Educational".to_string(), "EDU".to_string());
    platforms.insert("IBM - PC Sports".to_string(), "SPORTS".to_string());
    platforms.insert("IBM - PC Racing".to_string(), "RACING".to_string());
    platforms.insert("IBM - PC Fighting".to_string(), "FIGHTING".to_string());
    platforms.insert("IBM - PC Shooter".to_string(), "SHOOTER".to_string());
    platforms.insert("IBM - PC Adventure".to_string(), "ADV".to_string());
    platforms.insert("IBM - PC RPG".to_string(), "RPG".to_string());
    platforms.insert("IBM - PC Strategy".to_string(), "STRAT".to_string());
    platforms.insert("IBM - PC Simulation".to_string(), "SIM".to_string());
    platforms.insert("IBM - PC Puzzle".to_string(), "PUZZLE".to_string());
    platforms.insert("IBM - PC Platformer".to_string(), "PLAT".to_string());
    platforms.insert("IBM - PC Action".to_string(), "ACTION".to_string());
    platforms.insert("IBM - PC Horror".to_string(), "HORROR".to_string());
    platforms.insert("IBM - PC Comedy".to_string(), "COMEDY".to_string());
    platforms.insert("IBM - PC Drama".to_string(), "DRAMA".to_string());
    platforms.insert("IBM - PC Sci-Fi".to_string(), "SCIFI".to_string());
    platforms.insert("IBM - PC Fantasy".to_string(), "FANTASY".to_string());
    platforms.insert("IBM - PC Historical".to_string(), "HIST".to_string());
    platforms.insert("IBM - PC Military".to_string(), "MIL".to_string());
    platforms.insert("IBM - PC Western".to_string(), "WESTERN".to_string());
    platforms.insert("IBM - PC Crime".to_string(), "CRIME".to_string());
    platforms.insert("IBM - PC Mystery".to_string(), "MYSTERY".to_string());
    platforms.insert("IBM - PC Thriller".to_string(), "THRILLER".to_string());
    platforms.insert("IBM - PC Romance".to_string(), "ROMANCE".to_string());
    platforms.insert("IBM - PC Musical".to_string(), "MUSICAL".to_string());
    platforms.insert("IBM - PC Documentary".to_string(), "DOC".to_string());
    platforms.insert("IBM - PC Animation".to_string(), "ANIM".to_string());
    platforms.insert("IBM - PC Family".to_string(), "FAMILY".to_string());
    platforms.insert("IBM - PC Children".to_string(), "CHILDREN".to_string());
    platforms.insert("IBM - PC Teen".to_string(), "TEEN".to_string());
    platforms.insert("IBM - PC Adult".to_string(), "ADULT".to_string());
    platforms.insert("IBM - PC Mature".to_string(), "MATURE".to_string());
    platforms.insert("IBM - PC Everyone".to_string(), "EVERYONE".to_string());
    platforms.insert("IBM - PC Everyone 10+".to_string(), "E10+".to_string());
    platforms.insert("IBM - PC Teen 13+".to_string(), "T13+".to_string());
    platforms.insert("IBM - PC Mature 17+".to_string(), "M17+".to_string());
    platforms.insert("IBM - PC Adults Only 18+".to_string(), "AO18+".to_string());
    platforms.insert("IBM - PC Rating Pending".to_string(), "RP".to_string());
    platforms.insert("IBM - PC Not Rated".to_string(), "NR".to_string());
    platforms.insert("IBM - PC Unrated".to_string(), "UR".to_string());
    platforms.insert("IBM - PC Unknown".to_string(), "UNK".to_string());
    platforms.insert("IBM - PC Other".to_string(), "OTHER".to_string());
    
    platforms
}

/// Popular games with their ratings for heuristic scoring
pub fn get_popular_games_ratings() -> HashMap<String, f64> {
    let mut ratings = HashMap::new();
    
    ratings.insert("witcher".to_string(), 9.5);
    ratings.insert("skyrim".to_string(), 9.5);
    ratings.insert("fallout".to_string(), 9.0);
    ratings.insert("elder scrolls".to_string(), 9.0);
    ratings.insert("dark souls".to_string(), 9.0);
    ratings.insert("bloodborne".to_string(), 9.5);
    ratings.insert("sekiro".to_string(), 9.0);
    ratings.insert("zelda".to_string(), 9.5);
    ratings.insert("mario".to_string(), 9.0);
    ratings.insert("pokemon".to_string(), 8.5);
    ratings.insert("halo".to_string(), 8.5);
    ratings.insert("gears".to_string(), 8.0);
    ratings.insert("mass effect".to_string(), 9.0);
    ratings.insert("dragon age".to_string(), 8.5);
    ratings.insert("bioshock".to_string(), 9.0);
    ratings.insert("portal".to_string(), 9.5);
    ratings.insert("half-life".to_string(), 9.5);
    ratings.insert("counter-strike".to_string(), 8.5);
    ratings.insert("dota".to_string(), 8.5);
    ratings.insert("league of legends".to_string(), 8.0);
    ratings.insert("world of warcraft".to_string(), 8.5);
    ratings.insert("minecraft".to_string(), 8.5);
    ratings.insert("terraria".to_string(), 8.5);
    ratings.insert("stardew valley".to_string(), 8.5);
    ratings.insert("civilization".to_string(), 8.5);
    ratings.insert("total war".to_string(), 8.0);
    ratings.insert("xcom".to_string(), 8.5);
    ratings.insert("doom".to_string(), 8.5);
    ratings.insert("quake".to_string(), 8.0);
    ratings.insert("wolfenstein".to_string(), 8.0);
    ratings.insert("tomb raider".to_string(), 8.0);
    ratings.insert("uncharted".to_string(), 8.5);
    ratings.insert("god of war".to_string(), 9.0);
    ratings.insert("spider-man".to_string(), 8.5);
    ratings.insert("batman".to_string(), 8.5);
    ratings.insert("assassin".to_string(), 8.0);
    ratings.insert("call of duty".to_string(), 7.5);
    ratings.insert("battlefield".to_string(), 7.5);
    ratings.insert("fifa".to_string(), 7.0);
    ratings.insert("nba".to_string(), 7.0);
    ratings.insert("madden".to_string(), 7.0);
    ratings.insert("nhl".to_string(), 7.0);
    
    ratings
}

/// Common suffixes to remove from game names
pub fn get_game_name_suffixes() -> Vec<&'static str> {
    vec![
        " (ModEngine)",
        " (Protected)",
        " (MCC Launcher)",
        " (Startup)",
        " (Pre-Launcher)",
        " (Mod - Armoredcore6)",
        " (Mod - Darksouls3)",
        " (Mod - Eldenring)",
        " (PS2)",
        " (PSX)",
        " (N64)",
        " (GameCube)",
        " (Wii)",
        " (Dreamcast)",
        " (Genesis)",
        " (SNES)",
        " (NES)",
        " (GBA)",
        " (NDS)",
        " (PSP)",
        " (MAME)",
        " (C64)",
        " (Amiga)",
        " (Atari2600)",
        "Launch ",
        " - ",
        ":",
        ";",
        "!",
        "?",
    ]
}
