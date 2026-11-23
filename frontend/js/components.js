const Components = {
    createGameCard(game) {
        const card = document.createElement('div');
        card.className = `game-card ${game.is_favorite ? 'favorite' : ''}`;
        card.dataset.id = game.id;

        const coverFilename = game.cover_path ? game.cover_path.split('/').pop() : null;
        const coverUrl = coverFilename ? `${API.baseUrl}/covers/${game.console_name}/${encodeURIComponent(coverFilename)}` : null;
        const coverHtml = coverUrl
            ? `<div class="game-cover" style="background-image: url('${coverUrl}')"></div>`
            : this.createPlaceholderCover(game);

        card.innerHTML = `
            ${coverHtml}
            <div class="favorite-star">★</div>
            <div class="game-info">
                <div class="game-title" title="${game.clean_name || game.name}">${game.clean_name || game.name}</div>
                <div class="console-badge">${game.console_name || ''}</div>
            </div>
        `;
        return card;
    },

    createPlaceholderCover(game) {
        return `
            <div class="placeholder-cover">
                <div style="font-size: 3rem;">🎮</div>
                <div style="margin-top: 10px; font-weight: bold; padding: 0 10px;">${game.clean_name || game.name}</div>
            </div>
        `;
    },

    createGameModal(game) {
        const coverFilename = game.cover_path ? game.cover_path.split('/').pop() : null;
        const coverUrl = coverFilename ? `${API.baseUrl}/covers/${game.console_name}/${encodeURIComponent(coverFilename)}` : null;
        const sizeMB = game.file_size ? (game.file_size / 1024 / 1024).toFixed(2) : '0';
        return `
            <div class="modal-header">
                <h2>${game.clean_name || game.name}</h2>
                <button class="close-btn" id="modal-close">&times;</button>
            </div>
            <div class="modal-body" style="display: flex; gap: 20px; margin-top: 15px; flex-wrap: wrap;">
                <div class="modal-cover-wrapper" style="flex-shrink: 0; width: 220px; display: flex; flex-direction: column; align-items: center; gap: 10px;">
                    <div id="modal-cover-preview" style="width: 100%; border-radius: var(--radius-sm); overflow: hidden; background: rgba(0,0,0,0.3); min-height: 220px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
                        ${coverUrl ? `<img src="${coverUrl}" style="width: 100%; height: auto; display: block; border-radius: var(--radius-sm);">` : this.createPlaceholderCover(game)}
                    </div>
                    <label for="cover-file-input" class="btn-secondary" style="cursor: pointer; font-size: 0.85rem; padding: 8px 12px; text-align: center; width: 100%; display: block; box-sizing: border-box; border: 1px dashed var(--accent);">
                        🖼️ Escolher Imagem do PC
                    </label>
                    <input type="file" id="cover-file-input" accept="image/*" style="display: none;" data-id="${game.id}">
                </div>
                <div class="modal-info" style="flex: 1; min-width: 250px;">
                    <p><strong>Console:</strong> ${game.console_name}</p>
                    <p><strong>Arquivo ROM:</strong> <span style="font-size: 0.85rem; color: var(--text-muted); word-break: break-all;">${game.name}</span></p>
                    <p><strong>Tamanho:</strong> ${sizeMB} MB</p>
                    <p><strong>Jogadas:</strong> ${game.play_count || 0}</p>
                    <p><strong>Avaliação:</strong> <span class="rating-stars" data-id="${game.id}">${this.createRatingStars(game.rating, true)}</span></p>
                    <div style="margin-top: 25px; display: flex; gap: 10px;">
                        <button class="btn-primary btn-play" id="btn-play" data-id="${game.id}">▶ Jogar</button>
                        <button class="btn-secondary" id="btn-fav" data-id="${game.id}">${game.is_favorite ? '★ Desfavoritar' : '☆ Favoritar'}</button>
                    </div>
                </div>
            </div>
        `;
    },

    createSidebarItems(consoles, activeConsole) {
        let html = `<li data-id="all" class="${activeConsole === 'all' ? 'active' : ''}">🏠 Todos</li>`;
        html += `<li data-id="favorites" class="${activeConsole === 'favorites' ? 'active' : ''}">⭐ Favoritos</li>`;
        
        consoles.forEach(c => {
            html += `<li data-id="${c.name}" class="${activeConsole === c.name ? 'active' : ''}">
                ${c.icon || '🎮'} ${c.name} <span style="color: var(--text-muted); font-size: 0.8rem;">(${c.rom_count || 0})</span>
            </li>`;
        });
        
        return html;
    },

    createRatingStars(rating, interactive = false) {
        let html = '';
        const r = rating || 0;
        for(let i = 1; i <= 5; i++) {
            html += `<span class="star ${interactive ? 'interactive' : ''} ${i <= r ? 'filled' : ''}" data-value="${i}" style="color: ${i <= r ? 'var(--gold)' : 'var(--text-muted)'}; ${interactive ? 'cursor:pointer;' : ''}">★</span>`;
        }
        return html;
    },

    createStatsBar(stats) {
        const consoleCount = stats.by_console ? Object.keys(stats.by_console).length : 0;
        const totalSizeMB = stats.total_size ? (stats.total_size / 1024 / 1024 / 1024).toFixed(1) : '0';
        return `<span>🎮 ${stats.total_games || 0} jogos</span> | <span>📺 ${consoleCount} sistemas</span> | <span>💾 ${totalSizeMB} GB</span>`;
    },

    createToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: var(--bg-card); border-left: 4px solid var(--accent); padding: 10px 20px; 
            margin-bottom: 10px; border-radius: 4px; box-shadow: 0 2px 5px var(--shadow);
            animation: slideIn 0.3s;
        `;
        toast.textContent = message;
        
        const container = document.getElementById('toast-container') || document.body;
        if(container === document.body) {
            const tc = document.createElement('div');
            tc.id = 'toast-container';
            tc.style.cssText = 'position: fixed; bottom: 80px; right: 20px; z-index: 9999;';
            document.body.appendChild(tc);
            tc.appendChild(toast);
        } else {
            container.appendChild(toast);
        }

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    createPagination(currentPage, totalPages, totalGames) {
        if (!totalPages || totalPages <= 1) {
            return '';
        }
        let html = '';
        
        // Previous
        if (currentPage > 1) {
            html += `<button class="btn-secondary page-btn" data-page="${currentPage - 1}" style="padding: 6px 14px; font-size: 0.85rem; cursor: pointer;">⬅️ Anterior</button>`;
        } else {
            html += `<button class="btn-secondary" disabled style="opacity: 0.4; cursor: not-allowed; padding: 6px 14px; font-size: 0.85rem;">⬅️ Anterior</button>`;
        }

        // Page numbers
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            html += `<button class="btn-secondary page-btn" data-page="1" style="padding: 6px 12px; font-size: 0.85rem; cursor: pointer;">1</button>`;
            if (startPage > 2) html += `<span style="color: var(--text-muted); padding: 0 4px;">...</span>`;
        }

        for (let i = startPage; i <= endPage; i++) {
            const isCurrent = i === currentPage;
            const style = isCurrent 
                ? 'background: var(--accent); color: #fff; font-weight: bold; border-color: var(--accent); padding: 6px 12px; font-size: 0.85rem; cursor: pointer;'
                : 'padding: 6px 12px; font-size: 0.85rem; cursor: pointer;';
            html += `<button class="btn-secondary page-btn" data-page="${i}" style="${style}">${i}</button>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) html += `<span style="color: var(--text-muted); padding: 0 4px;">...</span>`;
            html += `<button class="btn-secondary page-btn" data-page="${totalPages}" style="padding: 6px 12px; font-size: 0.85rem; cursor: pointer;">${totalPages}</button>`;
        }

        // Next
        if (currentPage < totalPages) {
            html += `<button class="btn-secondary page-btn" data-page="${currentPage + 1}" style="padding: 6px 14px; font-size: 0.85rem; cursor: pointer;">Próxima ➡️</button>`;
        } else {
            html += `<button class="btn-secondary" disabled style="opacity: 0.4; cursor: not-allowed; padding: 6px 14px; font-size: 0.85rem;">Próxima ➡️</button>`;
        }

        return html;
    }
};
