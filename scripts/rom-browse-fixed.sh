#!/bin/bash

# Myrient Browser - Fixed Version
# Interactive CLI browser for Myrient.erista.me

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BASE_URL_REDUMP="https://myrient.erista.me/files/Redump/"
BASE_URL_NOIN="https://myrient.erista.me/files/No-Intro/"
TEMP_DIR="./temp"
LOG_FILE="./mbrowse.log"
QUEUE_FILE="./download_queue"
PAGE_SIZE=50

# Create temp directory
mkdir -p "$TEMP_DIR"

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE" >&2
}

# Download index page
download_index() {
    local url="$1"
    local output="$2"
    log "${CYAN}Downloading index...${NC}"
    curl -s "$url" > "$output" || { log "${RED}Failed to download index${NC}"; return 1; }
}

# URL decode function
url_decode() {
    printf '%b\n' "${1//%/\\x}"
}

# List directories from index
list_dirs() {
    local index_file="$1"
    local output="$2"
    grep -o 'href="[^"]*/"' "$index_file" | sed 's/href="//;s/"//' | grep -v '^\.\./$' | grep -v '^https\?://' | grep -v '^/' | grep -v '^?' | while read -r line; do
        url_decode "$line"
    done > "$output"
}

# List files from directory
list_files() {
    local index_file="$1"
    local output="$2"
    # Extract both directories and files from table rows
    grep -o 'href="[^"]*"' "$index_file" | sed 's/href="//;s/"//' | grep -v '^\.\./$' | grep -v '^https\?://' | grep -v '^/' | grep -v '^?' | while read -r line; do
        url_decode "$line"
    done > "$output"
}

# Print numbered range
print_numbered_range() {
    local file="$1"
    local start="$2"
    local size="$3"
    local end=$((start + size - 1))
    local total=$(wc -l < "$file" 2>/dev/null || echo 0)
    if [ "$end" -gt "$total" ]; then end="$total"; fi
    
    local count="$start"
    while IFS= read -r line && [ "$count" -le "$end" ]; do
        echo "  $count. $line"
        count=$((count + 1))
    done < "$file"
}

# Browse directory
browse_dir() {
    local platform="$1"
    local rel="$2"
    local page_start=1
    
    while true; do
        # Download directory index
        local url="${MYRIENT_BASE_URL}${rel}"
        local index_file="$TEMP_DIR/index.html"
        if ! download_index "$url" "$index_file"; then
            log "${RED}Failed to download directory${NC}"
            return 1
        fi
        
        # List files
        local files="$TEMP_DIR/files.txt"
        list_files "$index_file" "$files"
        
        local total=$(wc -l < "$files" 2>/dev/null || echo 0)
        if [ "$total" -le 0 ]; then
            log "${YELLOW}No files found${NC}"
            return 1
        fi
        
        # Calculate pagination
        local page_end=$((page_start + PAGE_SIZE - 1))
        if [ "$page_end" -gt "$total" ]; then page_end="$total"; fi
        local total_pages=$(((total + PAGE_SIZE - 1) / PAGE_SIZE))
        local current_page=$(((page_start - 1) / PAGE_SIZE + 1))
        
        # Display files
        echo -e "${CYAN}Files (${page_start}-${page_end} of ${total}) [Page ${current_page}/${total_pages}]${NC}"
        print_numbered_range "$files" "$page_start" "$PAGE_SIZE"
        echo ""
        echo -e "${CYAN}Commands: n/p (next/prev page), p-<num> (goto page), <num> (select file), <text> (search), .. (up), q (quit)${NC}"
        echo -ne "${CYAN}Enter command: ${NC}"
        read -r cmd
        
        case "$cmd" in
            "q")
                return 1
                ;;
            "..")
                rel="${rel%/}"
                rel="${rel%/*}/"
                if [ "$rel" = "/" ]; then
                    return 0
                fi
                page_start=1
                ;;
            "n")
                if [ $((page_start + PAGE_SIZE)) -le "$total" ]; then
                    page_start=$((page_start + PAGE_SIZE))
                else
                    log "${YELLOW}Already at last page${NC}"
                fi
                ;;
            "p")
                if [ $((page_start - PAGE_SIZE)) -ge 1 ]; then
                    page_start=$((page_start - PAGE_SIZE))
                else
                    log "${YELLOW}Already at first page${NC}"
                fi
                ;;
            p-*)
                local target_page="${cmd#p-}"
                if [[ "$target_page" =~ ^[0-9]+$ ]]; then
                    local max_page=$(((total + PAGE_SIZE - 1) / PAGE_SIZE))
                    if [ "$target_page" -ge 1 ] && [ "$target_page" -le "$max_page" ]; then
                        page_start=$(((target_page - 1) * PAGE_SIZE + 1))
                    else
                        log "${YELLOW}Invalid page number. Range: 1-${max_page}${NC}"
                    fi
                else
                    log "${YELLOW}Invalid page number${NC}"
                fi
                ;;
            [0-9]*)
                local file_num="$cmd"
                if [ "$file_num" -ge 1 ] && [ "$file_num" -le "$total" ]; then
                    local selected_file=$(sed -n "${file_num}p" "$files")
                    if [ -n "$selected_file" ]; then
                        # Check if it's a directory or file
                        if [[ "$selected_file" == */ ]]; then
                            # It's a directory - need to URL encode the path for navigation
                            local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                            rel="${rel}${encoded_file}"
                            page_start=1
                        else
                            # It's a file - need to URL encode for download
                            local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                            local file_url="${url}${encoded_file}"
                            local filename=$(basename "$selected_file")
                            log "${CYAN}Downloading: $filename${NC}"
                            if curl -s -o "$filename" "$file_url"; then
                                log "${GREEN}Downloaded: $filename${NC}"
                            else
                                log "${RED}Failed to download: $filename${NC}"
                            fi
                        fi
                    else
                        log "${YELLOW}Invalid file number${NC}"
                    fi
                else
                    log "${YELLOW}Invalid file number${NC}"
                fi
                ;;
            *)
                # Text search
                log "${CYAN}Searching for: $cmd${NC}"
                grep -i "$cmd" "$files" > "$TEMP_DIR/search_results.txt" || true
                if [ -s "$TEMP_DIR/search_results.txt" ]; then
                    local search_total=$(wc -l < "$TEMP_DIR/search_results.txt")
                    echo -e "${CYAN}Search results (${search_total} matches):${NC}"
                    print_numbered_range "$TEMP_DIR/search_results.txt" 1 50
                    echo ""
                    echo -e "${CYAN}Commands: <num> (select from results), .. (back to full list), q (quit)${NC}"
                    echo -ne "${CYAN}Enter command: ${NC}"
                    read -r search_cmd
                    
                    case "$search_cmd" in
                        "q")
                            return 1
                            ;;
                        "..")
                            # Continue with normal browsing
                            ;;
                        [0-9]*)
                            local search_num="$search_cmd"
                            if [ "$search_num" -ge 1 ] && [ "$search_num" -le "$search_total" ]; then
                                local selected_file=$(sed -n "${search_num}p" "$TEMP_DIR/search_results.txt")
                                if [ -n "$selected_file" ]; then
                                    # Check if it's a directory or file
                                    if [[ "$selected_file" == */ ]]; then
                                        # It's a directory - need to URL encode the path for navigation
                                        local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                                        rel="${rel}${encoded_file}"
                                        page_start=1
                                    else
                                        # It's a file - need to URL encode for download
                                        local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                                        local file_url="${url}${encoded_file}"
                                        local filename=$(basename "$selected_file")
                                        log "${CYAN}Downloading: $filename${NC}"
                                        if curl -s -o "$filename" "$file_url"; then
                                            log "${GREEN}Downloaded: $filename${NC}"
                                        else
                                            log "${RED}Failed to download: $filename${NC}"
                                        fi
                                    fi
                                else
                                    log "${YELLOW}Invalid file number${NC}"
                                fi
                            else
                                log "${YELLOW}Invalid file number${NC}"
                            fi
                            ;;
                        *)
                            log "${YELLOW}Unknown command: $search_cmd${NC}"
                            ;;
                    esac
                else
                    log "${YELLOW}No matches found${NC}"
                fi
                ;;
        esac
    done
}

# Search function
search_platforms() {
    local query="$1"
    local platforms_file="$TEMP_DIR/all_platforms.txt"
    
    # Get platforms from both datasets
    local redump_file="$TEMP_DIR/redump_platforms.txt"
    local nointro_file="$TEMP_DIR/nointro_platforms.txt"
    
    download_index "$BASE_URL_REDUMP" "$TEMP_DIR/redump_index.html"
    download_index "$BASE_URL_NOIN" "$TEMP_DIR/nointro_index.html"
    
    list_dirs "$TEMP_DIR/redump_index.html" "$redump_file"
    list_dirs "$TEMP_DIR/nointro_index.html" "$nointro_file"
    
    # Combine and search
    echo "Redump:" > "$platforms_file"
    cat "$redump_file" >> "$platforms_file"
    echo "" >> "$platforms_file"
    echo "No-Intro:" >> "$platforms_file"
    cat "$nointro_file" >> "$platforms_file"
    
    grep -i "$query" "$platforms_file" | head -20
}

# Main function
main() {
    echo -e "${CYAN}Myrient Browser${NC}"
    echo ""
    echo "Select dataset or quick-jump (e.g., 1-177 or 1-microsoft):"
    echo "  1) Redump"
    echo "  2) No-Intro"
    echo -ne "Enter choice or search term: "
    read -r choice
    
    # Handle quick navigation (e.g., 2-176)
    if [[ "$choice" =~ ^([12])-([0-9]+)$ ]]; then
        local dataset="${BASH_REMATCH[1]}"
        local platform_num="${BASH_REMATCH[2]}"
        
        if [ "$dataset" = "1" ]; then
            MYRIENT_BASE_URL="$BASE_URL_REDUMP"
        else
            MYRIENT_BASE_URL="$BASE_URL_NOIN"
        fi
        
        # Download platform list and navigate to specific platform
        local index_file="$TEMP_DIR/root.html"
        download_index "$MYRIENT_BASE_URL" "$index_file"
        local platforms_file="$TEMP_DIR/plats.txt"
        list_dirs "$index_file" "$platforms_file"
        
        local platform=$(sed -n "${platform_num}p" "$platforms_file")
        if [ -n "$platform" ]; then
            log "${GREEN}Selected platform: $platform${NC}"
            # Convert decoded platform name back to URL-encoded for navigation
            local encoded_platform=$(printf '%s\n' "$platform" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
            browse_dir "platform" "$encoded_platform"
        else
            log "${RED}Invalid platform index${NC}"
            exit 1
        fi
        return
    fi
    
    # Handle search
    if [[ "$choice" =~ ^[a-zA-Z] ]]; then
        log "${CYAN}Searching for: $choice${NC}"
        search_platforms "$choice"
        echo ""
        echo -ne "Enter dataset choice (1 or 2) or 'q' to quit: "
        read -r dataset_choice
        if [ "$dataset_choice" = "q" ]; then
            exit 0
        fi
        choice="$dataset_choice"
    fi
    
    case "$choice" in
        "1")
            MYRIENT_BASE_URL="$BASE_URL_REDUMP"
            ;;
        "2")
            MYRIENT_BASE_URL="$BASE_URL_NOIN"
            ;;
        *)
            log "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
    
    # Browse root directory
    browse_dir "platform" "/"
}

# Run main function
main "$@"
