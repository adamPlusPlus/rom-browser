#!/bin/bash

# ROM Batch Downloader
# Downloads ROMs from ROM archives based on platform selection and download queue
# Usage: ./rom-download.sh [platform] [subtype]

# Configuration
# Dataset bases
BASE_URL_REDUMP="https://myrient.erista.me/files/Redump/"
BASE_URL_NOIN="https://myrient.erista.me/files/No-Intro/"
# Active base URL (will be set after dataset selection)
ROM_ARCHIVE_BASE_URL="$BASE_URL_REDUMP"
DOWNLOAD_DIR="./downloads"
QUEUE_FILE="./download_queue"
LOG_FILE="./download_log.txt"
TEMP_DIR="./temp"

# Available platforms and their subtypes
declare -A PLATFORMS
PLATFORMS["Nintendo - Nintendo Entertainment System"]="NES"
PLATFORMS["Nintendo - Super Nintendo Entertainment System"]="SNES"
PLATFORMS["Nintendo - Nintendo 64"]="N64"
PLATFORMS["Nintendo - Nintendo GameCube"]="NGC"
PLATFORMS["Nintendo - Nintendo Wii"]="WII"
PLATFORMS["Nintendo - Nintendo Wii U"]="WIIU"
PLATFORMS["Nintendo - Nintendo Switch"]="NSW"
PLATFORMS["Sony - PlayStation"]="PS1"
PLATFORMS["Sony - PlayStation 2"]="PS2"
PLATFORMS["Sony - PlayStation 3"]="PS3"
PLATFORMS["Sony - PlayStation 4"]="PS4"
PLATFORMS["Sony - PlayStation 5"]="PS5"
PLATFORMS["Sony - PlayStation Portable"]="PSP"
PLATFORMS["Sony - PlayStation Vita"]="PSV"
PLATFORMS["Microsoft - Xbox"]="XBOX"
PLATFORMS["Microsoft - Xbox 360"]="X360"
PLATFORMS["Microsoft - Xbox One"]="XONE"
PLATFORMS["Microsoft - Xbox Series X|S"]="XSX"
PLATFORMS["Sega - Master System"]="SMS"
PLATFORMS["Sega - Mega Drive - Genesis"]="MD"
PLATFORMS["Sega - Sega CD"]="SCD"
PLATFORMS["Sega - Sega 32X"]="32X"
PLATFORMS["Sega - Sega Saturn"]="SAT"
PLATFORMS["Sega - Dreamcast"]="DC"
PLATFORMS["Atari - 2600"]="A2600"
PLATFORMS["Atari - 5200"]="A5200"
PLATFORMS["Atari - 7800"]="A7800"
PLATFORMS["Atari - Jaguar"]="JAG"
PLATFORMS["Atari - Lynx"]="LYNX"
PLATFORMS["NEC - PC Engine - TurboGrafx-16"]="PCE"
PLATFORMS["NEC - PC Engine CD - TurboGrafx-CD"]="PCE-CD"
PLATFORMS["NEC - PC Engine SuperGrafx"]="SGX"
PLATFORMS["NEC - PC-FX"]="PCFX"
PLATFORMS["SNK - Neo Geo"]="NEO"
PLATFORMS["SNK - Neo Geo CD"]="NGCD"
PLATFORMS["SNK - Neo Geo Pocket"]="NGP"
PLATFORMS["SNK - Neo Geo Pocket Color"]="NGPC"
PLATFORMS["Bandai - WonderSwan"]="WS"
PLATFORMS["Bandai - WonderSwan Color"]="WSC"
PLATFORMS["Commodore - Amiga"]="AMIGA"
PLATFORMS["Commodore - Commodore 64"]="C64"
PLATFORMS["Commodore - Amiga CD32"]="CD32"
PLATFORMS["Apple - Apple II"]="APPLE2"
PLATFORMS["Apple - Macintosh"]="MAC"
PLATFORMS["IBM - PC"]="PC"
PLATFORMS["IBM - PC DOS"]="DOS"
PLATFORMS["IBM - PC Windows"]="WIN"
PLATFORMS["IBM - PC Linux"]="LINUX"
PLATFORMS["IBM - PC macOS"]="MACOS"
PLATFORMS["IBM - PC Android"]="ANDROID"
PLATFORMS["IBM - PC iOS"]="IOS"
PLATFORMS["IBM - PC Web"]="WEB"
PLATFORMS["IBM - PC VR"]="VR"
PLATFORMS["IBM - PC AR"]="AR"
PLATFORMS["IBM - PC Cloud"]="CLOUD"
PLATFORMS["IBM - PC Mobile"]="MOBILE"
PLATFORMS["IBM - PC Handheld"]="HANDHELD"
PLATFORMS["IBM - PC Console"]="CONSOLE"
PLATFORMS["IBM - PC Arcade"]="ARCADE"
PLATFORMS["IBM - PC Pinball"]="PINBALL"
PLATFORMS["IBM - PC Casino"]="CASINO"
PLATFORMS["IBM - PC Educational"]="EDU"
PLATFORMS["IBM - PC Sports"]="SPORTS"
PLATFORMS["IBM - PC Racing"]="RACING"
PLATFORMS["IBM - PC Fighting"]="FIGHTING"
PLATFORMS["IBM - PC Shooter"]="SHOOTER"
PLATFORMS["IBM - PC Adventure"]="ADV"
PLATFORMS["IBM - PC RPG"]="RPG"
PLATFORMS["IBM - PC Strategy"]="STRAT"
PLATFORMS["IBM - PC Simulation"]="SIM"
PLATFORMS["IBM - PC Puzzle"]="PUZZLE"
PLATFORMS["IBM - PC Platformer"]="PLAT"
PLATFORMS["IBM - PC Action"]="ACTION"
PLATFORMS["IBM - PC Horror"]="HORROR"
PLATFORMS["IBM - PC Comedy"]="COMEDY"
PLATFORMS["IBM - PC Drama"]="DRAMA"
PLATFORMS["IBM - PC Sci-Fi"]="SCIFI"
PLATFORMS["IBM - PC Fantasy"]="FANTASY"
PLATFORMS["IBM - PC Historical"]="HIST"
PLATFORMS["IBM - PC Military"]="MIL"
PLATFORMS["IBM - PC Western"]="WESTERN"
PLATFORMS["IBM - PC Crime"]="CRIME"
PLATFORMS["IBM - PC Mystery"]="MYSTERY"
PLATFORMS["IBM - PC Thriller"]="THRILLER"
PLATFORMS["IBM - PC Romance"]="ROMANCE"
PLATFORMS["IBM - PC Musical"]="MUSICAL"
PLATFORMS["IBM - PC Documentary"]="DOC"
PLATFORMS["IBM - PC Animation"]="ANIM"
PLATFORMS["IBM - PC Family"]="FAMILY"
PLATFORMS["IBM - PC Children"]="CHILDREN"
PLATFORMS["IBM - PC Teen"]="TEEN"
PLATFORMS["IBM - PC Adult"]="ADULT"
PLATFORMS["IBM - PC Mature"]="MATURE"
PLATFORMS["IBM - PC Everyone"]="EVERYONE"
PLATFORMS["IBM - PC Everyone 10+"]="E10+"
PLATFORMS["IBM - PC Teen 13+"]="T13+"
PLATFORMS["IBM - PC Mature 17+"]="M17+"
PLATFORMS["IBM - PC Adults Only 18+"]="AO18+"
PLATFORMS["IBM - PC Rating Pending"]="RP"
PLATFORMS["IBM - PC Not Rated"]="NR"
PLATFORMS["IBM - PC Unrated"]="UR"
PLATFORMS["IBM - PC Unknown"]="UNK"
PLATFORMS["IBM - PC Other"]="OTHER"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create directories
mkdir -p "$DOWNLOAD_DIR"
mkdir -p "$TEMP_DIR"

# Initialize log file
echo "Universal ROM Download Session Started: $(date)" > "$LOG_FILE"

# Function to log messages
log_message() {
    local message="$1"
    echo -e "$message"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $message" >> "$LOG_FILE"
}

# Function to display platform selection menu
show_platform_menu() {
    log_message "${CYAN}Available Platforms:${NC}"
    log_message "${YELLOW}Enter platform name or number:${NC}"
    echo ""
    
    local count=1
    for platform in "${!PLATFORMS[@]}"; do
        printf "${BLUE}%2d.${NC} %s\n" "$count" "$platform"
        count=$((count + 1))
    done
    echo ""
}

# Function: improved URL encode for platform paths
urlencode_platform() {
    local s="$1"
    s=$(echo "$s" | sed 's/ /%20/g' | sed 's/(/%28/g' | sed 's/)/%29/g' | sed 's/+/%2B/g' | sed 's/&/%26/g' | sed "s/'/%27/g" | sed 's/,/%2C/g')
    echo "$s"
}

# Download dataset index (root listing) and return path
download_dataset_index() {
    local index_file="$TEMP_DIR/dataset_index.html"
    log_message "${BLUE}Loading dataset index...${NC}" >/dev/null
    if curl -s -o "$index_file" "$MYRIENT_BASE_URL"; then
        echo "$index_file"
        return 0
    else
        log_message "${RED}Failed to load dataset index${NC}" >/dev/null
        return 1
    fi
}

# Parse platforms (directories) from dataset index into a file (one per line)
parse_platforms_from_index() {
    local index_file="$1"
    local out_file="$TEMP_DIR/platforms.txt"
    : > "$out_file"
    # Prefer title attribute when present; fallback to href decoding
    local with_titles=$(grep -E 'href="[^"]+/"' "$index_file" | grep -v '\?C=' | grep -v '\.\./' | sed -n 's/.*title="\([^"]*\)".*/\1/p')
    if [ -n "$with_titles" ]; then
        echo "$with_titles" | sed 's:/$::' | sort -f > "$out_file"
    else
        grep -E 'href="[^"]+/"' "$index_file" | grep -v '\?C=' | grep -v '\.\./' | \
        sed -n 's/.*href="\([^"]*\)".*/\1/p' | sed 's:/$::' | \
        sed -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g' -e 's/%2B/+/g' -e 's/%26/&/g' -e "s/%27/'/g" -e 's/%2C/,/g' | \
        sort -f > "$out_file"
    fi
    echo "$out_file"
}

# Print a numbered list (top N)
print_numbered_list() {
    local file="$1"
    local limit="$2"
    if [ -z "$limit" ]; then limit=100; fi
    if [ ! -s "$file" ]; then
        return 0
    fi
    awk -v lim="$limit" '{ if (NR <= lim) printf("%2d. %s\n", NR, $0) }' "$file"
}

# Print indexed matches (original list numbering) for filtered items
print_indexed_matches() {
    local items_file="$1"
    local filtered_file="$2"
    local limit="$3"
    if [ -z "$limit" ]; then limit=100; fi
    if [ ! -s "$filtered_file" ]; then
        return 0
    fi
    local count=0
    while IFS= read -r line; do
        local idx=$(grep -n -F -x -- "$line" "$items_file" | head -n1 | cut -d: -f1)
        if [ -n "$idx" ]; then
            printf "%d. %s\n" "$idx" "$line"
            count=$((count+1))
            if [ "$count" -ge "$limit" ]; then
                break
            fi
        fi
    done < "$filtered_file"
}

# Interactive filter-and-select from a list file
interactive_select_from_list() {
    local items_file="$1"
    local prompt_text="$2"
    local initial_filter="$3"
    local limit="$4"
    if [ -z "$limit" ]; then limit=100; fi
    local filtered_file=$(mktemp)
    cp "$items_file" "$filtered_file"
    if [ -n "$initial_filter" ]; then
        grep -i -- "$initial_filter" "$items_file" > "$filtered_file" || true
        if [ ! -s "$filtered_file" ]; then cp "$items_file" "$filtered_file"; fi
    fi
    while true; do
        echo "" >&2
        local total=$(wc -l < "$filtered_file" 2>/dev/null | tr -d '[:space:]')
        if [ -z "$total" ]; then total=0; fi
        log_message "${CYAN}Matches ($total found):${NC}" >&2
        print_indexed_matches "$items_file" "$filtered_file" "$limit" >&2
        if [ "$total" -gt "$limit" ]; then
            echo "... (showing first $limit of $total)" >&2
        fi
        echo "" >&2
        read -p "$prompt_text (type to filter or number to select, q=quit): " input
        if [[ "$input" =~ ^[0-9]+$ ]]; then
            local selection=$(sed -n "${input}p" "$items_file")
            if [ -n "$selection" ] && grep -Fx -q -- "$selection" "$filtered_file"; then
                echo "$selection"
                rm -f "$filtered_file"
                return 0
            else
                log_message "${YELLOW}Invalid selection number for current filter${NC}" >&2
            fi
        elif [[ "$input" =~ ^[0-9]+(,[0-9]+)*$ ]]; then
            # Multi-select by comma-separated indices (validate each against current filter)
            local IFS=','
            local indices=($input)
            local out_tmp=$(mktemp)
            local ok=0
            for idx in "${indices[@]}"; do
                if [[ "$idx" =~ ^[0-9]+$ ]]; then
                    local line=$(sed -n "${idx}p" "$items_file")
                    if [ -n "$line" ] && grep -Fx -q -- "$line" "$filtered_file"; then
                        echo "$line" >> "$out_tmp"
                        ok=1
                    fi
                fi
            done
            if [ "$ok" = "1" ]; then
                cat "$out_tmp"
                rm -f "$out_tmp" "$filtered_file"
                return 0
            else
                rm -f "$out_tmp"
                log_message "${YELLOW}Invalid selection numbers for current filter${NC}" >&2
            fi
        elif [ "$input" = "q" ] || [ "$input" = "Q" ]; then
            rm -f "$filtered_file"
            return 1
        else
            # Apply filter; update list and loop (printing will happen once at top)
            if [ -z "$input" ]; then
                continue
            fi
            grep -i -- "$input" "$items_file" > "${filtered_file}.tmp" || true
            if [ -s "${filtered_file}.tmp" ]; then
                mv "${filtered_file}.tmp" "$filtered_file"
                continue
            else
                rm -f "${filtered_file}.tmp"
                log_message "${YELLOW}No matches, try a different filter${NC}" >&2
                continue
            fi
        fi
    done
}

# Function to get platform by number or name
get_platform() {
    local input="$1"
    local count=1
    
    # Check if input is a number
    if [[ "$input" =~ ^[0-9]+$ ]]; then
        for platform in "${!PLATFORMS[@]}"; do
            if [ $count -eq $input ]; then
                echo "$platform"
                return 0
            fi
            count=$((count + 1))
        done
        return 1
    else
        # Check if input matches a platform name (case-insensitive)
        for platform in "${!PLATFORMS[@]}"; do
            if [[ "${platform,,}" == *"${input,,}"* ]]; then
                echo "$platform"
                return 0
            fi
        done
        # Check if input matches a platform short code (values), e.g. PS2, X360
        for platform in "${!PLATFORMS[@]}"; do
            local code="${PLATFORMS[$platform]}"
            if [[ "${code,,}" == "${input,,}" ]]; then
                echo "$platform"
                return 0
            fi
        done
        return 1
    fi
}

# Function to get platform URL
get_platform_url() {
    local platform="$1"
    # URL encode spaces and special characters
    local encoded_platform=$(urlencode_platform "$platform")
    echo "${MYRIENT_BASE_URL}${encoded_platform}/"
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
    local platform="$1"
    local index_file="$TEMP_DIR/archive_index.html"
    
    log_message "${BLUE}Downloading archive index for: $platform${NC}"
    
    if curl -s -o "$index_file" "$(get_platform_url "$platform")"; then
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
    
    # Create multiple search patterns for better matching
    local search_patterns=(
        "$(echo "$game_title" | sed 's/[[:space:]]\+/.*/g')"
        "$(echo "$game_title" | sed 's/[[:space:]]\+/.*/g' | sed 's/[^a-zA-Z0-9]/.*/g')"
        "$(echo "$game_title" | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]]\+/.*/g')"
        "$(echo "$game_title" | sed 's/[[:space:]]\+/.*/g' | sed 's/[^a-zA-Z0-9]/.*/g' | sed 's/.*/.*&.*/')"
    )
    
    # Try each search pattern
    for pattern in "${search_patterns[@]}"; do
        local matches=$(grep -i "$pattern" "$index_file" | grep -E 'href="[^"]*\.(zip|7z)"' | head -10)
        
        if [ -n "$matches" ]; then
            log_message "${GREEN}Found $(echo "$matches" | wc -l) potential matches for: $game_title${NC}"
            echo "$matches"
            return 0
        fi
    done
    
    log_message "${YELLOW}No matches found for: $game_title${NC}"
    return 1
}

# Function to select best match
select_best_match() {
    local game_title="$1"
    local matches="$2"
    
    # Score each match based on similarity and region preference
    local best_match=""
    local best_score=0
    
    while IFS= read -r match; do
        if [ -n "$match" ]; then
            # Extract filename from href attribute, handling different HTML formats
            local filename=""
            if echo "$match" | grep -q 'href="[^"]*\.(zip|7z)"'; then
                filename=$(echo "$match" | sed 's/.*href="\([^"]*\.[zZ][iI][pP]\)".*/\1/')
                if [ -z "$filename" ]; then
                    filename=$(echo "$match" | sed 's/.*href="\([^"]*\.[7zZ]\)".*/\1/')
                fi
            elif echo "$match" | grep -q 'href="[^"]*"'; then
                filename=$(echo "$match" | sed 's/.*href="\([^\"]*\)".*/\1/')
            fi
            
            # Validate that we got a proper filename
            if [ -n "$filename" ] && [ "$filename" != "$match" ] && [[ "$filename" != *"Searching for:"* ]]; then
                local clean_filename=$(echo "$filename" | sed -e 's/\.zip$//' -e 's/\.7z$//' -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g')
                
                # Simple scoring based on word overlap
                local score=0
                local game_words=$(echo "$game_title" | tr '[:upper:]' '[:lower:]' | tr '[:space:]' '\n' | grep -v '^$')
                local filename_words=$(echo "$clean_filename" | tr '[:upper:]' '[:lower:]' | tr '[:space:]' '\n' | grep -v '^$')
                
                while IFS= read -r word; do
                    if echo "$filename_words" | grep -q "^$word$"; then
                        score=$((score + 1))
                    fi
                done <<< "$game_words"
                
                # Region preference scoring - prioritize USA versions
                if echo "$clean_filename" | grep -qi "(USA)"; then
                    score=$((score + 10))  # High bonus for USA versions
                elif echo "$clean_filename" | grep -qi "(US)"; then
                    score=$((score + 10))  # High bonus for US versions
                elif echo "$clean_filename" | grep -qi "(North America)"; then
                    score=$((score + 8))   # Good bonus for North America
                elif echo "$clean_filename" | grep -qi "(Europe)"; then
                    score=$((score + 2))   # Small bonus for Europe
                elif echo "$clean_filename" | grep -qi "(Asia)"; then
                    score=$((score + 1))   # Very small bonus for Asia
                elif echo "$clean_filename" | grep -qi "(Japan)"; then
                    score=$((score + 0))   # No bonus for Japan
                fi
                
                # Language preference - prefer English versions
                if echo "$clean_filename" | grep -qi "(En)"; then
                    score=$((score + 3))   # Bonus for English language
                fi
                
                if [ $score -gt $best_score ]; then
                    best_score=$score
                    best_match="$filename"
                fi
            fi
        fi
    done <<< "$matches"
    
    echo "$best_match"
}

# Function to download game
download_game() {
    local game_title="$1"
    local filename="$2"
    local platform="$3"
    local download_url="$(get_platform_url "$platform")${filename}"
    
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
    
    # Extract game titles from clean format (no suffixes)
    grep -E '^[A-Za-z0-9]' "$QUEUE_FILE" | \
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

# Function to display help
show_help() {
    echo "Usage: $0 [platform] [subtype]"
    echo ""
    echo "Examples:"
    echo "  $0                           # Interactive mode (choose queue or single game)"
    echo "  $0 \"Xbox 360\"                # Interactive mode starting on Xbox 360"
    echo "  $0 PS2                       # Abbreviation also accepted (same as above)"
    echo "  $0 9                         # Platform by number (order not guaranteed)"
    echo ""
    echo "Tips:"
    echo "  - You can enter a platform number, part of its name (e.g. 'xbox 360'),"
    echo "    or the short code (e.g. PS2, X360)."
    echo "  - In single-game mode, you can enter a rough title or browse/search titles."
    echo "  - The downloader will pick the best match, prioritizing USA region."
    echo "  - Datasets: Choose between Redump and No-Intro platform listings."
    echo ""
}

# Build a combined title list from the current platform index
build_title_list() {
    local index_file="$TEMP_DIR/archive_index.html"
    local combined_file="$TEMP_DIR/titles_combined.txt"
    : > "$combined_file"
    local hrefs=$(grep -E 'href="[^"]*\.(zip|7z)"' "$index_file" | sed -n 's/.*href="\([^\"]\+\)".*/\1/p')
    if [ -z "$hrefs" ]; then
        echo "$combined_file"
        return 0
    fi
    while IFS= read -r href; do
        local display=$(echo "$href" | sed -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g' -e 's/%2B/+/g' -e 's/%26/&/g' -e "s/%27/'/g" -e 's/%2C/,/g' -e 's/\.zip$//' -e 's/\.7z$//')
        echo "$display||$href" >> "$combined_file"
    done <<< "$hrefs"
    echo "$combined_file"
}

# List archives from an arbitrary index file (display||href)
list_archives_from_index() {
    local index_file="$1"
    local out_file="$TEMP_DIR/archives_combined.txt"
    : > "$out_file"
    local hrefs=$(grep -E 'href="[^"]*\.(zip|7z)"' "$index_file" | sed -n 's/.*href="\([^"]*\)".*/\1/p')
    if [ -z "$hrefs" ]; then
        echo "$out_file"
        return 0
    fi
    while IFS= read -r href; do
        local display=$(echo "$href" | sed -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g' -e 's/%2B/+/g' -e 's/%26/&/g' -e "s/%27/'/g" -e 's/%2C/,/g' -e 's/\.zip$//' -e 's/\.7z$//')
        echo "$display||$href" >> "$out_file"
    done <<< "$hrefs"
    echo "$out_file"
}

# List subdirectories from an index file (display||href)
list_subdirs_from_index() {
    local index_file="$1"
    local out_file="$TEMP_DIR/subdirs_combined.txt"
    : > "$out_file"
    # Prefer title attribute when present; exclude parent, query-sorted links, absolute URLs, and site nav
    local lines=$(grep -E 'href="[^"]+/"' "$index_file" \
        | grep -v '\?C=' \
        | grep -v '\.\./' \
        | grep -v 'href="https\?://' \
        | grep -v 'href="/' \
        | grep -vi -E '(contact/|donate/|faq/|files/|upload/|discord|telegram|hshop)')
    if [ -z "$lines" ]; then
        echo "$out_file"
        return 0
    fi
    # Extract pairs
    echo "$lines" | while IFS= read -r line; do
        local href=$(echo "$line" | sed -n 's/.*href="\([^"]*\/\)".*/\1/p')
        [ -z "$href" ] && continue
        # Skip absolute URLs (safety)
        if echo "$href" | grep -qE '^https?://'; then
            continue
        fi
        local title=$(echo "$line" | sed -n 's/.*title="\([^"]*\)".*/\1/p')
        if [ -z "$title" ]; then
            title=$(echo "$href" | sed 's:/$::' | sed -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g' -e 's/%2B/+/g' -e 's/%26/&/g' -e "s/%27/'/g" -e 's/%2C/,/g')
        fi
        echo "$title||$href" >> "$out_file"
    done
    sort -f "$out_file" -o "$out_file"
    echo "$out_file"
}

# Collect archives recursively (BFS) up to max depth for a platform; outputs display||href_rel
collect_archives_recursive_for_platform() {
    local platform_name="$1"
    local max_depth="$2"
    if [ -z "$max_depth" ]; then max_depth=2; fi
    local platform_url="$(get_platform_url "$platform_name")"
    local out_file="$TEMP_DIR/archives_recursive.txt"
    : > "$out_file"
    local queue_curr="$TEMP_DIR/queue_curr.txt"
    local queue_next="$TEMP_DIR/queue_next.txt"
    printf "\t0\n" > "$queue_curr"
    while [ -s "$queue_curr" ]; do
        : > "$queue_next"
        while IFS=$'\t' read -r rel_path depth; do
            [ -z "$rel_path" ] && rel_path=""
            [ -z "$depth" ] && depth=0
            local url="${platform_url}${rel_path}"
            log_message "${BLUE}Scanning:${NC} ${platform_name}/${rel_path} (depth $depth)" >&2
            local idx="$TEMP_DIR/rec_index.html"
            if ! curl -s -o "$idx" "$url"; then
                continue
            fi
            local archives=$(list_archives_from_index "$idx")
            if [ -s "$archives" ]; then
                while IFS= read -r line; do
                    local disp=$(echo "$line" | cut -d'|' -f1)
                    local href=$(echo "$line" | sed 's/^.*||//')
                    echo "$disp||${rel_path}${href}" >> "$out_file"
                done < "$archives"
            fi
            if [ "$depth" -lt "$max_depth" ]; then
                local subs=$(list_subdirs_from_index "$idx")
                if [ -s "$subs" ]; then
                    while IFS= read -r subline; do
                        local subhref=$(echo "$subline" | sed 's/^.*||//')
                        # Skip absolute URLs defensively
                        if echo "$subhref" | grep -qE '^https?://'; then
                            continue
                        fi
                        printf "%s\t%d\n" "${rel_path}${subhref}" "$((depth+1))" >> "$queue_next"
                    done < "$subs"
                fi
            fi
        done < "$queue_curr"
        mv "$queue_next" "$queue_curr"
    done
    echo "$out_file"
}

# Interactive folder-first browser; shows folders first, then titles in a leaf
interactive_browse_folders_first() {
    local platform_name="$1"
    local platform_url="$(get_platform_url "$platform_name")"
    local rel_path=""
    while true; do
        local current_url="${platform_url}${rel_path}"
        local idx="$TEMP_DIR/folder_index.html"
        if ! curl -s -o "$idx" "$current_url"; then
            log_message "${RED}Failed to load listing${NC}" >&2
            return 1
        fi
        local subdirs=$(list_subdirs_from_index "$idx")
        if [ -s "$subdirs" ]; then
            local subdisplays="$TEMP_DIR/subdir_displays.txt"
            cut -d'|' -f1 "$subdirs" > "$subdisplays"
            local menu_file=$(mktemp)
            if [ -n "$rel_path" ]; then
                echo ".." > "$menu_file"
                cat "$subdisplays" >> "$menu_file"
            else
                cp "$subdisplays" "$menu_file"
            fi
            local chosen=$(interactive_select_from_list "$menu_file" "Folder" "" 100)
            if [ -z "$chosen" ]; then
                return 1
            fi
            if [ "$chosen" = ".." ]; then
                local tmp_rel="${rel_path%/}"
                if [[ "$tmp_rel" == *"/"* ]]; then
                    tmp_rel="${tmp_rel%/*}/"
                else
                    tmp_rel=""
                fi
                rel_path="$tmp_rel"
                continue
            fi
            local chosen_href=$(grep -F "${chosen}||" "$subdirs" | head -n1 | sed 's/^.*||//')
            rel_path="${rel_path}${chosen_href}"
            continue
        fi
        local archives=$(list_archives_from_index "$idx")
        if [ -s "$archives" ]; then
            local displays="$TEMP_DIR/title_displays.txt"
            cut -d'|' -f1 "$archives" > "$displays"
            local selected_line=$(interactive_select_from_list "$displays" "Title" "" 100)
            if [ -z "$selected_line" ]; then
                return 1
            fi
            local href=$(grep -F "${selected_line}||" "$archives" | head -n1 | sed 's/^.*||//')
            echo "${selected_line}||${rel_path}${href}"
            return 0
        fi
        log_message "${YELLOW}No content found in this folder${NC}" >&2
        return 1
    done
}

# Main execution
main() {
    local platform=""
    local platform_name=""
    local mode=""
    local dataset_choice=""
    
    # Parse command line arguments
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    # Dataset selection
    echo ""
    log_message "${CYAN}Select dataset:${NC}"
    echo "  1) Redump"
    echo "  2) No-Intro"
    read -p "Enter choice [1-2] (default 1): " dataset_choice
    # Quick path: accepts '1-<index>' or '2-<index>' to jump directly
    if [[ "$dataset_choice" =~ ^([12])-([0-9]+)$ ]]; then
        local ds="${BASH_REMATCH[1]}"
        local pidx="${BASH_REMATCH[2]}"
        if [ "$ds" = "1" ]; then
            MYRIENT_BASE_URL="$BASE_URL_REDUMP"
            log_message "Using dataset: Redump"
        else
            MYRIENT_BASE_URL="$BASE_URL_NOIN"
            log_message "Using dataset: No-Intro"
        fi
        local ds_index=$(download_dataset_index)
        local plats=$(parse_platforms_from_index "$ds_index")
        if [ -z "$plats" ] || [ ! -s "$plats" ]; then
            log_message "${RED}Unable to load platform list${NC}"
            exit 1
        fi
        local pname=$(sed -n "${pidx}p" "$plats")
        if [ -z "$pname" ]; then
            log_message "${RED}Invalid platform index: $pidx${NC}"
            exit 1
        fi
        platform_name="$pname"
        log_message "${GREEN}Selected platform: $platform_name${NC}"
        if ! download_archive_index "$platform_name"; then
            log_message "${RED}Failed to download archive index. Exiting.${NC}"
            exit 1
        fi
        local pair=$(interactive_browse_folders_first "$platform_name")
        if [ -z "$pair" ]; then
            cleanup
            log_message "${YELLOW}No title selected${NC}"
            exit 1
        fi
        local disp=$(echo "$pair" | cut -d'|' -f1)
        local href=$(echo "$pair" | sed 's/^.*||//')
        if download_game "$disp" "$href" "$platform_name"; then
            log_message "${GREEN}✓ Completed: $disp${NC}"
        else
            log_message "${RED}✗ Download failed: $disp${NC}"
            cleanup
            exit 1
        fi
        cleanup
        log_message "${GREEN}Download session completed!${NC}"
        exit 0
    fi
    if [ -z "$dataset_choice" ] || [ "$dataset_choice" = "1" ]; then
        MYRIENT_BASE_URL="$BASE_URL_REDUMP"
        log_message "Using dataset: Redump"
    elif [ "$dataset_choice" = "2" ]; then
        MYRIENT_BASE_URL="$BASE_URL_NOIN"
        log_message "Using dataset: No-Intro"
    else
        log_message "${YELLOW}Invalid choice, defaulting to Redump${NC}"
        MYRIENT_BASE_URL="$BASE_URL_REDUMP"
    fi

    # Interactive mode selection
    echo ""
    log_message "${CYAN}Select mode:${NC}"
    echo "  1) Continue download queue"
    echo "  2) Single game search/download"
    read -p "Enter choice [1-2]: " mode
    if [ -z "$mode" ]; then mode=1; fi
    # Quick path: if user enters a number other than 1 or 2, treat as platform index
    if [[ "$mode" =~ ^[0-9]+$ ]] && [ "$mode" != "1" ] && [ "$mode" != "2" ]; then
        local dataset_index_qp=$(download_dataset_index)
        local platforms_file_qp=""
        if [ -n "$dataset_index_qp" ]; then
            platforms_file_qp=$(parse_platforms_from_index "$dataset_index_qp")
        fi
        if [ -z "$platforms_file_qp" ] || [ ! -s "$platforms_file_qp" ]; then
            log_message "${RED}Unable to load platform list for quick selection${NC}"
            exit 1
        fi
        local platform_qp=$(sed -n "${mode}p" "$platforms_file_qp")
        if [ -z "$platform_qp" ]; then
            log_message "${RED}Invalid platform index: $mode${NC}"
            exit 1
        fi
        platform_name="$platform_qp"
        log_message "${GREEN}Selected platform: $platform_name${NC}"
        if ! download_archive_index "$platform_name"; then
            log_message "${RED}Failed to download archive index. Exiting.${NC}"
            exit 1
        fi
        # Jump straight to interactive browsing of this platform (folders first)
        local sel_file="$TEMP_DIR/selection.txt"
        : > "$sel_file"
        interactive_browse_folders_first "$platform_name" > "$sel_file"
        local pair_qp=""
        if [ -f "$sel_file" ]; then
            pair_qp=$(cat "$sel_file")
        fi
        if [ -z "$pair_qp" ]; then
            cleanup
            log_message "${YELLOW}No title selected${NC}"
            exit 1
        fi
        local disp_qp=$(echo "$pair_qp" | cut -d'|' -f1)
        local href_qp=$(echo "$pair_qp" | sed 's/^.*||//')
        if download_game "$disp_qp" "$href_qp" "$platform_name"; then
            log_message "${GREEN}✓ Completed: $disp_qp${NC}"
        else
            log_message "${RED}✗ Download failed: $disp_qp${NC}"
            cleanup
            exit 1
        fi
        cleanup
        log_message "${GREEN}Download session completed!${NC}"
        exit 0
    fi
    if [ "$mode" != "1" ] && [ "$mode" != "2" ]; then
        log_message "${RED}Error: Invalid mode selection${NC}"
        exit 1
    fi

    # Dynamic platform fetch and interactive selection; fallback to static
    local dataset_index=$(download_dataset_index)
    local platforms_file=""
    if [ -n "$dataset_index" ]; then
        platforms_file=$(parse_platforms_from_index "$dataset_index")
    fi
    if [ -z "$platforms_file" ] || [ ! -s "$platforms_file" ]; then
        log_message "${YELLOW}Falling back to static platform list${NC}"
        if [ -n "$1" ]; then
            platform="$1"
            platform_name=$(get_platform "$platform")
        else
            show_platform_menu
            read -p "Enter platform: " platform
            platform_name=$(get_platform "$platform")
        fi
        if [ -z "$platform_name" ]; then
            log_message "${RED}Error: Invalid platform selection${NC}"
            exit 1
        fi
    else
        local initial_filter="$1"
        local selection=$(interactive_select_from_list "$platforms_file" "Platform" "$initial_filter" 100)
        if [ -z "$selection" ]; then
            log_message "${RED}No platform selected${NC}"
            exit 1
        fi
        # If multiple lines returned, treat as multi-select
        if printf "%s" "$selection" | grep -q $'\n'; then
            # Build a combined recursive archive list for all selected platforms
            local combined="$TEMP_DIR/multi_archives.txt"
            : > "$combined"
            while IFS= read -r plat; do
                [ -z "$plat" ] && continue
                # Non-recursive: list only current directory archives for each selected platform
                local idx="$TEMP_DIR/multi_index.html"
                if curl -s -o "$idx" "$(get_platform_url "$plat")"; then
                    local archives=$(list_archives_from_index "$idx")
                    if [ -s "$archives" ]; then
                        while IFS= read -r line; do
                            local disp=$(echo "$line" | cut -d'|' -f1)
                            local href=$(echo "$line" | sed 's/^.*||//')
                            echo "$plat / $disp||$href" >> "$combined"
                        done < "$archives"
                    fi
                fi
            done <<< "$selection"
            if [ ! -s "$combined" ]; then
                log_message "${YELLOW}No titles found across selected folders${NC}"
                exit 1
            fi
            # Let user filter and pick a title across combined results
            local displays="$TEMP_DIR/combined_displays.txt"
            cut -d'|' -f1 "$combined" > "$displays"
            local chosen=$(interactive_select_from_list "$displays" "Title" "" 100)
            if [ -z "$chosen" ]; then
                log_message "${RED}No title selected${NC}"
                exit 1
            fi
            local href=$(grep -F "${chosen}||" "$combined" | head -n1 | sed 's/^.*||//')
            # We need a platform to compute URL; extract platform (before ' / ')
            local chosen_platform=$(echo "$chosen" | sed 's/\s*\/\s.*$//')
            if download_game "$chosen" "$href" "$chosen_platform"; then
                log_message "${GREEN}✓ Completed: $chosen${NC}"
            else
                log_message "${RED}✗ Download failed: $chosen${NC}"
                exit 1
            fi
            cleanup
            log_message "${GREEN}Download session completed!${NC}"
            exit 0
        else
            platform_name="$selection"
        fi
    fi
    
    log_message "${GREEN}Selected platform: $platform_name${NC}"
    
    # Download archive index first
    if ! download_archive_index "$platform_name"; then
        log_message "${RED}Failed to download archive index. Exiting.${NC}"
        exit 1
    fi

    # Single game search/download mode
    if [ "$mode" = "2" ]; then
        # Immediately enter folder-first navigation of the selected platform
        local sel_file2="$TEMP_DIR/selection.txt"
        : > "$sel_file2"
        interactive_browse_folders_first "$platform_name" > "$sel_file2"
        local pair=""
        if [ -f "$sel_file2" ]; then
            pair=$(cat "$sel_file2")
        fi
        if [ -z "$pair" ]; then
            # Fallback: try flat listing
            local combined=$(build_title_list)
            if [ ! -s "$combined" ]; then
                log_message "${YELLOW}No titles found in this platform${NC}"
                exit 1
            fi
            local displays="$TEMP_DIR/title_displays.txt"
            cut -d'|' -f1 "$combined" > "$displays"
            local selected_line=$(interactive_select_from_list "$displays" "Title" "" 100)
            if [ -z "$selected_line" ]; then
                log_message "${RED}No title selected${NC}"
                exit 1
            fi
            local href=$(grep -F "${selected_line}||" "$combined" | head -n1 | sed 's/^.*||//')
            pair="${selected_line}||${href}"
        fi
        local disp=$(echo "$pair" | cut -d'|' -f1)
        local href=$(echo "$pair" | sed 's/^.*||//')
        if download_game "$disp" "$href" "$platform_name"; then
            log_message "${GREEN}✓ Completed: $disp${NC}"
        else
            log_message "${RED}✗ Download failed: $disp${NC}"
            exit 1
        fi
        cleanup
        log_message "${GREEN}Download session completed!${NC}"
        exit 0
    fi

    # Queue processing mode
    # Check if queue file exists
    if [ ! -f "$QUEUE_FILE" ]; then
        log_message "${RED}Error: Queue file not found: $QUEUE_FILE${NC}"
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
                if download_game "$clean_title" "$best_match" "$platform_name"; then
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
