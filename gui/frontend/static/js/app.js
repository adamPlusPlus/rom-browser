// Myrient Game Browser Frontend JavaScript

class MyrientBrowser {
    constructor() {
        this.currentPlatform = null;
        this.currentGames = [];
        this.filters = {
            genre: '',
            platform: '',
            rating: 0
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPlatforms();
    }

    setupEventListeners() {
        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', () => this.handleSearch());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSearch();
        });

        // Modal functionality
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
        document.getElementById('gameModal').addEventListener('click', (e) => {
            if (e.target.id === 'gameModal') this.closeModal();
        });

        // Filter functionality
        document.getElementById('applyFilters').addEventListener('click', () => this.applyFilters());
        document.getElementById('clearFilters').addEventListener('click', () => this.clearFilters());
        document.getElementById('ratingFilter').addEventListener('input', (e) => {
            document.getElementById('ratingValue').textContent = e.target.value + '+';
        });

        // Refresh platforms
        document.getElementById('refreshPlatforms').addEventListener('click', () => this.loadPlatforms());
    }

    async loadPlatforms() {
        try {
            this.showLoading();
            const response = await fetch('/api/platforms');
            const data = await response.json();
            
            if (data.platforms) {
                this.renderPlatforms(data.platforms);
            } else {
                this.showError('Failed to load platforms');
            }
        } catch (error) {
            console.error('Error loading platforms:', error);
            this.showError('Error loading platforms');
        } finally {
            this.hideLoading();
        }
    }

    renderPlatforms(platforms) {
        const platformsList = document.getElementById('platformsList');
        platformsList.innerHTML = '';

        platforms.forEach((platform, index) => {
            const platformElement = document.createElement('div');
            platformElement.className = 'platform-item';
            platformElement.innerHTML = `
                <div class="platform-name">${platform.name}</div>
                <div class="platform-dataset">${platform.dataset}</div>
            `;
            platformElement.addEventListener('click', () => this.selectPlatform(platform, index + 1));
            platformsList.appendChild(platformElement);
        });
    }

    async selectPlatform(platform, platformId) {
        try {
            // Update active platform in UI
            document.querySelectorAll('.platform-item').forEach(item => item.classList.remove('active'));
            event.target.closest('.platform-item').classList.add('active');

            this.currentPlatform = platform;
            this.showLoading();

            const response = await fetch(`/api/browse/${platformId}`);
            const data = await response.json();
            
            if (data.files) {
                this.currentGames = data.files;
                this.renderGames(data.files);
            } else {
                this.showError('Failed to load games');
            }
        } catch (error) {
            console.error('Error loading games:', error);
            this.showError('Error loading games');
        } finally {
            this.hideLoading();
        }
    }

    renderGames(games) {
        const gamesGrid = document.getElementById('gamesGrid');
        gamesGrid.innerHTML = '';

        if (games.length === 0) {
            gamesGrid.innerHTML = '<div class="welcome-message"><i class="fas fa-gamepad fa-3x"></i><h2>No games found</h2><p>Try adjusting your filters or search terms</p></div>';
            return;
        }

        games.forEach(game => {
            const gameCard = document.createElement('div');
            gameCard.className = 'game-card';
            gameCard.innerHTML = `
                <div class="game-cover">
                    <div class="game-cover-placeholder">
                        <i class="fas fa-gamepad"></i>
                    </div>
                </div>
                <div class="game-info">
                    <div class="game-title">${this.cleanGameTitle(game.name)}</div>
                    <div class="game-meta">
                        <div class="game-rating">
                            <div class="stars">★★★★☆</div>
                        </div>
                        <div class="game-platform">${this.getPlatformFromTitle(game.name)}</div>
                    </div>
                    <div class="game-description">Loading game information...</div>
                </div>
            `;
            
            gameCard.addEventListener('click', () => this.showGameDetails(game));
            gamesGrid.appendChild(gameCard);

            // Load game metadata asynchronously
            this.loadGameMetadata(game.name, gameCard);
        });
    }

    async loadGameMetadata(gameName, gameCard) {
        try {
            const response = await fetch(`/api/game/${encodeURIComponent(gameName)}`);
            if (response.ok) {
                const metadata = await response.json();
                this.updateGameCard(gameCard, metadata);
            }
        } catch (error) {
            console.error('Error loading game metadata:', error);
        }
    }

    updateGameCard(gameCard, metadata) {
        const coverImg = gameCard.querySelector('.game-cover img');
        const coverPlaceholder = gameCard.querySelector('.game-cover-placeholder');
        const title = gameCard.querySelector('.game-title');
        const rating = gameCard.querySelector('.stars');
        const platform = gameCard.querySelector('.game-platform');
        const description = gameCard.querySelector('.game-description');

        // Update cover art
        if (metadata.cover_art) {
            coverImg.src = metadata.cover_art;
            coverImg.style.display = 'block';
            coverPlaceholder.style.display = 'none';
        }

        // Update title
        if (metadata.title) {
            title.textContent = metadata.title;
        }

        // Update rating
        if (metadata.rating) {
            const stars = Math.round(metadata.rating / 20); // Convert 0-100 to 0-5 stars
            rating.innerHTML = '★'.repeat(stars) + '☆'.repeat(5 - stars);
        }

        // Update platform
        if (metadata.platforms && metadata.platforms.length > 0) {
            platform.textContent = metadata.platforms[0];
        }

        // Update description
        if (metadata.description) {
            description.textContent = metadata.description.substring(0, 150) + '...';
        }
    }

    async showGameDetails(game) {
        try {
            this.showLoading();
            const response = await fetch(`/api/game/${encodeURIComponent(game.name)}`);
            
            if (response.ok) {
                const metadata = await response.json();
                this.renderGameModal(game, metadata);
            } else {
                this.renderGameModal(game, null);
            }
        } catch (error) {
            console.error('Error loading game details:', error);
            this.renderGameModal(game, null);
        } finally {
            this.hideLoading();
        }
    }

    renderGameModal(game, metadata) {
        const modal = document.getElementById('gameModal');
        const title = document.getElementById('modalGameTitle');
        const cover = document.getElementById('modalGameCover');
        const rating = document.getElementById('modalGameRating');
        const ratingCount = document.getElementById('modalGameRatingCount');
        const metacritic = document.getElementById('modalGameMetacritic');
        const metacriticScore = document.getElementById('modalGameMetacriticScore');
        const platforms = document.getElementById('modalGamePlatforms');
        const genres = document.getElementById('modalGameGenres');
        const releaseDate = document.getElementById('modalGameReleaseDate');
        const description = document.getElementById('modalGameDescription');
        const screenshots = document.getElementById('modalGameScreenshots');
        const screenshotsGrid = document.getElementById('modalScreenshotsGrid');

        // Set basic game info
        title.textContent = this.cleanGameTitle(game.name);
        cover.src = metadata?.cover_art || '';
        cover.style.display = metadata?.cover_art ? 'block' : 'none';

        if (metadata) {
            // Rating
            if (metadata.rating) {
                const stars = Math.round(metadata.rating / 20);
                rating.innerHTML = '★'.repeat(stars) + '☆'.repeat(5 - stars);
                ratingCount.textContent = `(${metadata.rating_count || 0} ratings)`;
            }

            // Metacritic
            if (metadata.metacritic_score) {
                metacritic.style.display = 'flex';
                metacriticScore.textContent = metadata.metacritic_score;
                metacriticScore.className = `metacritic-score ${this.getMetacriticClass(metadata.metacritic_score)}`;
            }

            // Platforms
            if (metadata.platforms) {
                platforms.textContent = metadata.platforms.join(', ');
            }

            // Genres
            if (metadata.genres) {
                genres.textContent = metadata.genres.join(', ');
            }

            // Release Date
            if (metadata.release_date) {
                releaseDate.textContent = metadata.release_date;
            }

            // Description
            if (metadata.description) {
                description.textContent = metadata.description;
            }

            // Screenshots
            if (metadata.screenshots && metadata.screenshots.length > 0) {
                screenshots.style.display = 'block';
                screenshotsGrid.innerHTML = '';
                metadata.screenshots.forEach(screenshot => {
                    const img = document.createElement('img');
                    img.src = screenshot;
                    img.className = 'screenshot';
                    img.addEventListener('click', () => window.open(screenshot, '_blank'));
                    screenshotsGrid.appendChild(img);
                });
            }
        } else {
            // No metadata available
            rating.innerHTML = 'No rating available';
            ratingCount.textContent = '';
            platforms.textContent = this.getPlatformFromTitle(game.name);
            genres.textContent = 'Unknown';
            releaseDate.textContent = 'Unknown';
            description.textContent = 'No description available for this game.';
        }

        // Setup download button
        document.getElementById('downloadBtn').onclick = () => this.downloadGame(game.name);

        modal.style.display = 'block';
    }

    closeModal() {
        document.getElementById('gameModal').style.display = 'none';
    }

    async downloadGame(gameName) {
        try {
            const response = await fetch(`/api/download/${encodeURIComponent(gameName)}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                alert(`Download started for ${gameName}`);
            } else {
                alert('Failed to start download');
            }
        } catch (error) {
            console.error('Error downloading game:', error);
            alert('Error starting download');
        }
    }

    handleSearch() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        if (!searchTerm) return;

        const filteredGames = this.currentGames.filter(game => 
            game.name.toLowerCase().includes(searchTerm)
        );

        this.renderGames(filteredGames);
    }

    applyFilters() {
        // This would implement the filtering logic
        console.log('Applying filters:', this.filters);
    }

    clearFilters() {
        this.filters = { genre: '', platform: '', rating: 0 };
        document.getElementById('genreFilter').value = '';
        document.getElementById('platformFilter').value = '';
        document.getElementById('ratingFilter').value = '0';
        document.getElementById('ratingValue').textContent = '0+';
        this.renderGames(this.currentGames);
    }

    cleanGameTitle(title) {
        return title
            .replace(/\.zip$/, '')
            .replace(/\s*\([^)]*\)\s*$/, '')
            .replace(/\s*\[[^\]]*\]\s*$/, '')
            .trim();
    }

    getPlatformFromTitle(title) {
        if (title.includes('(World)')) return 'Multi-platform';
        if (title.includes('(USA)')) return 'USA';
        if (title.includes('(Europe)')) return 'Europe';
        if (title.includes('(Japan)')) return 'Japan';
        return 'Unknown';
    }

    getMetacriticClass(score) {
        if (score >= 80) return 'excellent';
        if (score >= 70) return 'good';
        if (score >= 60) return 'fair';
        return 'poor';
    }

    showLoading() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    showError(message) {
        const gamesGrid = document.getElementById('gamesGrid');
        gamesGrid.innerHTML = `
            <div class="welcome-message">
                <i class="fas fa-exclamation-triangle fa-3x"></i>
                <h2>Error</h2>
                <p>${message}</p>
            </div>
        `;
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new MyrientBrowser();
});

// Add some CSS for Metacritic score colors
const style = document.createElement('style');
style.textContent = `
    .metacritic-score.excellent { background: #48bb78; }
    .metacritic-score.good { background: #38b2ac; }
    .metacritic-score.fair { background: #ed8936; }
    .metacritic-score.poor { background: #e53e3e; }
`;
document.head.appendChild(style);
