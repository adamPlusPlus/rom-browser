#!/bin/bash

# Minimal Myrient browser (non-destructive). Uses helpers from universal_rom_downloader.sh by duplicating essential logic.

BASE_URL_REDUMP="https://myrient.erista.me/files/Redump/"
BASE_URL_NOIN="https://myrient.erista.me/files/No-Intro/"
MYRIENT_BASE_URL="$BASE_URL_REDUMP"
TEMP_DIR="./temp"
DOWNLOAD_DIR="./downloads"
QUEUE_FILE="./download_queue"
LOG_FILE="./mbrowse_log.txt"

mkdir -p "$TEMP_DIR" "$DOWNLOAD_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Options
HIDE_ADDONS="0"    # 1 = hide entries whose display name contains " (Addon"
HIDE_DLC="0"       # 1 = hide entries whose display name contains " (DLC"
HIDE_EXTRAS=""     # empty = use platform-specific default; 0/1 = override
HIDE_MAC=""        # empty = use platform-specific default; 0/1 = override
HIDE_LINUX=""      # empty = use platform-specific default; 0/1 = override
HIDE_PATCH=""      # empty = use platform-specific default; 0/1 = override
PAGE_SIZE="50"     # items per page in file lists

log() { echo -e "$1" | tee -a "$LOG_FILE" >&2; }

urlencode() {
    local s="$1"
    s=$(echo "$s" | sed 's/ /%20/g' | sed 's/(/%28/g' | sed 's/)/%29/g' | sed 's/+/%2B/g' | sed 's/&/%26/g' | sed "s/'/%27/g" | sed 's/,/%2C/g')
    echo "$s"
}

platform_url() {
    local platform="$1"
    echo "${MYRIENT_BASE_URL}$(urlencode "$platform")/"
}

dataset_name() {
    if [ "$MYRIENT_BASE_URL" = "$BASE_URL_REDUMP" ]; then echo "Redump"; else echo "No-Intro"; fi
}

download_index() {
    local url="$1"; local out="$2"
    curl -s --compressed -o "$out" "$url"
}

list_dirs() {
    local idx="$1"
    local out="$2"
    : > "$out"
    local raw_lines
    raw_lines=$(grep -E 'href="[^"]+/"' "$idx" \
      | grep -v '\?C=' \
      | grep -v '\.\./' \
      | grep -v 'href="https\?://' \
      | grep -v 'href="/' \
      | grep -vi -E '(contact/|donate/|faq/|files/|upload|discord|telegram|hshop)')
    if [ -n "$raw_lines" ]; then
        echo "$raw_lines" | sed -n 's/.*title="\([^"]*\)".*/\1/p' | sed 's:/$::' | sed '/^$/d' > "$out"
        if [ ! -s "$out" ]; then
            # Fallback: extract last path segment from href, decode readable chars
            echo "$raw_lines" | sed -n 's/.*href="\([^"]*\/\)".*/\1/p' \
              | sed 's:/$::' \
              | awk -F'/' '{print $NF}' \
              | sed -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g' -e 's/%2B/+/g' -e 's/%26/&/g' -e "s/%27/'/g" -e 's/%2C/,/g' \
              > "$out"
        fi
    fi
}

list_archives_flat() {
    local idx="$1"; local out="$2"
    : > "$out"
    awk '
        BEGIN{IGNORECASE=1}
        /href="[^"]*\.(zip|7z)"/{
            href=$0;
            sub(/.*href="/,"",href);
            sub(/".*/,"",href);
            disp=href;
            gsub(/%20/," ",disp); gsub(/%28/,"(",disp); gsub(/%29/,")",disp);
            gsub(/%2B/,"+",disp); gsub(/%26/,"&",disp); gsub(/%27/,"\047",disp); gsub(/%2C/,",",disp);
            gsub(/\.zip$/,"",disp); gsub(/\.7z$/,"",disp);
            print disp "||" href;
        }
    ' "$idx" > "$out"
}

print_numbered() {
    local file="$1"; local limit="$2"
    [ -z "$limit" ] && limit=200
    nl -w2 -s'. ' "$file" | head -n "$limit"
}

# Print a page range with absolute numbering aligned to the original file
print_numbered_range() {
    local file="$1"; local start="$2"; local size="$3"
    [ -z "$start" ] && start=1
    [ -z "$size" ] && size=200
    local end=$((start+size-1))
    if [ ! -s "$file" ]; then return 0; fi
    sed -n "${start},${end}p" "$file" | nl -w2 -s'. ' -v "$start"
}

# Print filtered matches using original indices from the full list
print_indexed_matches() {
    local master_file="$1"; local filtered_file="$2"; local limit="$3"
    [ -z "$limit" ] && limit=200
    local shown=0
    while IFS= read -r line; do
        # Find first matching line number in master (exact line match)
        local idx=$(grep -n -F -x -- "$line" "$master_file" | head -n1 | cut -d: -f1)
        if [ -n "$idx" ]; then
            printf "%d. %s\n" "$idx" "$line"
            shown=$((shown+1))
            [ "$shown" -ge "$limit" ] && break
        fi
    done < "$filtered_file"
}

print_collapsed_summary() {
    local file="$1"
    local prev_key=""; local start=0; local i=0
    while IFS= read -r line; do
        i=$((i+1))
        local key=$(echo "$line" | awk '{print $1}')
        if [ -z "$prev_key" ]; then
            prev_key="$key"; start=$i; continue
        fi
        if [ "$key" != "$prev_key" ]; then
            if [ $start -eq $((i-1)) ]; then
                printf "%d:%d %s\n" "$start" "$((i-1))" "$prev_key"
            else
                printf "%d:%d %s\n" "$start" "$((i-1))" "$prev_key"
            fi
            prev_key="$key"; start=$i
        fi
    done < "$file"
    if [ -n "$prev_key" ]; then
        printf "%d:%d %s\n" "$start" "$i" "$prev_key"
    fi
}

browse_dir() {
    local platform="$1"; local rel="${2:-}"
    while true; do
        local url="$(platform_url "$platform")${rel}"
        local idx="$TEMP_DIR/idx.html"
        if ! download_index "$url" "$idx"; then
            log "${RED}Failed to load index${NC}"; return 1
        fi
        local dirs="$TEMP_DIR/dirs.txt"; list_dirs "$idx" "$dirs"
        if [ -s "$dirs" ]; then
            echo -e "${CYAN}Folders:${NC}"
            print_numbered "$dirs" 500
            echo -ne "${CYAN}Folder (type to filter, number to open, '..' up, q quit):${NC} "
            read inp
            if [ "$inp" = "q" ]; then return 1; fi
            if [ "$inp" = ".." ]; then
                rel="${rel%/}"; rel="${rel%/*}/"; continue
            fi
            if [[ "$inp" =~ ^[0-9]+$ ]]; then
                local name=$(sed -n "${inp}p" "$dirs")
                if [ -n "$name" ]; then rel="${rel}${name}/"; continue; fi
            fi
            # filter
            grep -i -- "$inp" "$dirs" > "$TEMP_DIR/dirs_f.txt" || true
            if [ -s "$TEMP_DIR/dirs_f.txt" ]; then
                cp "$TEMP_DIR/dirs_f.txt" "$dirs"
            else
                log "${YELLOW}No matches${NC}"
            fi
            continue
        fi
        # No subdirs, list files to pick with paging and filters
        local files="$TEMP_DIR/files.txt"; list_archives_flat "$idx" "$files"
        if [ ! -s "$files" ]; then
            log "${YELLOW}Empty folder${NC}"; return 1
        fi
        # Build full display list and apply addon filtering if enabled
        cut -d'|' -f1 "$files" > "$TEMP_DIR/files_disp_all.txt"
        local disp_all="$TEMP_DIR/files_disp_all.txt"
        local disp_active="$TEMP_DIR/files_disp_active.txt"
        cp "$disp_all" "$disp_active"
        # Hide XBLIG by default for No-Intro -> Microsoft - Xbox 360 (Digital)
        local hide_xblig=0
        if [ "$MYRIENT_BASE_URL" = "$BASE_URL_NOIN" ] && [ "$platform" = "Microsoft - Xbox 360 (Digital)" ]; then
            hide_xblig=1
        fi
        # Decide default Extras/Mac/Linux/Patch hiding: by default hide everywhere
        local extras_hide_flag="${HIDE_EXTRAS:-1}"
        local mac_hide_flag="${HIDE_MAC:-1}"
        local linux_hide_flag="${HIDE_LINUX:-1}"
        local patch_hide_flag="${HIDE_PATCH:-1}"
        if [ "$HIDE_ADDONS" = "1" ]; then
            grep -vi " (Addon" "$disp_active" > "$TEMP_DIR/tmp.filter" || true
            mv "$TEMP_DIR/tmp.filter" "$disp_active"
        fi
        if [ "$HIDE_DLC" = "1" ]; then
            grep -vi " (DLC" "$disp_active" > "$TEMP_DIR/tmp.filter" || true
            mv "$TEMP_DIR/tmp.filter" "$disp_active"
        fi
        if [ "$extras_hide_flag" = "1" ]; then
            grep -vi " (Extra)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true
            mv "$TEMP_DIR/tmp.filter" "$disp_active"
        fi
        if [ "$mac_hide_flag" = "1" ]; then
            grep -vi " (Mac)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true
            mv "$TEMP_DIR/tmp.filter" "$disp_active"
        fi
        if [ "$linux_hide_flag" = "1" ]; then
            grep -vi " (Linux)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true
            mv "$TEMP_DIR/tmp.filter" "$disp_active"
        fi
        if [ "$patch_hide_flag" = "1" ]; then
            grep -vi " (Patch)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true
            mv "$TEMP_DIR/tmp.filter" "$disp_active"
        fi
        if [ "$hide_xblig" = "1" ]; then
            grep -vi " (XBLIG" "$disp_active" > "$TEMP_DIR/tmp.filter" || true
            mv "$TEMP_DIR/tmp.filter" "$disp_active"
        fi
        # Reset paging on entry
        local page_size="$PAGE_SIZE"; local page_start=1
        while true; do
            local total=$(wc -l < "$disp_active" 2>/dev/null || echo 0)
            if [ "$total" -le 0 ]; then
                log "${YELLOW}No titles${NC}"; break
            fi
            local page_end=$((page_start+page_size-1))
            if [ "$page_end" -gt "$total" ]; then page_end="$total"; fi
            local total_pages=$(((total + page_size - 1) / page_size))
            local current_page=$(((page_start - 1) / page_size + 1))
            echo -e "${CYAN}Titles (${page_start}-${page_end} of ${total}) [Page ${current_page}/${total_pages}] [n/p page, p-<num> goto page, a addons, d dlc, e extras, m mac, l linux, t patch, ps <n> size, multi: '1 3 7']:${NC}"
            print_numbered_range "$disp_active" "$page_start" "$page_size"
            echo -e "${CYAN}[n/p page, p-<num> goto page, a addons, d dlc, e extras, m mac, l linux, t patch, ps <n> size, multi: '1 3 7']${NC}"
            echo -ne "${CYAN}Title (# or space-separated #s, text filter, '..' up, n/p, p-<num>, a, d, e, m, l, t, q):${NC} "
        read tinp
        if [ "$tinp" = "q" ]; then return 1; fi
            if [ "$tinp" = ".." ]; then rel="${rel%/}"; rel="${rel%/*}/"; break; fi
            if [ "$tinp" = "n" ]; then
                if [ $((page_start+page_size)) -le "$total" ]; then page_start=$((page_start+page_size)); else log "${YELLOW}End of list${NC}"; fi
                continue
            fi
            if [ "$tinp" = "p" ]; then
                if [ $((page_start-page_size)) -ge 1 ]; then page_start=$((page_start-page_size)); else log "${YELLOW}At start${NC}"; fi
                continue
            fi
            if [[ "$tinp" =~ ^ps[[:space:]]*([0-9]+)$ ]]; then
                page_size="${BASH_REMATCH[1]}"; page_start=1; continue
            fi
            if [[ "$tinp" =~ ^p-([0-9]+)$ ]]; then
                local target_page="${BASH_REMATCH[1]}"
                local max_page=$(((total + page_size - 1) / page_size))
                if [ "$target_page" -ge 1 ] && [ "$target_page" -le "$max_page" ]; then
                    page_start=$(((target_page - 1) * page_size + 1))
                else
                    log "${YELLOW}Invalid page number. Range: 1-${max_page}${NC}"
                fi
                continue
            fi
            if [ "$tinp" = "a" ]; then
                if [ "$HIDE_ADDONS" = "1" ]; then HIDE_ADDONS="0"; else HIDE_ADDONS="1"; fi
                cp "$disp_all" "$disp_active"
                if [ "$HIDE_ADDONS" = "1" ]; then grep -vi " (Addon" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$HIDE_DLC" = "1" ]; then grep -vi " (DLC" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_EXTRAS:-1}" = "1" ]; then grep -vi " (Extra)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_MAC:-1}" = "1" ]; then grep -vi " (Mac)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_LINUX:-1}" = "1" ]; then grep -vi " (Linux)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_PATCH:-1}" = "1" ]; then grep -vi " (Patch)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$hide_xblig" = "1" ]; then grep -vi " (XBLIG" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                page_start=1; continue
            fi
            if [ "$tinp" = "d" ]; then
                if [ "$HIDE_DLC" = "1" ]; then HIDE_DLC="0"; else HIDE_DLC="1"; fi
                cp "$disp_all" "$disp_active"
                if [ "$HIDE_ADDONS" = "1" ]; then grep -vi " (Addon" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$HIDE_DLC" = "1" ]; then grep -vi " (DLC" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_EXTRAS:-1}" = "1" ]; then grep -vi " (Extra)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_MAC:-1}" = "1" ]; then grep -vi " (Mac)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_LINUX:-1}" = "1" ]; then grep -vi " (Linux)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_PATCH:-1}" = "1" ]; then grep -vi " (Patch)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$hide_xblig" = "1" ]; then grep -vi " (XBLIG" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                page_start=1; continue
            fi
            if [ "$tinp" = "e" ]; then
                if [ "${HIDE_EXTRAS:-1}" = "1" ]; then HIDE_EXTRAS="0"; else HIDE_EXTRAS="1"; fi
                cp "$disp_all" "$disp_active"
                if [ "$HIDE_ADDONS" = "1" ]; then grep -vi " (Addon" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$HIDE_DLC" = "1" ]; then grep -vi " (DLC" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_EXTRAS:-1}" = "1" ]; then grep -vi " (Extra)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_MAC:-1}" = "1" ]; then grep -vi " (Mac)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_LINUX:-1}" = "1" ]; then grep -vi " (Linux)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_PATCH:-1}" = "1" ]; then grep -vi " (Patch)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$hide_xblig" = "1" ]; then grep -vi " (XBLIG" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                page_start=1; continue
            fi
            if [ "$tinp" = "m" ]; then
                if [ "${HIDE_MAC:-1}" = "1" ]; then HIDE_MAC="0"; else HIDE_MAC="1"; fi
                cp "$disp_all" "$disp_active"
                if [ "$HIDE_ADDONS" = "1" ]; then grep -vi " (Addon" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$HIDE_DLC" = "1" ]; then grep -vi " (DLC" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_EXTRAS:-1}" = "1" ]; then grep -vi " (Extra)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_MAC:-1}" = "1" ]; then grep -vi " (Mac)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_LINUX:-1}" = "1" ]; then grep -vi " (Linux)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_PATCH:-1}" = "1" ]; then grep -vi " (Patch)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$hide_xblig" = "1" ]; then grep -vi " (XBLIG" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                page_start=1; continue
            fi
            if [ "$tinp" = "l" ]; then
                if [ "${HIDE_LINUX:-1}" = "1" ]; then HIDE_LINUX="0"; else HIDE_LINUX="1"; fi
                cp "$disp_all" "$disp_active"
                if [ "$HIDE_ADDONS" = "1" ]; then grep -vi " (Addon" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$HIDE_DLC" = "1" ]; then grep -vi " (DLC" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_EXTRAS:-1}" = "1" ]; then grep -vi " (Extra)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_MAC:-1}" = "1" ]; then grep -vi " (Mac)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_LINUX:-1}" = "1" ]; then grep -vi " (Linux)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_PATCH:-1}" = "1" ]; then grep -vi " (Patch)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$hide_xblig" = "1" ]; then grep -vi " (XBLIG" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                page_start=1; continue
            fi
            if [ "$tinp" = "t" ]; then
                if [ "${HIDE_PATCH:-1}" = "1" ]; then HIDE_PATCH="0"; else HIDE_PATCH="1"; fi
                cp "$disp_all" "$disp_active"
                if [ "$HIDE_ADDONS" = "1" ]; then grep -vi " (Addon" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$HIDE_DLC" = "1" ]; then grep -vi " (DLC" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_EXTRAS:-1}" = "1" ]; then grep -vi " (Extra)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_MAC:-1}" = "1" ]; then grep -vi " (Mac)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_LINUX:-1}" = "1" ]; then grep -vi " (Linux)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_PATCH:-1}" = "1" ]; then grep -vi " (Patch)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$hide_xblig" = "1" ]; then grep -vi " (XBLIG" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                page_start=1; continue
            fi
            # Multi-select: space-separated list of numbers
            if [[ "$tinp" =~ ^[0-9]+(\ [0-9]+)*$ ]]; then
                local nums=( $tinp )
                local sels_disp="$TEMP_DIR/sel_disp.txt"; : > "$sels_disp"
                local sels_href="$TEMP_DIR/sel_href.txt"; : > "$sels_href"
                local ok=0
                for n in "${nums[@]}"; do
                    local disp=$(sed -n "${n}p" "$disp_active")
                    if [ -z "$disp" ]; then continue; fi
                    local href=$(grep -F "${disp}||" "$files" | head -n1 | sed 's/^.*||//')
                    if [ -z "$href" ]; then continue; fi
                    echo "$disp" >> "$sels_disp"
                    echo "$href" >> "$sels_href"
                    ok=$((ok+1))
                done
                if [ "$ok" -le 0 ]; then log "${YELLOW}No valid selections${NC}"; continue; fi
                echo ""
                echo -e "${CYAN}Selected ${ok} item(s). Apply action to all:${NC}"
                echo "  1) Add to queue (beginning)"
                echo "  2) Add to queue (end)"
                echo "  3) Download now"
                echo "  4) Cancel"
                echo -ne "${CYAN}Choose [1-4]:${NC} "
                read act
                local ds_name=$(dataset_name)
                if [ "$act" = "1" ]; then
                    local tmpq="$TEMP_DIR/queue.tmp"; : > "$tmpq"
                    paste -d'|' "$sels_disp" "$sels_href" | while IFS='|' read -r disp href; do
                        echo "dataset=$ds_name platform=$platform path=${rel}${href} title=$disp" >> "$tmpq"
                    done
                    if [ -f "$QUEUE_FILE" ]; then cat "$QUEUE_FILE" >> "$tmpq"; fi
                    mv "$tmpq" "$QUEUE_FILE"
                    log "${GREEN}Added ${ok} to queue (beginning)${NC}"
                    continue
                elif [ "$act" = "2" ]; then
                    paste -d'|' "$sels_disp" "$sels_href" | while IFS='|' read -r disp href; do
                        echo "dataset=$ds_name platform=$platform path=${rel}${href} title=$disp" >> "$QUEUE_FILE"
                    done
                    log "${GREEN}Added ${ok} to queue (end)${NC}"
                    continue
                elif [ "$act" = "3" ]; then
                    paste -d'|' "$sels_disp" "$sels_href" | while IFS='|' read -r disp href; do
                        local dl_url="$(platform_url "$platform")${rel}${href}"
                        local fname_enc=$(basename "$href")
                        local fname=$(echo "$fname_enc" | sed -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g' -e 's/%2B/+/g' -e 's/%26/&/g' -e "s/%27/'/g" -e 's/%2C/,/g')
                        echo -e "${CYAN}Downloading:${NC} $fname"
                        if curl -L -C - --progress-bar --retry 3 --retry-delay 5 -o "$DOWNLOAD_DIR/$fname" "$dl_url"; then
                            echo -e "${GREEN}Downloaded successfully${NC}"
                        else
                            echo -e "${RED}Download failed${NC}"
                        fi
                    done
                    continue
                else
                    continue
                fi
            fi
        if [[ "$tinp" =~ ^[0-9]+$ ]]; then
                local disp=$(sed -n "${tinp}p" "$disp_active")
                if [ -z "$disp" ]; then log "${YELLOW}Invalid index${NC}"; continue; fi
            local href=$(grep -F "${disp}||" "$files" | head -n1 | sed 's/^.*||//')
                if [ -z "$href" ]; then log "${YELLOW}Mapping not found${NC}"; continue; fi
            # Action prompt
            echo ""
            echo -e "${CYAN}Selected:${NC} $disp"
            echo "  1) Add to queue (beginning)"
            echo "  2) Add to queue (end)"
            echo "  3) Download now"
            echo "  4) Cancel"
            echo -ne "${CYAN}Choose [1-4]:${NC} "
            read act
            local ds_name=$(dataset_name)
            local qline="dataset=$ds_name platform=$platform path=${rel}${href} title=$disp"
            if [ "$act" = "1" ]; then
                local tmpq="$TEMP_DIR/queue.tmp"
                echo "$qline" > "$tmpq"
                if [ -f "$QUEUE_FILE" ]; then cat "$QUEUE_FILE" >> "$tmpq"; fi
                mv "$tmpq" "$QUEUE_FILE"
                log "${GREEN}Added to queue (beginning)${NC}"
                continue
            elif [ "$act" = "2" ]; then
                echo "$qline" >> "$QUEUE_FILE"
                log "${GREEN}Added to queue (end)${NC}"
                continue
            elif [ "$act" = "3" ]; then
                local dl_url="$(platform_url "$platform")${rel}${href}"
                # Derive filename from href (keep encoded or decode common parts)
                local fname_enc=$(basename "$href")
                local fname=$(echo "$fname_enc" | sed -e 's/%20/ /g' -e 's/%28/(/g' -e 's/%29/)/g' -e 's/%2B/+/g' -e 's/%26/&/g' -e "s/%27/'/g" -e 's/%2C/,/g')
                echo -e "${CYAN}Downloading:${NC} $fname"
                if curl -L -C - --progress-bar --retry 3 --retry-delay 5 -o "$DOWNLOAD_DIR/$fname" "$dl_url"; then
                    echo -e "${GREEN}Downloaded successfully${NC}"
                else
                    echo -e "${RED}Download failed${NC}"
                fi
                continue
            else
                # cancel
                continue
            fi
        fi
            # text filter (case-insensitive) over the full display list, then re-apply addon/DLC/Extras/Mac/Linux/Patch/XBLIG filters
            grep -i -- "$tinp" "$disp_all" > "$TEMP_DIR/files_f_base.txt" || true
            if [ -s "$TEMP_DIR/files_f_base.txt" ]; then
                mv "$TEMP_DIR/files_f_base.txt" "$disp_active"
                if [ "$HIDE_ADDONS" = "1" ]; then grep -vi " (Addon" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$HIDE_DLC" = "1" ]; then grep -vi " (DLC" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_EXTRAS:-1}" = "1" ]; then grep -vi " (Extra)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_MAC:-1}" = "1" ]; then grep -vi " (Mac)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_LINUX:-1}" = "1" ]; then grep -vi " (Linux)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "${HIDE_PATCH:-1}" = "1" ]; then grep -vi " (Patch)" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                if [ "$hide_xblig" = "1" ]; then grep -vi " (XBLIG" "$disp_active" > "$TEMP_DIR/tmp.filter" || true; mv "$TEMP_DIR/tmp.filter" "$disp_active"; fi
                page_start=1
            else
                log "${YELLOW}No matches${NC}"
            fi
        done
    done
}

main() {
    echo ""; log "${CYAN}Select dataset or quick-jump (e.g., 1-177 or 1-microsoft):${NC}"
    echo "  1) Redump"; echo "  2) No-Intro"
    read -p "Enter choice or 1-<n>/2-<n> (or 'q' to exit): " ds
    if [ "$ds" = "q" ]; then exit 0; fi
    if [[ "$ds" =~ ^([12])-([0-9]+)$ ]]; then
        if [ "${BASH_REMATCH[1]}" = "1" ]; then MYRIENT_BASE_URL="$BASE_URL_REDUMP"; else MYRIENT_BASE_URL="$BASE_URL_NOIN"; fi
        local ds_index="$TEMP_DIR/root.html"; download_index "$MYRIENT_BASE_URL" "$ds_index"
        local plats="$TEMP_DIR/plats.txt"; list_dirs "$ds_index" "$plats"
        local pidx="${BASH_REMATCH[2]}"; local plat=$(sed -n "${pidx}p" "$plats")
        [ -z "$plat" ] && { log "${RED}Invalid platform index${NC}"; exit 1; }
        log "${GREEN}Selected platform:${NC} $plat";
        # Browse (returns when user quits)
        browse_dir "$plat" ""
        # After quitting folder, return to dataset selection
        :
        exit 0
    fi
    # Dataset + search term quick-jump: 1-term or 2-term (non-numeric)
    if [[ "$ds" =~ ^([12])-(.+)$ ]]; then
        if [ "${BASH_REMATCH[1]}" = "1" ]; then MYRIENT_BASE_URL="$BASE_URL_REDUMP"; else MYRIENT_BASE_URL="$BASE_URL_NOIN"; fi
        local term="${BASH_REMATCH[2]}"
        local root="$TEMP_DIR/root.html"; download_index "$MYRIENT_BASE_URL" "$root"
        local plats="$TEMP_DIR/plats.txt"; list_dirs "$root" "$plats"
        grep -i -- "$term" "$plats" > "$TEMP_DIR/plats_f.txt" || true
        if [ -s "$TEMP_DIR/plats_f.txt" ]; then
            log "${CYAN}Matches:${NC}"; print_indexed_matches "$plats" "$TEMP_DIR/plats_f.txt" 500 >&2
        else
            log "${YELLOW}No matches for '${term}'${NC}"
        fi
        # Fall through to normal loop with same master list
        while true; do
            read -p "$(echo -e "${CYAN}Platform (type to filter, number to open, q quit):${NC} ")" pinp
            [ "$pinp" = "q" ] && exit 0
            if [[ "$pinp" =~ ^[0-9]+$ ]]; then
                local plat=$(sed -n "${pinp}p" "$plats"); [ -z "$plat" ] && { log "${YELLOW}Invalid index${NC}"; continue; }
                log "${GREEN}Selected platform:${NC} $plat";
                browse_dir "$plat" ""
                continue
            fi
            grep -i -- "$pinp" "$plats" > "$TEMP_DIR/plats_ff.txt" || true
            if [ -s "$TEMP_DIR/plats_ff.txt" ]; then
                log "${CYAN}Matches:${NC}"; print_indexed_matches "$plats" "$TEMP_DIR/plats_ff.txt" 500 >&2
            else
                log "${YELLOW}No matches${NC}"
            fi
        done
    fi
    if [ -z "$ds" ] || [ "$ds" = "1" ]; then MYRIENT_BASE_URL="$BASE_URL_REDUMP"; else MYRIENT_BASE_URL="$BASE_URL_NOIN"; fi
    # Load root index and display collapsed summary and full list
    local root="$TEMP_DIR/root.html"; download_index "$MYRIENT_BASE_URL" "$root"
    local plats="$TEMP_DIR/plats.txt"; list_dirs "$root" "$plats"
    log "${CYAN}Summary (collapsed by first word):${NC}"; print_collapsed_summary "$plats" >&2
    log "${CYAN}All platforms:${NC}"; print_numbered "$plats" 500 >&2
    # Filter + selection loop using full list numbering
    while true; do
        read -p "$(echo -e "${CYAN}Platform (type to filter, number to open, q quit):${NC} ")" pinp
        [ "$pinp" = "q" ] && exit 0
        if [[ "$pinp" =~ ^[0-9]+$ ]]; then
            local plat=$(sed -n "${pinp}p" "$plats"); [ -z "$plat" ] && { log "${YELLOW}Invalid index${NC}"; continue; }
            log "${GREEN}Selected platform:${NC} $plat";
            browse_dir "$plat" ""
            continue
        fi
        grep -i -- "$pinp" "$plats" > "$TEMP_DIR/plats_f.txt" || true
        if [ -s "$TEMP_DIR/plats_f.txt" ]; then
            log "${CYAN}Matches:${NC}"; print_indexed_matches "$plats" "$TEMP_DIR/plats_f.txt" 500 >&2
        else
            log "${YELLOW}No matches${NC}"
        fi
    done
}

main "$@"
