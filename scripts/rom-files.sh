#!/bin/bash

# Myrient /files interactive browser for Git Bash (Windows) and Unix shells
# - Start at https://myrient.erista.me/files/
# - Navigate folders, filter by typing, select by number
# - For files: print URL, copy URL to clipboard (Windows clip.exe supported), or download

ROOT_URL="https://myrient.erista.me/files/"
TEMP_DIR="./temp"
DOWNLOAD_DIR="./downloads"
LOG_FILE="./mbrowse_log.txt"

mkdir -p "$TEMP_DIR" "$DOWNLOAD_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    echo -e "$1" | tee -a "$LOG_FILE" >&2
}

# Minimal urlencode for common characters used on Myrient
urlencode() {
    local s="$1"
    s=$(echo "$s" | sed 's/%/%25/g' | sed 's/ /%20/g' | sed 's/(/%28/g' | sed 's/)/%29/g' | sed 's/+/%2B/g' | sed 's/&/%26/g' | sed "s/'/%27/g" | sed 's/,/%2C/g' | sed 's/\[/\%5B/g' | sed 's/\]/\%5D/g')
    echo "$s"
}

# Decode common URL-encoded characters for display
urldecode_display() {
    echo "$1" | sed -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g' -e 's/%2B/+/g' -e 's/%26/&/g' -e "s/%27/'/g" -e 's/%2C/,/g' -e 's/%5[Bb]/[/g' -e 's/%5[Dd]/]/g'
}

download_index() {
    local url="$1"; local out="$2"
    curl -fsSL --compressed -H 'User-Agent: Mozilla/5.0 (Myrient CLI)' -o "$out" "$url"
}

# Extract directories as: name||href (href is relative, includes trailing /)
list_dirs_links() {
    local idx="$1"; local out="$2"
    : > "$out"
    # Filter anchors that look like directories and exclude sorting, parent, absolute links, and top navigation
    local raw_lines
    raw_lines=$(grep -E 'href="[^"]+/"' "$idx" \
        | grep -v '\?C=' \
        | grep -v '\.\./' \
        | grep -v 'href="/' \
        | grep -vi -E '(contact|donate|faq|upload|discord|telegram|hshop|home)')
    if [ -n "$raw_lines" ]; then
        echo "$raw_lines" | awk '
            BEGIN{IGNORECASE=1}
            {
                href=$0;
                sub(/.*href="/,"",href);
                sub(/".*/,"",href);
                disp=href;
                gsub(/\/$/,"",href); # clean for building rel
                gsub(/\/$/,"",disp);
                # Prefer title when available
                t=$0; sub(/.*title="/,"",t); if (t!=$0){ sub(/".*/,"",t); disp=t; }
                gsub(/%20/," ",disp); gsub(/%28/,"(",disp); gsub(/%29/,")",disp);
                gsub(/%2B/,"+",disp); gsub(/%26/,"&",disp); gsub(/%27/,"'\''",disp); gsub(/%2C/,",",disp);
                gsub(/%5[Bb]/,"[",disp); gsub(/%5[Dd]/,"]",disp);
                print disp "||" href "/";
            }
        ' > "$out"
    fi
}

# Extract files as: name||href (href is relative to current URL)
list_files_links() {
    local idx="$1"; local out="$2"
    : > "$out"
    local raw_lines
    raw_lines=$(grep -E 'href="[^"]+"' "$idx" \
        | grep -v '\?C=' \
        | grep -v 'href="[^"]*/"' \
        | grep -v 'href="/' \
        | grep -v 'href="https\?://' \
        | grep -vi -E '(contact|donate|faq|upload|discord|telegram|hshop|home|Parent directory)')
    if [ -n "$raw_lines" ]; then
        echo "$raw_lines" | awk '
            BEGIN{IGNORECASE=1}
            {
                href=$0;
                sub(/.*href="/,"",href);
                sub(/".*/,"",href);
                disp=href;
                gsub(/%20/," ",disp); gsub(/%28/,"(",disp); gsub(/%29/,")",disp);
                gsub(/%2B/,"+",disp); gsub(/%26/,"&",disp); gsub(/%27/,"'\''",disp); gsub(/%2C/,",",disp);
                gsub(/%5[Bb]/,"[",disp); gsub(/%5[Dd]/,"]",disp);
                print disp "||" href;
            }
        ' > "$out"
    fi
}

print_numbered_data() {
    local data_file="$1"; local limit="$2"
    [ -z "$limit" ] && limit=500
    awk -F"\\|\\|" '{printf("%2d. %s %s\n", NR, $1, $2)}' "$data_file" | head -n "$limit"
}

copy_to_clipboard() {
    local text="$1"
    if command -v clip.exe >/dev/null 2>&1; then
        printf "%s" "$text" | clip.exe
        return 0
    elif command -v clip >/dev/null 2>&1; then
        printf "%s" "$text" | clip
        return 0
    elif command -v pbcopy >/dev/null 2>&1; then
        printf "%s" "$text" | pbcopy
        return 0
    elif command -v xclip >/dev/null 2>&1; then
        printf "%s" "$text" | xclip -selection clipboard
        return 0
    fi
    return 1
}

download_file() {
    local url="$1"; local out_path="$2"
    curl -L -C - --progress-bar --retry 3 --retry-delay 5 -o "$out_path" "$url"
}

file_actions() {
    local base_url="$1"; local rel="$2"; local disp_name="$3"; local href="$4"
    local full_url="${base_url}${rel}${href}"
    echo ""
    echo -e "${CYAN}Selected:${NC} $disp_name"
    echo "  1) Print URL"
    echo "  2) Copy URL to clipboard"
    echo "  3) Download now"
    echo "  4) Cancel"
    echo -ne "${CYAN}Choose [1-4]:${NC} "
    read act
    case "$act" in
        1)
            echo "$full_url"
            ;;
        2)
            if copy_to_clipboard "$full_url"; then
                log "${GREEN}Copied to clipboard${NC}"
            else
                log "${YELLOW}Clipboard utility not found${NC}"
            fi
            ;;
        3)
            local fname_enc
            fname_enc=$(basename "$href")
            local fname
            fname=$(urldecode_display "$fname_enc")
            echo -e "${CYAN}Downloading:${NC} $fname"
            if download_file "$full_url" "$DOWNLOAD_DIR/$fname"; then
                echo -e "${GREEN}Downloaded successfully${NC}"
            else
                echo -e "${RED}Download failed${NC}"
            fi
            ;;
        *) ;;
    esac
}

batch_file_actions() {
    local base_url="$1"; local rel="$2"; shift 2
    local files=("$@")
    local count=${#files[@]}
    
    echo ""
    echo -e "${CYAN}Selected ${count} files:${NC}"
    for file in "${files[@]}"; do
        local name
        name=$(echo "$file" | awk -F"\\|\\|" '{print $1}')
        echo "  - $name"
    done
    echo ""
    echo "  1) Print all URLs"
    echo "  2) Copy all URLs to clipboard"
    echo "  3) Download all files"
    echo "  4) Cancel"
    echo -ne "${CYAN}Choose [1-4]:${NC} "
    read act
    
    case "$act" in
        1)
            for file in "${files[@]}"; do
                local name href
                name=$(echo "$file" | awk -F"\\|\\|" '{print $1}')
                href=$(echo "$file" | awk -F"\\|\\|" '{print $2}')
                local full_url="${base_url}${rel}${href}"
                echo "$full_url"
            done
            ;;
        2)
            local urls=""
            for file in "${files[@]}"; do
                local name href
                name=$(echo "$file" | awk -F"\\|\\|" '{print $1}')
                href=$(echo "$file" | awk -F"\\|\\|" '{print $2}')
                local full_url="${base_url}${rel}${href}"
                urls="${urls}${full_url}\n"
            done
            if copy_to_clipboard "$urls"; then
                log "${GREEN}Copied ${count} URLs to clipboard${NC}"
            else
                log "${YELLOW}Clipboard utility not found${NC}"
            fi
            ;;
        3)
            local success_count=0
            local fail_count=0
            for file in "${files[@]}"; do
                local name href
                name=$(echo "$file" | awk -F"\\|\\|" '{print $1}')
                href=$(echo "$file" | awk -F"\\|\\|" '{print $2}')
                local full_url="${base_url}${rel}${href}"
                local fname_enc
                fname_enc=$(basename "$href")
                local fname
                fname=$(urldecode_display "$fname_enc")
                echo -e "${CYAN}Downloading [${success_count + fail_count + 1}/${count}]:${NC} $fname"
                if download_file "$full_url" "$DOWNLOAD_DIR/$fname"; then
                    echo -e "${GREEN}Downloaded successfully${NC}"
                    ((success_count++))
                else
                    echo -e "${RED}Download failed${NC}"
                    ((fail_count++))
                fi
            done
            echo -e "${CYAN}Batch download complete: ${GREEN}${success_count} successful${NC}, ${RED}${fail_count} failed${NC}"
            ;;
        *) ;;
    esac
}

browse() {
    local rel_path="${1:-}"
    while true; do
        local url="${ROOT_URL}${rel_path}"
        local idx="$TEMP_DIR/index.html"
        if ! download_index "$url" "$idx"; then
            log "${RED}Failed to load index${NC}"
            return 1
        fi

        local dirs="$TEMP_DIR/dirs_links.txt"
        local files="$TEMP_DIR/files_links.txt"
        list_dirs_links "$idx" "$dirs"
        list_files_links "$idx" "$files"

        local combined="$TEMP_DIR/combined.txt"
        : > "$combined"
        if [ -s "$dirs" ]; then awk -F"\\|\\|" '{print "D||"$1"||"$2}' "$dirs" >> "$combined"; fi
        if [ -s "$files" ]; then awk -F"\\|\\|" '{print "F||"$1"||"$2}' "$files" >> "$combined"; fi

        if [ ! -s "$combined" ]; then
            log "${YELLOW}No entries found here${NC}"
            return 0
        fi

        local active="$TEMP_DIR/active.txt"
        cp "$combined" "$active"

        while true; do
            echo ""
            echo -e "${CYAN}Path:${NC} /files/${rel_path}"
            echo -e "${CYAN}Entries (D=dir, F=file):${NC}"
            print_numbered_data "$active" 500
            echo -ne "${CYAN}Enter number to open/select, range (e.g., 1:50), '..' up, filter text, or 'q' quit:${NC} "
            read input
            [ -z "$input" ] && continue
            if [ "$input" = "q" ]; then
                return 0
            fi
            if [ "$input" = ".." ]; then
                rel_path="${rel_path%/}"
                rel_path="${rel_path%/*}/"
                break
            fi
            if [[ "$input" =~ ^[0-9]+$ ]] || [[ "$input" =~ ^[0-9]+:[0-9]+$ ]]; then
                # Handle single number or range selection
                local start_num end_num
                if [[ "$input" =~ ^[0-9]+$ ]]; then
                    start_num="$input"
                    end_num="$input"
                else
                    start_num=$(echo "$input" | cut -d: -f1)
                    end_num=$(echo "$input" | cut -d: -f2)
                fi
                
                # Validate range
                if [ "$start_num" -gt "$end_num" ]; then
                    log "${YELLOW}Invalid range: start must be <= end${NC}"
                    continue
                fi
                
                # Check if any numbers are out of bounds
                local total_lines
                total_lines=$(wc -l < "$active")
                if [ "$start_num" -lt 1 ] || [ "$end_num" -gt "$total_lines" ]; then
                    log "${YELLOW}Invalid range: numbers must be between 1 and $total_lines${NC}"
                    continue
                fi
                
                # Process each item in the range
                local has_dirs=false
                local files_to_process=()
                
                for ((i=start_num; i<=end_num; i++)); do
                    local line
                    line=$(sed -n "${i}p" "$active")
                    if [ -z "$line" ]; then
                        log "${YELLOW}Invalid index: $i${NC}"
                        continue
                    fi
                    
                    local type name href
                    type=$(echo "$line" | awk -F"\\|\\|" '{print $1}')
                    name=$(echo "$line" | awk -F"\\|\\|" '{print $2}')
                    href=$(echo "$line" | awk -F"\\|\\|" '{print $3}')
                    
                    if [ "$type" = "D" ]; then
                        has_dirs=true
                        log "${YELLOW}Cannot select directories in range. Skipping: $name${NC}"
                    else
                        files_to_process+=("$name||$href")
                    fi
                done
                
                # If we have directories, we can't proceed with range selection
                if [ "$has_dirs" = true ] && [ ${#files_to_process[@]} -eq 0 ]; then
                    log "${YELLOW}Range contains only directories. Use single numbers to navigate directories.${NC}"
                    continue
                fi
                
                # If we have directories and files, warn but continue with files only
                if [ "$has_dirs" = true ] && [ ${#files_to_process[@]} -gt 0 ]; then
                    log "${YELLOW}Range contains directories which will be skipped. Processing ${#files_to_process[@]} files.${NC}"
                fi
                
                # Process files
                if [ ${#files_to_process[@]} -gt 0 ]; then
                    if [ ${#files_to_process[@]} -eq 1 ]; then
                        # Single file - use existing file_actions
                        local name href
                        name=$(echo "${files_to_process[0]}" | awk -F"\\|\\|" '{print $1}')
                        href=$(echo "${files_to_process[0]}" | awk -F"\\|\\|" '{print $2}')
                        file_actions "$ROOT_URL" "$rel_path" "$name" "$href"
                    else
                        # Multiple files - batch processing
                        batch_file_actions "$ROOT_URL" "$rel_path" "${files_to_process[@]}"
                    fi
                    continue
                fi
            fi
            # Treat as filter on name
            awk -F"\\|\\|" -v term="$input" 'BEGIN{IGNORECASE=1} index($2, term)>0 {print $0}' "$active" > "$TEMP_DIR/active_f.txt" || true
            if [ -s "$TEMP_DIR/active_f.txt" ]; then
                mv "$TEMP_DIR/active_f.txt" "$active"
            else
                log "${YELLOW}No matches${NC}"
            fi
        done
    done
}

main() {
    log "${CYAN}Myrient CLI browser - starting at ${ROOT_URL}${NC}"
    browse ""
}

main "$@"


