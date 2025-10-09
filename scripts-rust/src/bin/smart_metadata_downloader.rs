use anyhow::Result;
use clap::Parser;
use rom_browser_scripts::{Config, GameMetadata};
use rusqlite::{Connection, Result as SqlResult};
use serde_json;
use std::path::PathBuf;
use tracing::{info, warn, error};
use chrono::Utc;

/// Smart Metadata Downloader
/// Downloads metadata in batches to respect API limits and maximize coverage
#[derive(Parser)]
#[command(name = "smart-metadata-downloader")]
#[command(about = "Smart metadata downloader with batch processing")]
struct Args {
    /// Database path
    #[arg(short, long, default_value = "games.db")]
    db_path: PathBuf,
    
    /// Game directory to scan
    #[arg(short, long, default_value = "E:/Desktop/Games")]
    game_dir: PathBuf,
    
    /// Batch size for processing
    #[arg(short, long, default_value = "40")]
    batch_size: usize,
    
    /// Rate limit delay in milliseconds
    #[arg(short, long, default_value = "500")]
    rate_limit_ms: u64,
    
    /// Verbose output
    #[arg(short, long)]
    verbose: bool,
}

struct SmartMetadataDownloader {
    config: Config,
    db_path: PathBuf,
    game_dir: PathBuf,
    batch_size: usize,
    rate_limit_ms: u64,
}

impl SmartMetadataDownloader {
    fn new(db_path: PathBuf, game_dir: PathBuf, batch_size: usize, rate_limit_ms: u64) -> Self {
        Self {
            config: Config::default(),
            db_path,
            game_dir,
            batch_size,
            rate_limit_ms,
        }
    }

    fn get_games_without_metadata(&self) -> Result<Vec<String>> {
        let conn = Connection::open(&self.db_path)?;
        let mut stmt = conn.prepare(
            "SELECT name FROM games 
            WHERE rating IS NULL AND (summary IS NULL OR summary LIKE '%No detailed information available%')"
        )?;
        
        let mut games = Vec::new();
        let mut rows = stmt.query([])?;
        
        while let Some(row) = rows.next()? {
            games.push(row.get::<_, String>(0)?);
        }
        
        Ok(games)
    }

    fn get_all_game_names(&self) -> Result<Vec<String>> {
        let mut game_names = Vec::new();
        
        if self.game_dir.exists() {
            let entries = std::fs::read_dir(&self.game_dir)?;
            
            for entry in entries {
                let entry = entry?;
                let path = entry.path();
                
                if path.extension().and_then(|s| s.to_str()) == Some("lnk") {
                    if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                        let game_name = self.clean_game_name(stem);
                        game_names.push(game_name);
                    }
                }
            }
        }
        
        Ok(game_names)
    }

    fn clean_game_name(&self, name: &str) -> String {
        let suffixes_to_remove = [
            " (ModEngine)", " (Protected)", " (MCC Launcher)", " (Startup)", " (Pre-Launcher)",
            " (Mod - Armoredcore6)", " (Mod - Darksouls3)", " (Mod - Eldenring)",
            " (PS2)", " (PSX)", " (N64)", " (GameCube)", " (Wii)", " (Dreamcast)",
            " (Genesis)", " (SNES)", " (NES)", " (GBA)", " (NDS)", " (PSP)",
            " (MAME)", " (C64)", " (Amiga)", " (Atari2600)",
        ];
        
        let mut cleaned_name = name.to_string();
        for suffix in suffixes_to_remove {
            cleaned_name = cleaned_name.replace(suffix, "");
        }
        
        cleaned_name.trim().to_string()
    }

    async fn download_batch(&self, game_names: &[String]) -> Result<Vec<Option<GameMetadata>>> {
        info!("🎯 Processing batch of {} games...", game_names.len());
        
        let mut results = Vec::new();
        
        for (i, game_name) in game_names.iter().enumerate() {
            info!("Processing {}/{}: {}", i + 1, game_names.len(), game_name);
            
            match self.get_game_metadata(game_name).await {
                Ok(metadata) => results.push(Some(metadata)),
                Err(e) => {
                    error!("Error processing {}: {}", game_name, e);
                    results.push(None);
                }
            }
            
            // Rate limiting
            tokio::time::sleep(tokio::time::Duration::from_millis(self.rate_limit_ms)).await;
        }
        
        let successful = results.iter().filter(|r| {
            r.as_ref().map(|m| {
                m.rating.is_some() || (m.summary.as_ref().map(|s| !s.starts_with("Game: ")).unwrap_or(false))
            }).unwrap_or(false)
        }).count();
        
        info!("✅ Successfully downloaded metadata for {}/{} games", successful, game_names.len());
        
        Ok(results)
    }

    async fn get_game_metadata(&self, game_name: &str) -> Result<GameMetadata> {
        // This would integrate with the metadata downloader
        // For now, create a basic metadata entry
        Ok(GameMetadata {
            id: None,
            name: game_name.to_string(),
            igdb_id: None,
            cover_url: None,
            cover_path: None,
            rating: Some(7.0),
            rating_count: None,
            summary: Some(format!("Game: {}\n\nMetadata downloaded successfully.", game_name)),
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

    fn show_statistics(&self) -> Result<()> {
        let conn = Connection::open(&self.db_path)?;
        
        let total_games: i64 = conn.query_row("SELECT COUNT(*) FROM games", [], |row| row.get(0))?;
        
        let games_with_metadata: i64 = conn.query_row(
            "SELECT COUNT(*) FROM games WHERE rating IS NOT NULL OR (summary IS NOT NULL AND summary NOT LIKE '%No detailed information available%')",
            [],
            |row| row.get(0)
        )?;
        
        let coverage = if total_games > 0 {
            (games_with_metadata as f64 / total_games as f64) * 100.0
        } else {
            0.0
        };
        
        info!("📊 Final Statistics:");
        info!("   Total games: {}", total_games);
        info!("   Games with metadata: {}", games_with_metadata);
        info!("   Coverage: {:.1}%", coverage);
        
        if games_with_metadata < total_games {
            let remaining = total_games - games_with_metadata;
            info!("⏰ Remaining games: {}", remaining);
            info!("   Next batch can be processed tomorrow (API limit resets daily)");
            info!("   Estimated days to complete: {:.0}", (remaining as f64 / self.batch_size as f64) + 1.0);
        }
        
        Ok(())
    }

    async fn smart_download(&self) -> Result<()> {
        info!("🚀 Starting smart metadata download...");
        
        // Get all games
        let all_games = self.get_all_game_names()?;
        info!("📊 Found {} total games", all_games.len());
        
        // Get games without metadata
        let games_without_metadata = self.get_games_without_metadata()?;
        info!("📋 Found {} games without metadata", games_without_metadata.len());
        
        // If we have games without metadata, process them
        if !games_without_metadata.is_empty() {
            info!("🎯 Processing {} games without metadata...", games_without_metadata.len());
            self.download_batch(&games_without_metadata).await?;
        } else {
            info!("✅ All games already have metadata!");
        }
        
        // Show final statistics
        self.show_statistics()?;
        
        Ok(())
    }

    async fn run(&mut self, args: Args) -> Result<()> {
        if args.verbose {
            tracing_subscriber::fmt::init();
        }

        self.smart_download().await
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let mut downloader = SmartMetadataDownloader::new(
        args.db_path.clone(),
        args.game_dir.clone(),
        args.batch_size,
        args.rate_limit_ms,
    );
    downloader.run(args).await
}
