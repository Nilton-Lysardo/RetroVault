class App {
    constructor() {
        this.state = {
            currentConsole: 'all',
            currentSearch: '',
            currentSort: 'name',
            currentOrder: 'asc',
            currentPage: 1,
            perPage: 50,
            totalPages: 1,
            totalGames: 0,
            games: [],
            consoles: []
        };
        this.searchTimeout = null;
    }

    async init() {
        this.setupEventListeners();
        await this.loadConsoles();
        await this.loadGames();
        await this.loadStats();
    }

    setupEventListeners() {
        // Sidebar clicks
        document.getElementById('console-list').addEventListener('click', (e) => {
            const li = e.target.closest('li');
            if (li) {
                this.selectConsole(li.dataset.id);
            }
        });

        // Search
        document.getElementById('search-input').addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.state.currentSearch = e.target.value;
                this.loadGames(true);
            }, 300);
        });

        // Sort controls
        document.getElementById('sort-name').addEventListener('click', () => this.setSort('name'));
        document.getElementById('sort-date').addEventListener('click', () => this.setSort('date'));
        document.getElementById('sort-rating').addEventListener('click', () => this.setSort('rating'));

        // Per page select
        document.getElementById('select-per-page')?.addEventListener('change', (e) => {
            this.state.perPage = parseInt(e.target.value, 10);
            this.loadGames(true);
        });

        // Pagination clicks
        document.getElementById('pagination-bar')?.addEventListener('click', (e) => {
            const btn = e.target.closest('.page-btn');
            if (btn && btn.dataset.page) {
                this.state.currentPage = parseInt(btn.dataset.page, 10);
                this.loadGames(false);
                document.querySelector('.main-content').scrollTop = 0;
            }
        });

        // Game Grid clicks
        document.getElementById('game-grid').addEventListener('click', (e) => {
            const card = e.target.closest('.game-card');
            if (card) {
                this.showGameModal(card.dataset.id);
            }
        });

        // Modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeModal();
            if (e.key === '/' && document.activeElement !== document.getElementById('search-input')) {
                e.preventDefault();
                document.getElementById('search-input').focus();
            }
        });

        document.getElementById('game-modal').addEventListener('click', (e) => {
            if (e.target.id === 'game-modal' || e.target.id === 'modal-close') {
                this.closeModal();
            }
        });

        // Modal actions
        document.getElementById('game-modal-content').addEventListener('click', (e) => {
            if (e.target.id === 'btn-play') {
                this.handleLaunch(e.target.dataset.id);
            } else if (e.target.id === 'btn-fav') {
                this.handleFavorite(e.target.dataset.id);
            } else if (e.target.classList.contains('star')) {
                this.handleRating(e.target.closest('.rating-stars').dataset.id, e.target.dataset.value);
            }
        });

        // Cover file upload
        document.getElementById('game-modal-content').addEventListener('change', async (e) => {
            if (e.target.id === 'cover-file-input' && e.target.files && e.target.files[0]) {
                const file = e.target.files[0];
                const gameId = e.target.dataset.id;
                try {
                    Components.createToast('Enviando capa...', 'info');
                    await API.uploadCover(gameId, file);
                    Components.createToast('Capa atualizada com sucesso!', 'success');
                    await this.showGameModal(gameId);
                    this.loadGames(false);
                } catch (err) {
                    console.error('Erro ao enviar capa', err);
                    Components.createToast('Erro ao enviar capa', 'error');
                }
            }
        });

        // Footer buttons
        document.getElementById('btn-scan').addEventListener('click', () => this.handleScan());
        document.getElementById('btn-fetch-covers').addEventListener('click', () => this.handleFetchCovers());
    }

    setSort(sortField) {
        if (this.state.currentSort === sortField) {
            this.state.currentOrder = this.state.currentOrder === 'asc' ? 'desc' : 'asc';
        } else {
            this.state.currentSort = sortField;
            this.state.currentOrder = (sortField === 'date' || sortField === 'rating') ? 'desc' : 'asc';
        }
        document.querySelectorAll('.sort-controls button').forEach(b => b.style.borderColor = 'transparent');
        const activeBtn = document.getElementById(`sort-${sortField}`);
        if (activeBtn) activeBtn.style.borderColor = 'var(--accent)';
        this.loadGames(true);
    }

    async loadConsoles() {
        try {
            const data = await API.getConsoles();
            this.state.consoles = data;
            const list = document.getElementById('console-list');
            list.innerHTML = Components.createSidebarItems(data, this.state.currentConsole);
        } catch (e) {
            console.error('Falha ao carregar consoles', e);
        }
    }

    async loadStats() {
        try {
            const stats = await API.getStats();
            document.getElementById('stats-summary').innerHTML = Components.createStatsBar(stats);
        } catch (e) {
            console.error('Falha ao carregar estatísticas', e);
        }
    }

    async loadGames(resetPage = true) {
        if (resetPage) this.state.currentPage = 1;
        
        const filters = {
            search: this.state.currentSearch,
            sort: this.state.currentSort,
            order: this.state.currentOrder,
            page: this.state.currentPage,
            per_page: this.state.perPage
        };

        if (this.state.currentConsole === 'favorites') {
            filters.favorite = true;
        } else if (this.state.currentConsole !== 'all') {
            filters.console = this.state.currentConsole;
        }

        try {
            document.getElementById('loading-spinner').classList.remove('hidden');
            const data = await API.getGames(filters);
            this.state.games = data.games || [];
            this.state.totalPages = data.pages || Math.ceil((data.total || 0) / (this.state.perPage || 50)) || 1;
            this.state.totalGames = data.total || 0;

            this.renderGameGrid(this.state.games);

            // Render pagination
            const pagBar = document.getElementById('pagination-bar');
            if (pagBar) {
                pagBar.innerHTML = Components.createPagination(this.state.currentPage, this.state.totalPages, this.state.totalGames);
            }

            // Results count
            const countEl = document.getElementById('results-count');
            if (countEl) {
                const start = (this.state.currentPage - 1) * this.state.perPage + 1;
                const end = Math.min(this.state.currentPage * this.state.perPage, this.state.totalGames);
                if (this.state.totalGames > 0) {
                    countEl.textContent = `Exibindo ${start}-${end} de ${this.state.totalGames} jogos`;
                } else {
                    countEl.textContent = 'Nenhum jogo encontrado';
                }
            }
        } catch (e) {
            Components.createToast('Erro ao carregar jogos', 'error');
        } finally {
            document.getElementById('loading-spinner').classList.add('hidden');
        }
    }

    renderGameGrid(games) {
        const grid = document.getElementById('game-grid');
        grid.innerHTML = '';
        games.forEach(game => {
            grid.appendChild(Components.createGameCard(game));
        });
    }

    selectConsole(id) {
        this.state.currentConsole = id;
        document.querySelectorAll('.console-list li').forEach(li => li.classList.remove('active'));
        document.querySelector(`.console-list li[data-id="${id}"]`)?.classList.add('active');
        this.loadGames();
    }

    async showGameModal(id) {
        try {
            const game = await API.getGame(id);
            const content = document.getElementById('game-modal-content');
            content.innerHTML = Components.createGameModal(game);
            document.getElementById('game-modal').classList.remove('hidden');
        } catch (e) {
            Components.createToast('Erro ao carregar detalhes', 'error');
        }
    }

    closeModal() {
        document.getElementById('game-modal').classList.add('hidden');
        document.getElementById('settings-modal').classList.add('hidden');
    }

    async handleLaunch(id) {
        try {
            Components.createToast('Iniciando jogo...', 'info');
            await API.launchGame(id);
            this.closeModal();
        } catch (e) {
            Components.createToast('Erro ao iniciar jogo', 'error');
        }
    }

    async handleFavorite(id) {
        try {
            await API.toggleFavorite(id);
            Components.createToast('Favorito atualizado', 'success');
            // Optimistic update
            const card = document.querySelector(`.game-card[data-id="${id}"]`);
            if(card) {
                card.classList.toggle('favorite');
            }
            if(this.state.currentConsole === 'favorites') {
                this.loadGames(); // reload if in fav view
            }
        } catch (e) {
            Components.createToast('Erro ao atualizar favorito', 'error');
        }
    }

    async handleRating(id, rating) {
        try {
            await API.setRating(id, rating);
            Components.createToast('Avaliação salva', 'success');
            const starsContainer = document.querySelector(`.rating-stars[data-id="${id}"]`);
            if (starsContainer) {
                starsContainer.innerHTML = Components.createRatingStars(rating, true);
            }
        } catch (e) {
            Components.createToast('Erro ao salvar avaliação', 'error');
        }
    }

    async handleScan() {
        try {
            Components.createToast('Iniciando varredura...', 'info');
            await API.scanRoms();
            Components.createToast('Varredura concluída', 'success');
            this.loadConsoles();
            this.loadGames();
            this.loadStats();
        } catch (e) {
            Components.createToast('Erro na varredura', 'error');
        }
    }

    async handleFetchCovers() {
        try {
            Components.createToast('Iniciando busca automática de capas...', 'info');
            const res = await API.fetchCovers();
            Components.createToast(res.message || 'Busca iniciada em segundo plano!', 'success');
            // Recarrega os jogos a cada 5 segundos para exibir as capas novas
            let checks = 0;
            const interval = setInterval(() => {
                checks++;
                this.loadGames(false);
                this.loadStats();
                if (checks >= 6) clearInterval(interval);
            }, 5000);
        } catch (e) {
            Components.createToast('Erro ao buscar capas', 'error');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
    window.app.init();
});
