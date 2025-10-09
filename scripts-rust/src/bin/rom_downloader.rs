use anyhow::Result;
use clap::Parser;
use rom_browser_scripts::{
    Config, DirectoryItem, GameInfo, PlatformInfo, get_platform_mappings,
    get_game_name_suffixes,
};
use std::collections::HashMap;
use std::path::PathBuf;
use tracing::{info, warn, error};
use indicatif::{ProgressBar, ProgressStyle};

/// ROM Batch Downloader
/// Downloads ROMs from ROM archives based on platform selection and download queue
#[derive(Parser)]
#[command(name = "rom-downloader")]
#[command(about = "Downloads ROMs from ROM archives")]
struct Args {
    /// Platform to download from
    #[arg(short, long)]
    platform: Option<String>,
    
    /// Subtype/path within platform
    #[arg(short, long)]
    subtype: Option<String>,
    
    /// Maximum number of files to download
    #[arg(short, long, default_value = "10")]
    max_files: usize,
    
    /// Download directory
    #[arg(short, long, default_value = "./downloads")]
    download_dir: PathBuf,
    
    /// Queue file path
    #[arg(short, long, default_value = "./download_queue")]
    queue_file: PathBuf,
    
    /// Dataset to use (redump or no-intro)
    #[arg(short, long, default_value = "redump")]
    dataset: String,
    
    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

struct ROMDownloader {
    config: Config,
    current_url: String,
    platforms: HashMap<String, String>,
    download_dir: PathBuf,
    queue_file: PathBuf,
}

impl ROMDownloader {
    fn new(download_dir: PathBuf, queue_file: PathBuf) -> Self {
        Self {
            config: Config::default(),
            current_url: String::new(),
            platforms: get_platform_mappings(),
            download_dir,
            queue_file,
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
            .header("User-Agent", "Mozilla/5.0 (ROM Downloader CLI)")
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

    async fn get_platforms(&self) -> Result<Vec<PlatformInfo>> {
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

    fn clean_title(&self, title: &str) -> String {
        let mut clean_title = title.to_string();
        
        // Remove common suffixes
        for suffix in get_game_name_suffixes() {
            clean_title = clean_title.replace(suffix, " ");
        }
        
        // Remove extra whitespace
        clean_title = clean_title.split_whitespace().collect::<Vec<&str>>().join(" ");
        
        clean_title
    }

    fn search_game(&self, game_title: &str, index_file: &str) -> Result<Vec<String>> {
        let content = std::fs::read_to_string(index_file)?;
        let clean_title = self.clean_title(game_title);
        
        // Create multiple search patterns for better matching
        let search_patterns = vec![
            regex::escape(&clean_title),
            clean_title.replace(' ', ".*"),
            regex::Regex::new(r"[^a-zA-Z0-9]")?.replace_all(&clean_title, ".*").to_string(),
            format!(".*{}.*", regex::escape(&clean_title)),
        ];
        
        let mut matches = Vec::new();
        for pattern in search_patterns {
            let file_pattern = regex::Regex::new(r#"href="([^"]*\.(?:zip|7z))""#)?;
            for cap in file_pattern.captures_iter(&content) {
                let href = &cap[1];
                if regex::Regex::new(&pattern)?.is_match(href) {
                    matches.push(href.to_string());
                }
            }
            if !matches.is_empty() {
                break;
            }
        }
        
        Ok(matches)
    }

    fn select_best_match(&self, game_title: &str, matches: &[String]) -> Option<String> {
        if matches.is_empty() {
            return None;
        }

        let mut best_match = None;
        let mut best_score = 0;

        for match_href in matches {
            let filename = self.url_decode(match_href);
            let clean_filename = filename.replace(".zip", "").replace(".7z", "");
            
            // Simple scoring based on word overlap
            let mut score = 0;
            let game_title_lower = game_title.to_lowercase();
            let filename_lower = clean_filename.to_lowercase();
            let game_words: std::collections::HashSet<&str> = game_title_lower.split_whitespace().collect();
            let filename_words: std::collections::HashSet<&str> = filename_lower.split_whitespace().collect();
            
            // Count word matches
            for word in &game_words {
                if filename_words.contains(word) {
                    score += 1;
                }
            }
            
            // Region preference scoring - prioritize USA versions
            if clean_filename.contains("(USA)") || clean_filename.contains("(US)") {
                score += 10;
            } else if clean_filename.contains("(North America)") {
                score += 8;
            } else if clean_filename.contains("(Europe)") {
                score += 2;
            } else if clean_filename.contains("(Asia)") {
                score += 1;
            }
            
            // Language preference
            if clean_filename.contains("(En)") {
                score += 3;
            }
            
            if score > best_score {
                best_score = score;
                best_match = Some(match_href.clone());
            }
        }

        best_match
    }

    async fn download_file(&self, url: &str, filename: &str) -> Result<bool> {
        let download_path = self.download_dir.join(filename);
        
        // Check if file already exists
        if download_path.exists() {
            info!("File already exists, skipping download: {}", filename);
            return Ok(true);
        }

        let client = reqwest::Client::new();
        let response = client
            .get(url)
            .header("User-Agent", "Mozilla/5.0 (ROM Downloader CLI)")
            .send()
            .await?;

        let total_size = response.content_length().unwrap_or(0);
        let mut downloaded = 0u64;
        let mut stream = response.bytes_stream();

        let pb = ProgressBar::new(total_size);
        pb.set_style(ProgressStyle::default_bar()
            .template("{msg} {bar:40.cyan/blue} {bytes}/{total_bytes} ({eta})")
            .unwrap()
            .progress_chars("#>-"));

        pb.set_message(format!("Downloading {}", filename));

        let mut file = tokio::fs::File::create(&download_path).await?;

        use futures::StreamExt;
        while let Some(chunk) = stream.next().await {
            let chunk = chunk?;
            downloaded += chunk.len() as u64;
            pb.set_position(downloaded);
            
            use tokio::io::AsyncWriteExt;
            file.write_all(&chunk).await?;
        }

        pb.finish_with_message(format!("Downloaded {}", filename));
        info!("Successfully downloaded: {}", filename);
        Ok(true)
    }

    async fn download_game(&self, game_title: &str, filename: &str, platform_url: &str) -> Result<bool> {
        let download_url = format!("{}{}", platform_url, filename);
        
        info!("Downloading: {}", game_title);
        info!("Filename: {}", filename);
        info!("URL: {}", download_url);
        
        self.download_file(&download_url, filename).await
    }

    fn extract_games_from_queue(&self) -> Result<Vec<String>> {
        if !self.queue_file.exists() {
            return Ok(Vec::new());
        }

        let content = std::fs::read_to_string(&self.queue_file)?;
        let games: Vec<String> = content
            .lines()
            .filter(|line| !line.trim().is_empty() && !line.trim().starts_with('#'))
            .map(|line| line.trim().to_string())
            .collect();

        Ok(games)
    }

    fn remove_from_queue(&self, game_title: &str) -> Result<()> {
        if !self.queue_file.exists() {
            return Ok(());
        }

        let content = std::fs::read_to_string(&self.queue_file)?;
        let lines: Vec<&str> = content
            .lines()
            .filter(|line| !line.contains(game_title))
            .collect();

        std::fs::write(&self.queue_file, lines.join("\n"))?;
        info!("Removed '{}' from download queue", game_title);
        Ok(())
    }

    async fn interactive_browse_folders(&self, platform_name: &str) -> Result<Option<(String, String)>> {
        let platform_url = format!("{}{}/", self.current_url, self.url_encode(platform_name));
        let mut rel_path = String::new();
        
        loop {
            let current_url = format!("{}{}", platform_url, rel_path);
            let index_file = self.download_index(&current_url).await?;
            let items = self.parse_items_from_index(&index_file)?;

            // Get subdirectories
            let subdirs: Vec<&DirectoryItem> = items.iter().filter(|item| item.item_type == "directory").collect();
            
            if !subdirs.is_empty() {
                // Show subdirectories
                println!("Subdirectories:");
                for (i, subdir) in subdirs.iter().enumerate() {
                    println!("{:2}. {}", i + 1, subdir.name);
                }
                
                println!("Enter directory number (or '..' to go up, 'q' to quit):");
                let mut input = String::new();
                std::io::stdin().read_line(&mut input)?;
                let input = input.trim();
                
                if input == "q" {
                    return Ok(None);
                } else if input == ".." {
                    // Go up
                    rel_path = rel_path.trim_end_matches('/').to_string();
                    if let Some(last_slash) = rel_path.rfind('/') {
                        rel_path = rel_path[..last_slash + 1].to_string();
                    } else {
                        rel_path = String::new();
                    }
                    continue;
                } else if let Ok(num) = input.parse::<usize>() {
                    if num > 0 && num <= subdirs.len() {
                        let chosen = &subdirs[num - 1];
                        rel_path = format!("{}{}/", rel_path, chosen.href);
                        continue;
                    }
                }
            }

            // No subdirectories, look for files
            let files: Vec<&DirectoryItem> = items.iter().filter(|item| item.item_type == "file").collect();
            
            if files.is_empty() {
                warn!("No content found in this folder");
                return Ok(None);
            }

            println!("Files:");
            for (i, file) in files.iter().enumerate() {
                println!("{:2}. {}", i + 1, file.name);
            }
            
            println!("Enter file number (or '..' to go up, 'q' to quit):");
            let mut input = String::new();
            std::io::stdin().read_line(&mut input)?;
            let input = input.trim();
            
            if input == "q" {
                return Ok(None);
            } else if input == ".." {
                // Go up
                rel_path = rel_path.trim_end_matches('/').to_string();
                if let Some(last_slash) = rel_path.rfind('/') {
                    rel_path = rel_path[..last_slash + 1].to_string();
                } else {
                    rel_path = String::new();
                }
                continue;
            } else if let Ok(num) = input.parse::<usize>() {
                if num > 0 && num <= files.len() {
                    let chosen = &files[num - 1];
                    let title = chosen.name.replace(".zip", "").replace(".7z", "");
                    return Ok(Some((title, chosen.href.clone())));
                }
            }
        }
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

        // Create download directory
        tokio::fs::create_dir_all(&self.download_dir).await?;

        if let Some(platform) = args.platform {
            // Download specific platform
            let platform_url = format!("{}{}/", self.current_url, self.url_encode(&platform));
            
            if self.queue_file.exists() {
                // Process queue
                let games = self.extract_games_from_queue()?;
                let total_games = games.len();
                let mut successful_downloads = 0;
                let mut failed_downloads = 0;

                info!("Found {} games to process", total_games);

                for (current_game, game_title) in games.iter().enumerate() {
                    info!("[{}/{}] Processing: {}", current_game + 1, total_games, game_title);
                    
                    let clean_title = self.clean_title(game_title);
                    let index_file = self.download_index(&platform_url).await?;
                    let matches = self.search_game(&clean_title, &index_file)?;
                    
                    if let Some(best_match) = self.select_best_match(&clean_title, &matches) {
                        if self.download_game(game_title, &best_match, &platform_url).await? {
                            self.remove_from_queue(game_title)?;
                            successful_downloads += 1;
                            info!("✓ Completed: {}", game_title);
                        } else {
                            failed_downloads += 1;
                            error!("✗ Download failed: {}", game_title);
                        }
                    } else {
                        warn!("Could not find suitable match for: {}", game_title);
                        failed_downloads += 1;
                    }
                    
                    // Wait before next download to be respectful to the server
                    if current_game < total_games - 1 {
                        info!("Waiting 3 seconds before next download...");
                        tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
                    }
                }

                info!("Download session completed!");
                info!("Successful downloads: {}", successful_downloads);
                error!("Failed downloads: {}", failed_downloads);
            } else {
                // Interactive single game download
                if let Some((title, href)) = self.interactive_browse_folders(&platform).await? {
                    if self.download_game(&title, &href, &platform_url).await? {
                        info!("✓ Completed: {}", title);
                    } else {
                        error!("✗ Download failed: {}", title);
                    }
                } else {
                    info!("No title selected");
                }
            }
        } else {
            // Interactive platform selection
            let platforms = self.get_platforms().await?;
            println!("Available Platforms:");
            for (i, platform) in platforms.iter().enumerate() {
                println!("{:2}. {} ({})", i + 1, platform.name, platform.dataset);
            }
            
            println!("Enter platform number:");
            let mut input = String::new();
            std::io::stdin().read_line(&mut input)?;
            let input = input.trim();
            
            if let Ok(num) = input.parse::<usize>() {
                if num > 0 && num <= platforms.len() {
                    let platform = &platforms[num - 1];
                    let platform_url = format!("{}{}/", self.current_url, self.url_encode(&platform.name));
                    
                    if let Some((title, href)) = self.interactive_browse_folders(&platform.name).await? {
                        if self.download_game(&title, &href, &platform_url).await? {
                            info!("✓ Completed: {}", title);
                        } else {
                            error!("✗ Download failed: {}", title);
                        }
                    } else {
                        info!("No title selected");
                    }
                } else {
                    error!("Invalid platform number");
                }
            } else {
                error!("Invalid input");
            }
        }

        Ok(())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let mut downloader = ROMDownloader::new(args.download_dir.clone(), args.queue_file.clone());
    downloader.run(args).await
}
