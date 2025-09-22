#!/bin/bash

# PS2 Game Downloader Script v2
# Downloads games from remote archive based on download queue
# Usage: ./ps2_downloader_v2.sh

# Configuration
ARCHIVE_URL="https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%202/"
DOWNLOAD_DIR="./downloads"
QUEUE_FILE="./download_queue"
LOG_FILE="./download_log.txt"
TEMP_DIR="./temp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Create directories
mkdir -p "$DOWNLOAD_DIR"
mkdir -p "$TEMP_DIR"

# Initialize log file
echo "PS2 Download Session Started: $(date)" > "$LOG_FILE"

# Function to log messages
log_message() {
    local message="$1"
    echo -e "$message"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $message" >> "$LOG_FILE"
}

# Function to clean game title for search
clean_title() {
    local title="$1"
    # Remove common suffixes and clean up
    title=$(echo "$title" | sed 's/ - Missing.*$//')
    title=$(echo "$title" | sed 's/ (Note:.*$//')
    title=$(echo "$title" | sed 's/ - Missing$//')
    # Remove extra whitespace
    title=$(echo "$title" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    echo "$title"
}

# Function to download and parse archive index
download_archive_index() {
    local index_file="$TEMP_DIR/archive_index.html"
    
    log_message "${BLUE}Downloading archive index...${NC}"
    
    if curl -s -o "$index_file" "$ARCHIVE_URL"; then
        log_message "${GREEN}Archive index downloaded successfully${NC}"
        return 0
    else
        log_message "${RED}Failed to download archive index${NC}"
        return 1
    fi
}

# Function to search for game in archive
search_game() {
    local game_title="$1"
    local index_file="$TEMP_DIR/archive_index.html"
    
    log_message "${BLUE}Searching for: $game_title${NC}"
    
    # Create a more flexible search pattern
    local search_pattern=$(echo "$game_title" | sed 's/[[:space:]]\+/.*/g')
    
    # Search for the game in the archive index
    local matches=$(grep -i "$search_pattern" "$index_file" | grep -E 'href="[^"]*\.zip"' | head -10)
    
    if [ -n "$matches" ]; then
        log_message "${GREEN}Found $(echo "$matches" | wc -l) potential matches for: $game_title${NC}"
        echo "$matches"
        return 0
    else
        # Try alternative search patterns
        local alt_patterns=(
            "$(echo "$game_title" | sed 's/[[:space:]]\+/.*/g')"
            "$(echo "$game_title" | sed 's/[[:space:]]\+/.*/g' | sed 's/[^a-zA-Z0-9]/.*/g')"
            "$(echo "$game_title" | sed 's/[[:space:]]\+/.*/g' | sed 's/[^a-zA-Z0-9]/.*/g' | sed 's/.*/.*&.*/')"
        )
        
        for pattern in "${alt_patterns[@]}"; do
            matches=$(grep -i "$pattern" "$index_file" | grep -E 'href="[^"]*\.zip"' | head -5)
            if [ -n "$matches" ]; then
                log_message "${YELLOW}Found matches using alternative pattern for: $game_title${NC}"
                echo "$matches"
                return 0
            fi
        done
        
        log_message "${YELLOW}No matches found for: $game_title${NC}"
        return 1
    fi
}

# Function to select best match
select_best_match() {
    local game_title="$1"
    local matches="$2"
    
    # Score each match based on similarity
    local best_match=""
    local best_score=0
    
    while IFS= read -r match; do
        if [ -n "$match" ]; then
            local filename=$(echo "$match" | sed 's/.*href="\([^"]*\)".*/\1/')
            local clean_filename=$(echo "$filename" | sed 's/\.zip$//' | sed 's/%20/ /g' | sed 's/%28/(/g' | sed 's/%29/)/g')
            
            # Simple scoring based on word overlap
            local score=0
            local game_words=$(echo "$game_title" | tr '[:upper:]' '[:lower:]' | tr '[:space:]' '\n' | grep -v '^$')
            local filename_words=$(echo "$clean_filename" | tr '[:upper:]' '[:lower:]' | tr '[:space:]' '\n' | grep -v '^$')
            
            while IFS= read -r word; do
                if echo "$filename_words" | grep -q "^$word$"; then
                    score=$((score + 1))
                fi
            done <<< "$game_words"
            
            if [ $score -gt $best_score ]; then
                best_score=$score
                best_match="$filename"
            fi
        fi
    done <<< "$matches"
    
    echo "$best_match"
}

# Function to download game
download_game() {
    local game_title="$1"
    local filename="$2"
    local download_url="${ARCHIVE_URL}${filename}"
    
    log_message "${BLUE}Downloading: $game_title${NC}"
    log_message "Filename: $filename"
    log_message "URL: $download_url"
    
    # Check if file already exists
    if [ -f "$DOWNLOAD_DIR/$filename" ]; then
        log_message "${YELLOW}File already exists, skipping download: $filename${NC}"
        return 0
    fi
    
    # Download with progress bar and resume support
    if curl -L -C - -o "$DOWNLOAD_DIR/$filename" "$download_url" --progress-bar --retry 3 --retry-delay 5; then
        log_message "${GREEN}Successfully downloaded: $game_title${NC}"
        return 0
    else
        log_message "${RED}Failed to download: $game_title${NC}"
        # Remove partial download if it exists
        rm -f "$DOWNLOAD_DIR/$filename"
        return 1
    fi
}

# Function to extract game titles from queue file
extract_games() {
    local temp_file=$(mktemp)
    
    # Extract game titles, removing headers and notes
    grep -E '^[A-Za-z0-9].* - Missing' "$QUEUE_FILE" | \
    sed 's/ - Missing.*$//' | \
    sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | \
    grep -v '^$' > "$temp_file"
    
    echo "$temp_file"
}

# Function to remove completed game from queue
remove_from_queue() {
    local game_title="$1"
    local temp_file=$(mktemp)
    
    # Remove the line containing this game title
    grep -v "$game_title" "$QUEUE_FILE" > "$temp_file"
    mv "$temp_file" "$QUEUE_FILE"
    
    log_message "${GREEN}Removed '$game_title' from download queue${NC}"
}

# Function to cleanup temporary files
cleanup() {
    log_message "${BLUE}Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_DIR"
}

# Main execution
main() {
    log_message "${BLUE}Starting PS2 Game Downloader v2${NC}"
    log_message "Archive URL: $ARCHIVE_URL"
    log_message "Download Directory: $DOWNLOAD_DIR"
    
    # Check if queue file exists
    if [ ! -f "$QUEUE_FILE" ]; then
        log_message "${RED}Error: Queue file not found: $QUEUE_FILE${NC}"
        exit 1
    fi
    
    # Download archive index first
    if ! download_archive_index; then
        log_message "${RED}Failed to download archive index. Exiting.${NC}"
        exit 1
    fi
    
    # Extract game titles
    local games_file=$(extract_games)
    local total_games=$(wc -l < "$games_file")
    local current_game=0
    local successful_downloads=0
    local failed_downloads=0
    
    log_message "Found $total_games games to process"
    
    # Process each game
    while IFS= read -r game_title; do
        current_game=$((current_game + 1))
        log_message "${BLUE}[$current_game/$total_games] Processing: $game_title${NC}"
        
        # Clean the title
        local clean_title=$(clean_title "$game_title")
        
        # Search for the game
        local search_results=$(search_game "$clean_title")
        
        if [ $? -eq 0 ]; then
            # Select best match
            local best_match=$(select_best_match "$clean_title" "$search_results")
            
            if [ -n "$best_match" ]; then
                # Download the game
                if download_game "$clean_title" "$best_match"; then
                    remove_from_queue "$game_title"
                    successful_downloads=$((successful_downloads + 1))
                    log_message "${GREEN}✓ Completed: $game_title${NC}"
                else
                    failed_downloads=$((failed_downloads + 1))
                    log_message "${RED}✗ Download failed: $game_title${NC}"
                fi
            else
                log_message "${YELLOW}Could not find suitable match for: $game_title${NC}"
                failed_downloads=$((failed_downloads + 1))
            fi
        else
            log_message "${YELLOW}Skipping: $game_title (not found)${NC}"
            failed_downloads=$((failed_downloads + 1))
        fi
        
        # Wait before next download to be respectful to the server
        if [ $current_game -lt $total_games ]; then
            log_message "${BLUE}Waiting 3 seconds before next download...${NC}"
            sleep 3
        fi
        
    done < "$games_file"
    
    # Cleanup
    rm -f "$games_file"
    cleanup
    
    # Final summary
    log_message "${GREEN}Download session completed!${NC}"
    log_message "${GREEN}Successful downloads: $successful_downloads${NC}"
    log_message "${RED}Failed downloads: $failed_downloads${NC}"
    log_message "Check $LOG_FILE for detailed log"
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
