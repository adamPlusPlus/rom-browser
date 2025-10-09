use anyhow::Result;
use clap::Parser;
use rom_browser_scripts::{
    Config, DirectoryItem, GameInfo, PlatformInfo, get_platform_mappings,
};
use std::collections::HashMap;
use std::path::PathBuf;
use tracing::{info, warn, error};

/// ROM Browser - Interactive CLI browser for ROM archives
/// Supports multiple ROM sources including Myrient.erista.me
#[derive(Parser)]
#[command(name = "rom-browser")]
#[command(about = "Interactive CLI browser for ROM archives")]
struct Args {
    /// Dataset to use (redump or no-intro)
    #[arg(short, long, default_value = "redump")]
    dataset: String,
    
    /// Platform to browse
    #[arg(short, long)]
    platform: Option<String>,
    
    /// Starting path within platform
    #[arg(short, long)]
    path: Option<String>,
    
    /// Output format (json, csv, html, markdown)
    #[arg(short, long, default_value = "json")]
    format: String,
    
    /// Maximum number of items to display
    #[arg(short, long, default_value = "100")]
    limit: usize,
    
    /// Search query
    #[arg(short, long)]
    search: Option<String>,
    
    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

struct ROMBrowser {
    config: Config,
    current_url: String,
    current_platform: String,
    current_path: String,
    platforms: HashMap<String, String>,
}

impl ROMBrowser {
    fn new() -> Self {
        Self {
            config: Config::default(),
            current_url: String::new(),
            current_platform: String::new(),
            current_path: String::new(),
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

    async fn download_index(&self, url: &str) -> Result<String> {
        let client = reqwest::Client::new();
        let response = client
            .get(url)
            .header("User-Agent", "Mozilla/5.0 (ROM Browser CLI)")
            .send()
            .await?;

        let content = response.text().await?;
        let index_file = self.config.temp_dir.join("index.html");
        
        tokio::fs::create_dir_all(&self.config.temp_dir).await?;
        tokio::fs::write(&index_file, content).await?;
        
        Ok(index_file.to_string_lossy().to_string())
    }

    fn parse_items_from_index(&self, index_file: &str) -> Result<Vec<DirectoryItem>> {
        let content = std::fs::read_to_string(index_file)?;
        let mut items = Vec::new();

        // Parse directories
        let dir_pattern = regex::Regex::new(r#"href="([^"]+/)"#)?;
        for cap in dir_pattern.captures_iter(&content) {
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
        let file_pattern = regex::Regex::new(r#"href="([^"]+\.(?:zip|7z))""#)?;
        for cap in file_pattern.captures_iter(&content) {
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

    async fn get_platforms(&mut self) -> Result<Vec<PlatformInfo>> {
        let files_url = "https://myrient.erista.me/files/";
        let index_file = self.download_index(files_url).await?;
        let items = self.parse_items_from_index(&index_file)?;

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

    async fn browse_platform(&mut self, platform_id: &str, path: Option<&str>) -> Result<Vec<GameInfo>> {
        // First get the platform list to find the correct URL
        let files_url = "https://myrient.erista.me/files/";
        let files_index = self.download_index(files_url).await?;
        let files_items = self.parse_items_from_index(&files_index)?;

        let mut platform_url = None;
        let mut platform_name = None;

        // Find the platform by ID or name
        for item in files_items {
            if item.item_type == "directory" {
                let encoded_id = self.url_encode(&item.name);
                if encoded_id == platform_id || item.name == platform_id {
                    platform_name = Some(item.name);
                    platform_url = Some(format!("{}{}", files_url, item.href));
                    break;
                }
            }
        }

        let platform_url = platform_url.ok_or_else(|| anyhow::anyhow!("Platform not found: {}", platform_id))?;
        let platform_name = platform_name.ok_or_else(|| anyhow::anyhow!("Platform not found: {}", platform_id))?;

        // Build the target URL
        let target_url = if let Some(path) = path {
            format!("{}{}/", platform_url, path)
        } else {
            platform_url
        };

        // Browse the directory
        let directory_index = self.download_index(&target_url).await?;
        let directory_items = self.parse_items_from_index(&directory_index)?;

        let mut games = Vec::new();
        for item in directory_items {
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

    async fn search_platforms(&self, query: &str) -> Result<Vec<PlatformInfo>> {
        let mut platforms = Vec::new();

        // Search Redump
        let redump_url = "https://myrient.erista.me/files/Redump/";
        let redump_index = self.download_index(redump_url).await?;
        let redump_items = self.parse_items_from_index(&redump_index)?;

        for item in redump_items {
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
        let nointro_index = self.download_index(nointro_url).await?;
        let nointro_items = self.parse_items_from_index(&nointro_index)?;

        for item in nointro_items {
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

    fn print_platforms(&self, platforms: &[PlatformInfo], limit: usize) {
        println!("Available Platforms:");
        for (i, platform) in platforms.iter().take(limit).enumerate() {
            println!("{:2}. {} ({})", i + 1, platform.name, platform.dataset);
        }
    }

    fn print_games(&self, games: &[GameInfo], limit: usize) {
        println!("Games:");
        for (i, game) in games.iter().take(limit).enumerate() {
            let item_type = if game.is_directory.unwrap_or(false) { "D" } else { "F" };
            println!("{:2}. [{}] {}", i + 1, item_type, game.name);
        }
    }

    async fn interactive_mode(&mut self) -> Result<()> {
        println!("ROM Browser - Interactive Mode");
        println!("=============================");

        // Get platforms
        let platforms = self.get_platforms().await?;
        self.print_platforms(&platforms, 50);

        println!("\nEnter platform number or name (or 'q' to quit):");
        let mut input = String::new();
        std::io::stdin().read_line(&mut input)?;
        let input = input.trim();

        if input == "q" {
            return Ok(());
        }

        let platform = if let Ok(num) = input.parse::<usize>() {
            if num > 0 && num <= platforms.len() {
                &platforms[num - 1]
            } else {
                println!("Invalid platform number");
                return Ok(());
            }
        } else {
            platforms.iter().find(|p| p.name.to_lowercase().contains(&input.to_lowercase()))
                .ok_or_else(|| anyhow::anyhow!("Platform not found"))?
        };

        println!("Selected platform: {}", platform.name);

        // Browse platform
        let games = self.browse_platform(&platform.id, None).await?;
        self.print_games(&games, 50);

        Ok(())
    }

    async fn run(&mut self, args: Args) -> Result<()> {
        if args.verbose {
            tracing_subscriber::fmt::init();
        }

        // Set current URL based on dataset
        self.current_url = match args.dataset.as_str() {
            "redump" => self.config.base_url_redump.clone(),
            "no-intro" => self.config.base_url_no_intro.clone(),
            _ => {
                warn!("Unknown dataset: {}, defaulting to redump", args.dataset);
                self.config.base_url_redump.clone()
            }
        };

        if let Some(search) = args.search {
            // Search mode
            let platforms = self.search_platforms(&search).await?;
            match args.format.as_str() {
                "json" => println!("{}", serde_json::to_string_pretty(&platforms)?),
                _ => self.print_platforms(&platforms, args.limit),
            }
        } else if let Some(platform) = args.platform {
            // Browse specific platform
            let games = self.browse_platform(&platform, args.path.as_deref()).await?;
            match args.format.as_str() {
                "json" => println!("{}", serde_json::to_string_pretty(&games)?),
                _ => self.print_games(&games, args.limit),
            }
        } else {
            // Interactive mode
            self.interactive_mode().await?;
        }

        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let mut browser = ROMBrowser::new();
    browser.run(args).await
}
