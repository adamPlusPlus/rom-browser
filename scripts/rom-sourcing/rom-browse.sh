#!/bin/bash

# ROM Browser - Interactive CLI browser for ROM archives
# Supports multiple ROM sources including Myrient.erista.me

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
DOWNLOADS_DIR="../downloads"
LOG_FILE="./rom-browse.log"
QUEUE_FILE="./download_queue"
PAGE_SIZE=50
FILTER_FILE="../config/rom-filter.txt"
HISTORY_FILE="./rom-browse-history.txt"

# Create temp directory
mkdir -p "$TEMP_DIR"

# Create downloads directory
mkdir -p "$DOWNLOADS_DIR"

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE" >&2
}

# Filter functions
apply_filters() {
    local input_file="$1"
    local output_file="$2"

    if [ ! -f "$FILTER_FILE" ]; then
        cp "$input_file" "$output_file"
        return
    fi

    cp "$input_file" "$output_file"

    # Apply each filter line
    while IFS= read -r filter_line; do
        # Skip empty lines and comments
        if [ -z "$filter_line" ] || [[ "$filter_line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        # Remove leading/trailing whitespace
        filter_line=$(echo "$filter_line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [ -n "$filter_line" ]; then
            grep -viF "$filter_line" "$output_file" > "$TEMP_DIR/tmp_filter.txt" || true
            mv "$TEMP_DIR/tmp_filter.txt" "$output_file"
        fi
    done < "$FILTER_FILE"
}

edit_filters() {
    if command -v vim >/dev/null 2>&1; then
        vim "$FILTER_FILE"
    elif command -v nano >/dev/null 2>&1; then
        nano "$FILTER_FILE"
    elif command -v notepad >/dev/null 2>&1; then
        notepad "$FILTER_FILE"
    else
        log "${YELLOW}No text editor found. Please edit $FILTER_FILE manually${NC}"
        return 1
    fi
}

add_filter() {
    local filter="$1"
    if [ -z "$filter" ]; then
        log "${YELLOW}Usage: -f-out <filter_word>${NC}"
        return 1
    fi

    # Remove surrounding quotes if present
    filter=$(echo "$filter" | sed 's/^"//;s/"$//')

    # Create filter file if it doesn't exist
    if [ ! -f "$FILTER_FILE" ]; then
        touch "$FILTER_FILE"
    fi

    # Check if filter already exists
    if grep -qFx "$filter" "$FILTER_FILE" 2>/dev/null; then
        log "${YELLOW}Filter '$filter' already exists${NC}"
        return 1
    fi

    echo "$filter" >> "$FILTER_FILE"
    log "${GREEN}Added filter: '$filter'${NC}"
}

remove_filter() {
    local filter="$1"
    if [ -z "$filter" ]; then
        log "${YELLOW}Usage: -f-in <filter_word>${NC}"
        return 1
    fi

    # Remove surrounding quotes if present
    filter=$(echo "$filter" | sed 's/^"//;s/"$//')

    if [ ! -f "$FILTER_FILE" ]; then
        log "${YELLOW}No filter file found${NC}"
        return 1
    fi

    if grep -qFx "$filter" "$FILTER_FILE" 2>/dev/null; then
        grep -vFx "$filter" "$FILTER_FILE" > "$TEMP_DIR/tmp_filter.txt"
        mv "$TEMP_DIR/tmp_filter.txt" "$FILTER_FILE"
        log "${GREEN}Removed filter: '$filter'${NC}"
    else
        log "${YELLOW}Filter '$filter' not found${NC}"
        return 1
    fi
}

# History functions
add_to_history() {
    local dir_path="$1"
    local platform="$2"
    
    # Only add leaf directories (those with actual content, not parent dirs)
    if [ -z "$dir_path" ] || [ "$dir_path" = "/" ] || [ "$dir_path" = "" ]; then
        return
    fi
    
    # Create history file if it doesn't exist
    if [ ! -f "$HISTORY_FILE" ]; then
        touch "$HISTORY_FILE"
    fi
    
    # Create history entry with timestamp
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local entry="$platform|$dir_path|$timestamp"
    
    # Remove any existing entry for this directory
    grep -v "^$platform|$dir_path|" "$HISTORY_FILE" > "$TEMP_DIR/tmp_history.txt" 2>/dev/null || true
    mv "$TEMP_DIR/tmp_history.txt" "$HISTORY_FILE" 2>/dev/null || true
    
    # Add new entry at the top
    echo "$entry" > "$TEMP_DIR/tmp_history.txt"
    cat "$HISTORY_FILE" >> "$TEMP_DIR/tmp_history.txt" 2>/dev/null || true
    
    # Keep only last 5 entries
    head -n 5 "$TEMP_DIR/tmp_history.txt" > "$HISTORY_FILE"
}

show_history() {
    if [ ! -f "$HISTORY_FILE" ] || [ ! -s "$HISTORY_FILE" ]; then
        log "${YELLOW}No directory history found${NC}"
        return 1
    fi
    
    log "${CYAN}Recent directories:${NC}"
    local count=1
    while IFS='|' read -r platform dir_path timestamp; do
        if [ -n "$platform" ] && [ -n "$dir_path" ]; then
            echo "  $count) $platform: $dir_path ($timestamp)"
            count=$((count + 1))
        fi
    done < "$HISTORY_FILE"
}

navigate_to_history() {
    local choice="$1"
    
    if [ ! -f "$HISTORY_FILE" ] || [ ! -s "$HISTORY_FILE" ]; then
        log "${YELLOW}No directory history found${NC}"
        return 1
    fi
    
    # Get the selected entry
    local entry=$(sed -n "${choice}p" "$HISTORY_FILE")
    if [ -z "$entry" ]; then
        log "${YELLOW}Invalid history selection${NC}"
        return 1
    fi
    
    # Parse the entry
    local platform=$(echo "$entry" | cut -d'|' -f1)
    local dir_path=$(echo "$entry" | cut -d'|' -f2)
    
    if [ -z "$platform" ] || [ -z "$dir_path" ]; then
        log "${YELLOW}Invalid history entry${NC}"
        return 1
    fi
    
    # Set the global variables to navigate to this directory
    export TARGET_PLATFORM="$platform"
    export TARGET_DIR="$dir_path"
    
    log "${GREEN}Navigating to: $platform - $dir_path${NC}"
    return 0
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
        local files_filtered="$TEMP_DIR/files_filtered.txt"
        list_files "$index_file" "$files"
        
        # Apply filters
        apply_filters "$files" "$files_filtered"
        
        local total=$(wc -l < "$files_filtered" 2>/dev/null || echo 0)
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
        print_numbered_range "$files_filtered" "$page_start" "$PAGE_SIZE"
        echo ""
        echo -e "${CYAN}Commands: n/p (next/prev page), p-<num> (goto page), <num> (select file), <text> (search), -f (list), -f-edit, -f-out <word>, -f-in <word>, -history, .. (up), q (quit)${NC}"
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
                    # At root directory, stay at root but reset page
                    page_start=1
                else
                    page_start=1
                fi
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
            "-filter")
                if edit_filters; then
                    apply_filters "$files" "$files_filtered"
                    page_start=1
                fi
                ;;
            "-f")
                if [ -f "$FILTER_FILE" ]; then
                    log "${CYAN}Current filters:${NC}"
                    cat "$FILTER_FILE"
                else
                    log "${YELLOW}No filter file found${NC}"
                fi
                echo ""
                echo -e "${CYAN}Commands: n/p (next/prev page), p-<num> (goto page), <num> (select file), <text> (search), -f (list), -f-edit, -f-out <word>, -f-in <word>, -history, .. (up), q (quit)${NC}"
                echo -ne "${CYAN}Enter command: ${NC}"
                read -r cmd
                continue
                ;;
            "-f-edit")
                if edit_filters; then
                    apply_filters "$files" "$files_filtered"
                    page_start=1
                fi
                ;;
            -f-out*)
                local filter_word="${cmd#-f-out }"
                if add_filter "$filter_word"; then
                    apply_filters "$files" "$files_filtered"
                    page_start=1
                fi
                ;;
            -f-in*)
                local filter_word="${cmd#-f-in }"
                if remove_filter "$filter_word"; then
                    apply_filters "$files" "$files_filtered"
                    page_start=1
                fi
                ;;
            "-history")
                show_history
            echo ""
                echo -ne "${CYAN}Enter number to navigate to directory (or press Enter to continue):${NC} "
                read -r hist_choice
                if [[ "$hist_choice" =~ ^[1-5]$ ]]; then
                    if navigate_to_history "$hist_choice"; then
                        # Set the platform and directory for navigation
                        local hist_platform="$TARGET_PLATFORM"
                        local hist_dir="$TARGET_DIR"
                        unset TARGET_PLATFORM TARGET_DIR
                        
                        # Navigate to the selected directory
                        if [ -n "$hist_platform" ] && [ -n "$hist_dir" ]; then
                            # Find the platform index
                            local platform_index=""
                            case "$hist_platform" in
                                "Redump") platform_index="1" ;;
                                "No-Intro") platform_index="2" ;;
                                *) platform_index="2" ;; # default to No-Intro
                            esac
                            
                            # Set the platform and directory
                            export MYRIENT_BASE_URL="$([ "$platform_index" = "1" ] && echo "$BASE_URL_REDUMP" || echo "$BASE_URL_NOIN")"
                            export LAST_PLATFORM_INDEX="$platform_index"
                            rel="$hist_dir"
                            break
                        fi
                    fi
                fi
                ;;
            [0-9]*)
                local file_num="$cmd"
                if [ "$file_num" -ge 1 ] && [ "$file_num" -le "$total" ]; then
                    local selected_file=$(sed -n "${file_num}p" "$files_filtered")
                    if [ -n "$selected_file" ]; then
                        # Add to history when selecting a directory
                        if [[ "$selected_file" == */ ]]; then
                            add_to_history "$rel" "$platform"
                        fi
                        
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
                            local download_path="$DOWNLOADS_DIR/$filename"
                            log "${CYAN}Downloading: $filename${NC}"
                            if curl -L -s -o "$download_path" "$file_url"; then
                                log "${GREEN}Downloaded: $filename to $DOWNLOADS_DIR${NC}"
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
                grep -i "$cmd" "$files_filtered" > "$TEMP_DIR/search_results.txt" || true
                if [ -s "$TEMP_DIR/search_results.txt" ]; then
                    local search_total=$(wc -l < "$TEMP_DIR/search_results.txt")
                    echo -e "${CYAN}Search results (${search_total} matches):${NC}"
                    print_numbered_range "$TEMP_DIR/search_results.txt" 1 50
                    echo ""
                    echo -e "${CYAN}Commands: <num> (select from results), <start:end> (select range), .. (back to full list), q (cancel search)${NC}"
                    echo -ne "${CYAN}Enter command: ${NC}"
                    read -r search_cmd
                    
                    case "$search_cmd" in
                        "q")
                            # Cancel search and continue with normal browsing
                            break
                            ;;
                        "..")
                            # Continue with normal browsing
                            ;;
                        [0-9]*)
                            # Handle single number or range selection
                            local start_num end_num
                            if [[ "$search_cmd" =~ ^[0-9]+$ ]]; then
                                start_num="$search_cmd"
                                end_num="$search_cmd"
                            elif [[ "$search_cmd" =~ ^[0-9]+:[0-9]+$ ]]; then
                                start_num=$(echo "$search_cmd" | cut -d: -f1)
                                end_num=$(echo "$search_cmd" | cut -d: -f2)
                            else
                                log "${YELLOW}Invalid format. Use number (e.g., 5) or range (e.g., 1:50)${NC}"
                                continue
                            fi
                            
                            # Validate range
                            if [ "$start_num" -gt "$end_num" ]; then
                                log "${YELLOW}Invalid range: start must be <= end${NC}"
                                continue
                            fi
                            
                            if [ "$start_num" -lt 1 ] || [ "$end_num" -gt "$search_total" ]; then
                                log "${YELLOW}Invalid range: numbers must be between 1 and $search_total${NC}"
                                continue
                            fi
                            
                            # Handle single number selection (navigate directory or download file)
                            if [ "$start_num" -eq "$end_num" ]; then
                                local selected_file=$(sed -n "${start_num}p" "$TEMP_DIR/search_results.txt")
                                if [ -n "$selected_file" ]; then
                                    if [[ "$selected_file" == */ ]]; then
                                        # It's a directory - navigate to it
                                        local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                                        rel="${rel}${encoded_file}"
                                        page_start=1
                                        break
                                    else
                                        # It's a file - download it
                                        local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                                        local file_url="${url}${encoded_file}"
                                        local filename=$(basename "$selected_file")
                                        local download_path="$DOWNLOADS_DIR/$filename"
                                        log "${CYAN}Downloading: $filename${NC}"
                                        if curl -L -s -o "$download_path" "$file_url"; then
                                            log "${GREEN}Downloaded: $filename to $DOWNLOADS_DIR${NC}"
                                        else
                                            log "${RED}Failed to download: $filename${NC}"
                                        fi
                                    fi
                                else
                                    log "${YELLOW}Invalid file number${NC}"
                                fi
                            else
                                # Process each item in the range
                            local has_dirs=false
                            local files_to_download=()
                            
                            for ((i=start_num; i<=end_num; i++)); do
                                local selected_file=$(sed -n "${i}p" "$TEMP_DIR/search_results.txt")
                                if [ -n "$selected_file" ]; then
                                    if [[ "$selected_file" == */ ]]; then
                                        has_dirs=true
                                        log "${YELLOW}Cannot select directories in range. Skipping: $(basename "$selected_file")${NC}"
                                    else
                                        files_to_download+=("$selected_file")
                                    fi
                                fi
                            done
                            
                            # If we have directories, we can't proceed with range selection
                            if [ "$has_dirs" = true ] && [ ${#files_to_download[@]} -eq 0 ]; then
                                log "${YELLOW}Range contains only directories. Use single numbers to navigate directories.${NC}"
                                continue
                            fi
                            
                            # If we have directories and files, warn but continue with files only
                            if [ "$has_dirs" = true ] && [ ${#files_to_download[@]} -gt 0 ]; then
                                log "${YELLOW}Range contains directories which will be skipped. Processing ${#files_to_download[@]} files.${NC}"
                            fi
                            
                            # Process files
                            if [ ${#files_to_download[@]} -gt 0 ]; then
                                if [ ${#files_to_download[@]} -eq 1 ]; then
                                    # Single file - use existing logic
                                    local selected_file="${files_to_download[0]}"
                                    local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                                    local file_url="${url}${encoded_file}"
                                    local filename=$(basename "$selected_file")
                                    local download_path="$DOWNLOADS_DIR/$filename"
                                    log "${CYAN}Downloading: $filename${NC}"
                                    if curl -L -s -o "$download_path" "$file_url"; then
                                        log "${GREEN}Downloaded: $filename to $DOWNLOADS_DIR${NC}"
                                    else
                                        log "${RED}Failed to download: $filename${NC}"
                                    fi
                                else
                                    # Show selection menu for multiple files
                                    echo ""
                                    echo -e "${CYAN}Selected ${#files_to_download[@]} files:${NC}"
                                    for file in "${files_to_download[@]}"; do
                                        local filename=$(basename "$file")
                                        echo "  - $filename"
                                    done
                                    echo ""
                                    echo "  1) Print all URLs"
                                    echo "  2) Copy all URLs to clipboard"
                                    echo "  3) Download all files"
                                    echo "  4) Cancel"
                                    echo -ne "${CYAN}Choose [1-4]:${NC} "
                                    read -r batch_choice
                                    
                                    case "$batch_choice" in
                                        1)
                                            # Print all URLs
                                            for selected_file in "${files_to_download[@]}"; do
                                                local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                                                local file_url="${url}${encoded_file}"
                                                echo "$file_url"
                                            done
                                            ;;
                                        2)
                                            # Copy all URLs to clipboard
                                            local urls=""
                                            for selected_file in "${files_to_download[@]}"; do
                                                local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                                                local file_url="${url}${encoded_file}"
                                                urls="${urls}${file_url}\n"
                                            done
                                            if command -v clip.exe >/dev/null 2>&1; then
                                                printf "%s" "$urls" | clip.exe
                                                log "${GREEN}Copied ${#files_to_download[@]} URLs to clipboard${NC}"
                                            elif command -v clip >/dev/null 2>&1; then
                                                printf "%s" "$urls" | clip
                                                log "${GREEN}Copied ${#files_to_download[@]} URLs to clipboard${NC}"
                                            elif command -v pbcopy >/dev/null 2>&1; then
                                                printf "%s" "$urls" | pbcopy
                                                log "${GREEN}Copied ${#files_to_download[@]} URLs to clipboard${NC}"
                                            elif command -v xclip >/dev/null 2>&1; then
                                                printf "%s" "$urls" | xclip -selection clipboard
                                                log "${GREEN}Copied ${#files_to_download[@]} URLs to clipboard${NC}"
                                            else
                                                log "${YELLOW}Clipboard utility not found${NC}"
                                            fi
                                            ;;
                                        3)
                                            # Download all files
                                            log "${CYAN}Downloading ${#files_to_download[@]} files...${NC}"
                                            local success_count=0
                                            local fail_count=0
                                            for selected_file in "${files_to_download[@]}"; do
                                                local encoded_file=$(printf '%s\n' "$selected_file" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
                                                local file_url="${url}${encoded_file}"
                                                local filename=$(basename "$selected_file")
                                                local download_path="$DOWNLOADS_DIR/$filename"
                                                local current_num=$((success_count + fail_count + 1))
                                                log "${CYAN}Downloading [${current_num}/${#files_to_download[@]}]: $filename${NC}"
                                                if curl -L -s -o "$download_path" "$file_url"; then
                                                    log "${GREEN}Downloaded: $filename${NC}"
                                                    ((success_count++))
                                                else
                                                    log "${RED}Failed to download: $filename${NC}"
                                                    ((fail_count++))
                                                fi
                                            done
                                            log "${CYAN}Batch download complete: ${GREEN}${success_count} successful${NC}, ${RED}${fail_count} failed${NC}"
                                            ;;
                                        *) ;;
                                    esac
                                fi
                            fi
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
    
    # Create searchable results with dataset info
    local search_results="$TEMP_DIR/search_results.txt"
    > "$search_results"
    
    # Add Redump results with dataset prefix
    local count=1
    while IFS= read -r line; do
        if grep -qi "$query" <<< "$line"; then
            echo "1|$line" >> "$search_results"
            echo "  $count) [Redump] $line"
            count=$((count + 1))
        fi
    done < "$redump_file"
    
    # Add No-Intro results with dataset prefix
    while IFS= read -r line; do
        if grep -qi "$query" <<< "$line"; then
            echo "2|$line" >> "$search_results"
            echo "  $count) [No-Intro] $line"
            count=$((count + 1))
        fi
    done < "$nointro_file"
    
    local total_results=$((count - 1))
    if [ "$total_results" -eq 0 ]; then
        log "${YELLOW}No matches found${NC}"
        return 1
    fi
    
    echo ""
    echo -e "${CYAN}Found ${total_results} matches. Enter number to navigate directly, or 'q' to quit:${NC}"
    echo -ne "${CYAN}Enter choice: ${NC}"
    read -r choice
    
    if [ "$choice" = "q" ]; then
        return 1
    fi
    
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$total_results" ]; then
        local selected_line=$(sed -n "${choice}p" "$search_results")
        local dataset=$(echo "$selected_line" | cut -d'|' -f1)
        local platform=$(echo "$selected_line" | cut -d'|' -f2-)
        
        if [ "$dataset" = "1" ]; then
            MYRIENT_BASE_URL="$BASE_URL_REDUMP"
        else
            MYRIENT_BASE_URL="$BASE_URL_NOIN"
        fi
        
        log "${GREEN}Selected: $platform${NC}"
        # Convert decoded platform name back to URL-encoded for navigation
        local encoded_platform=$(printf '%s\n' "$platform" | sed 's/ /%20/g; s/&/%26/g; s/+/%2B/g; s/,/%2C/g; s/;/%3B/g; s/=/%3D/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\]/%5D/g')
        browse_dir "platform" "$encoded_platform"
        return 0
    else
        log "${RED}Invalid choice${NC}"
        return 1
    fi
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
        if search_platforms "$choice"; then
            return 0
        else
            exit 0
        fi
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
