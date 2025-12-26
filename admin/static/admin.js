// Admin Dashboard JavaScript

class AdminDashboard {
    constructor() {
        this.currentTab = 'movies';
        this.moviesData = [];
        this.allMoviesLoaded = false;
        this.filters = {
            search: '',
            status: '',
            language: '',
            region: '',
            missing_ott: false,
            missing_rating: false
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadMovies();
        this.loadStats();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Filter inputs
        document.getElementById('search-input')?.addEventListener('keyup', (e) => {
            this.filters.search = e.target.value;
            this.loadMovies();
        });

        document.getElementById('filter-status')?.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.loadMovies();
        });

        document.getElementById('filter-language')?.addEventListener('change', (e) => {
            this.filters.language = e.target.value;
            this.loadMovies();
        });

        document.getElementById('filter-region')?.addEventListener('change', (e) => {
            this.filters.region = e.target.value;
            this.loadMovies();
        });

        document.getElementById('filter-missing-ott')?.addEventListener('change', (e) => {
            this.filters.missing_ott = e.target.checked;
            this.loadMovies();
        });

        document.getElementById('filter-missing-rating')?.addEventListener('change', (e) => {
            this.filters.missing_rating = e.target.checked;
            this.loadMovies();
        });

        // Pipeline buttons
        document.getElementById('btn-enrich')?.addEventListener('click', () => this.runEnrich());
        document.getElementById('btn-generate')?.addEventListener('click', () => this.runGenerate());
        document.getElementById('btn-preview')?.addEventListener('click', () => this.showPreview());
        document.getElementById('btn-publish')?.addEventListener('click', () => this.showPublishModal());

        // Modal
        document.getElementById('modal-close')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modal-save')?.addEventListener('click', () => this.saveMovie());
    }

    async switchTab(tab) {
        this.currentTab = tab;
        
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // Show active content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`tab-${tab}`).classList.add('active');

        // Load data for specific tabs
        if (tab === 'backups') {
            await this.loadBackups();
        }
    }

    async loadMovies() {
        try {
            const params = new URLSearchParams(this.filters);
            const response = await fetch(`/api/movies?${params}`);
            const data = await response.json();
            
            this.moviesData = data.movies || [];
            this.renderMovies();
            
            // Populate language and region dropdowns from all movies
            if (!this.allMoviesLoaded) {
                this.populateFilterDropdowns();
                this.allMoviesLoaded = true;
            }
        } catch (error) {
            console.error('Failed to load movies:', error);
            this.showError('Failed to load movies');
        }
    }

    populateFilterDropdowns() {
        // Get all movies without filters to populate dropdowns
        fetch('/api/movies')
            .then(r => r.json())
            .then(data => {
                const movies = data.movies || [];
                const languages = new Set();
                const regions = new Set();
                
                movies.forEach(m => {
                    if (m.language) languages.add(m.language);
                    if (m.region) regions.add(m.region);
                });
                
                // Populate language dropdown
                const langSelect = document.getElementById('filter-language');
                const currentLang = langSelect.value;
                langSelect.innerHTML = '<option value="">All Languages</option>';
                Array.from(languages).sort().forEach(lang => {
                    const opt = document.createElement('option');
                    opt.value = lang;
                    opt.textContent = lang;
                    langSelect.appendChild(opt);
                });
                langSelect.value = currentLang;
                
                // Populate region dropdown
                const regionSelect = document.getElementById('filter-region');
                const currentRegion = regionSelect.value;
                regionSelect.innerHTML = '<option value="">All Regions</option>';
                Array.from(regions).sort().forEach(region => {
                    const opt = document.createElement('option');
                    opt.value = region;
                    opt.textContent = region;
                    regionSelect.appendChild(opt);
                });
                regionSelect.value = currentRegion;
            })
            .catch(err => console.error('Failed to populate dropdowns:', err));
    }

    renderMovies() {
        const tbody = document.querySelector('.movies-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (this.moviesData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #999;">No movies found</td></tr>';
            return;
        }

        this.moviesData.forEach(movie => {
            const row = document.createElement('tr');
            
            const statusClass = movie.status === 'published' ? 'status-published' : 
                               movie.status === 'review' ? 'status-review' : '';
            
            const ottStatus = !movie.ott || movie.ott.length === 0 ? '<span class="missing">Missing</span>' : 
                             `<small>${movie.ott.join(', ')}</small>`;
            
            const ratingStatus = !movie.rating || movie.rating === 0 ? '<span class="missing">Missing</span>' : 
                                movie.rating;
            
            row.innerHTML = `
                <td>${movie.title}</td>
                <td><span class="${statusClass}">${movie.status}</span></td>
                <td>${movie.language || '-'}</td>
                <td>${ottStatus}</td>
                <td>${ratingStatus}</td>
                <td>${movie.release_date || '-'}</td>
                <td><button class="btn btn-secondary" onclick="dashboard.editMovie(${movie.id})">Edit</button></td>
            `;
            
            tbody.appendChild(row);
        });
    }

    editMovie(movieId) {
        const movie = this.moviesData.find(m => m.id === movieId);
        if (!movie) return;

        // Store current movie ID for save
        this.currentEditMovieId = movieId;

        // Populate modal
        document.getElementById('edit-title').value = movie.title || '';
        document.getElementById('edit-status').value = movie.status || 'draft';
        document.getElementById('edit-language').value = movie.language || '';
        document.getElementById('edit-ott').value = (movie.ott || []).join(', ');
        document.getElementById('edit-rating').value = movie.rating || '';
        document.getElementById('edit-release-date').value = movie.release_date || '';

        // Show modal
        document.getElementById('edit-modal').style.display = 'flex';
    }

    closeModal() {
        document.getElementById('edit-modal').style.display = 'none';
    }

    async saveMovie() {
        const movieId = this.currentEditMovieId;
        
        const updates = {
            title: document.getElementById('edit-title').value,
            status: document.getElementById('edit-status').value,
            language: document.getElementById('edit-language').value,
            ott: document.getElementById('edit-ott').value.split(',').map(s => s.trim()).filter(s => s),
            rating: parseFloat(document.getElementById('edit-rating').value) || null,
            release_date: document.getElementById('edit-release-date').value
        };

        try {
            const response = await fetch(`/api/movie/${movieId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });

            const result = await response.json();
            
            if (response.ok) {
                this.closeModal();
                this.loadMovies();
                this.showSuccess('Movie updated successfully');
            } else {
                this.showError(result.error || 'Failed to update movie');
            }
        } catch (error) {
            console.error('Save failed:', error);
            this.showError('Failed to save movie');
        }
    }

    async loadStats() {
        try {
            const response = await fetch('/api/movies?status=all');
            const data = await response.json();
            
            const allMovies = data.movies || [];
            const published = allMovies.filter(m => m.status === 'published').length;
            const review = allMovies.filter(m => m.status === 'review').length;
            const missingOtt = allMovies.filter(m => !m.ott || m.ott.length === 0).length;
            const missingRating = allMovies.filter(m => !m.rating || m.rating === 0).length;

            document.getElementById('total-count').textContent = allMovies.length;
            document.getElementById('published-count').textContent = published;
            document.getElementById('review-count').textContent = review;
            document.getElementById('missing-ott-count').textContent = missingOtt;
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    async runEnrich() {
        this.showProcessing('Running enrichment...');
        
        try {
            const response = await fetch('/api/pipeline/enrich', { method: 'POST' });
            const result = await response.json();
            
            if (response.ok) {
                this.showResult('Enrichment completed', result.output);
                this.loadStats();
                this.loadMovies();
            } else {
                this.showError(result.error || 'Enrichment failed');
            }
        } catch (error) {
            console.error('Enrich failed:', error);
            this.showError('Failed to run enrichment');
        }
    }

    async runGenerate() {
        this.showProcessing('Generating JSON...');
        
        try {
            const response = await fetch('/api/pipeline/generate-json', { method: 'POST' });
            const result = await response.json();
            
            if (response.ok) {
                this.showResult('JSON generation completed', result.output);
                this.loadStats();
            } else {
                this.showError(result.error || 'Generation failed');
            }
        } catch (error) {
            console.error('Generate failed:', error);
            this.showError('Failed to generate JSON');
        }
    }

    async showPreview() {
        try {
            const response = await fetch('/api/pipeline/preview');
            const result = await response.json();
            
            if (response.ok) {
                const preview = `
                    <strong>Generated Files:</strong><br>
                    ${Object.keys(result.files || {}).join(', ')}<br><br>
                    <strong>Sample Data:</strong><br>
                    <pre>${JSON.stringify(result.sample || {}, null, 2)}</pre>
                `;
                this.showResult('JSON Preview', preview);
            } else {
                this.showError(result.error || 'Failed to get preview');
            }
        } catch (error) {
            console.error('Preview failed:', error);
            this.showError('Failed to show preview');
        }
    }

    async showPublishModal() {
        const bucket = prompt('Enter S3 bucket name:', 'my-bucket');
        if (!bucket) return;

        const region = prompt('Enter AWS region:', 'us-east-1');
        if (!region) return;

        await this.publishToS3(bucket, region);
    }

    async publishToS3(bucket, region) {
        this.showProcessing('Publishing to S3...');
        
        try {
            const response = await fetch('/api/pipeline/publish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bucket, region })
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showResult('S3 Publish completed', result.output);
            } else {
                this.showError(result.error || 'Publishing failed');
            }
        } catch (error) {
            console.error('Publish failed:', error);
            this.showError('Failed to publish to S3');
        }
    }

    async loadBackups() {
        try {
            const response = await fetch('/api/backups');
            const data = await response.json();

            const container = document.getElementById('backups-container');
            if (!container) return;

            if (!data.backups || data.backups.length === 0) {
                container.innerHTML = '<p>No backups found</p>';
                return;
            }

            container.innerHTML = '';
            data.backups.forEach(backup => {
                const item = document.createElement('div');
                item.className = 'backup-item';
                item.innerHTML = `
                    <div class="backup-info">
                        <div class="backup-filename">${backup.filename}</div>
                        <div class="backup-meta">${backup.size} | ${backup.timestamp}</div>
                    </div>
                    <div class="backup-actions">
                        <button class="btn btn-secondary" onclick="dashboard.restoreBackup('${backup.filename}')">Restore</button>
                    </div>
                `;
                container.appendChild(item);
            });
        } catch (error) {
            console.error('Failed to load backups:', error);
        }
    }

    async restoreBackup(filename) {
        if (!confirm(`Restore backup ${filename}?`)) return;

        try {
            const response = await fetch(`/api/backups/${filename}/restore`, { method: 'POST' });
            const result = await response.json();

            if (response.ok) {
                this.showSuccess('Backup restored successfully');
                this.loadMovies();
                this.loadStats();
            } else {
                this.showError(result.error || 'Restore failed');
            }
        } catch (error) {
            console.error('Restore failed:', error);
            this.showError('Failed to restore backup');
        }
    }

    showProcessing(message) {
        const resultDiv = document.getElementById('pipeline-result');
        if (resultDiv) {
            resultDiv.innerHTML = `<div class="loading">${message}</div>`;
        }
    }

    showResult(title, output) {
        const resultDiv = document.getElementById('pipeline-result');
        if (resultDiv) {
            const cleanOutput = typeof output === 'string' ? 
                output.replace(/</g, '&lt;').replace(/>/g, '&gt;') : 
                JSON.stringify(output, null, 2);
            
            resultDiv.innerHTML = `
                <h3>${title}</h3>
                <div class="result-box">
                    <pre>${cleanOutput}</pre>
                </div>
            `;
        }
    }

    showError(message) {
        const resultDiv = document.getElementById('pipeline-result');
        if (resultDiv) {
            resultDiv.innerHTML = `<div style="color: var(--danger); padding: 1rem; background: #fef2f2; border-radius: 6px;">❌ ${message}</div>`;
        }
    }

    showSuccess(message) {
        const resultDiv = document.getElementById('pipeline-result');
        if (!resultDiv) {
            alert(message);
            return;
        }
        resultDiv.innerHTML = `<div style="color: var(--success); padding: 1rem; background: #f0fdf4; border-radius: 6px;">✓ ${message}</div>`;
    }
}

// Global functions called from HTML
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

function saveEdit() {
    if (window.dashboard) {
        window.dashboard.saveMovie();
    }
}

function clearFilters() {
    if (window.dashboard) {
        window.dashboard.filters = {
            search: '',
            status: '',
            language: '',
            region: '',
            missing_ott: false,
            missing_rating: false
        };
        
        // Reset form controls
        document.getElementById('search-input').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-language').value = '';
        document.getElementById('filter-region').value = '';
        document.getElementById('filter-missing-ott').checked = false;
        document.getElementById('filter-missing-rating').checked = false;
        
        // Reload movies
        window.dashboard.loadMovies();
    }
}

// ============================================================================
// PIPELINE FUNCTIONS
// ============================================================================

async function runEnrichment() {
    const resultBox = document.getElementById('enrich-result');
    const output = document.getElementById('enrich-output');
    const btn = event.target;
    
    btn.disabled = true;
    btn.textContent = '⏳ Running...';
    resultBox.style.display = 'block';
    output.textContent = 'Running enrichment...';
    
    try {
        const response = await fetch('/api/pipeline/enrich', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        output.textContent = result.summary?.stdout || JSON.stringify(result, null, 2);
        
        if (result.success) {
            window.dashboard.showSuccess('Enrichment completed successfully');
            setTimeout(() => window.dashboard.loadMovies(), 2000);
        } else {
            window.dashboard.showError(result.error || 'Enrichment failed');
        }
    } catch (error) {
        output.textContent = `Error: ${error.message}`;
        window.dashboard.showError('Enrichment failed');
    } finally {
        btn.disabled = false;
        btn.textContent = '▶ Run Enrichment';
    }
}

async function runJsonGeneration() {
    const resultBox = document.getElementById('json-result');
    const output = document.getElementById('json-output');
    const btn = event.target;
    
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';
    resultBox.style.display = 'block';
    output.textContent = 'Generating JSON files...';
    
    try {
        const response = await fetch('/api/pipeline/generate-json', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        const result = await response.json();
        output.textContent = result.summary?.stdout || JSON.stringify(result, null, 2);
        
        if (result.success) {
            window.dashboard.showSuccess('JSON generation completed successfully');
            setTimeout(() => window.dashboard.loadMovies(), 2000);
        } else {
            window.dashboard.showError(result.error || 'JSON generation failed');
        }
    } catch (error) {
        output.textContent = `Error: ${error.message}`;
        window.dashboard.showError('JSON generation failed');
    } finally {
        btn.disabled = false;
        btn.textContent = '▶ Generate JSON';
    }
}

async function previewChanges() {
    const resultBox = document.getElementById('preview-result');
    const output = document.getElementById('preview-output');
    const btn = event.target;
    
    btn.disabled = true;
    btn.textContent = '⏳ Loading...';
    resultBox.style.display = 'block';
    output.textContent = 'Loading preview...';
    
    try {
        const response = await fetch('/api/pipeline/preview', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        output.textContent = JSON.stringify(result, null, 2);
        
        if (result.success) {
            window.dashboard.showSuccess('Preview loaded');
        } else {
            window.dashboard.showError(result.error || 'Preview failed');
        }
    } catch (error) {
        output.textContent = `Error: ${error.message}`;
        window.dashboard.showError('Preview failed');
    } finally {
        btn.disabled = false;
        btn.textContent = '👁 Preview Changes';
    }
}

async function publishToS3() {
    const bucket = document.getElementById('s3-bucket').value.trim();
    const resultBox = document.getElementById('publish-result');
    const output = document.getElementById('publish-output');
    const btn = event.target;
    
    if (!bucket) {
        window.dashboard.showError('Please enter S3 bucket name');
        return;
    }
    
    btn.disabled = true;
    btn.textContent = '⏳ Publishing...';
    resultBox.style.display = 'block';
    output.textContent = 'Publishing to S3...';
    
    try {
        const response = await fetch('/api/pipeline/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bucket })
        });
        
        const result = await response.json();
        output.textContent = result.summary?.stdout || JSON.stringify(result, null, 2);
        
        if (result.success) {
            window.dashboard.showSuccess('Published to S3 successfully');
        } else {
            window.dashboard.showError(result.error || 'Publish failed');
        }
    } catch (error) {
        output.textContent = `Error: ${error.message}`;
        window.dashboard.showError('Publish failed');
    } finally {
        btn.disabled = false;
        btn.textContent = '🚀 Publish to S3';
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AdminDashboard();
});
