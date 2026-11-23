const API = {
  baseUrl: 'http://127.0.0.1:8080',

  async request(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, options);
      if (!response.ok) {
        throw new Error(`Erro na API: ${response.status} ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("API Request Error:", error);
      throw error;
    }
  },

  async getGames(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    return this.request(`/api/games?${params}`);
  },

  async getGame(id) {
    return this.request(`/api/games/${id}`);
  },

  async getConsoles() {
    return this.request('/api/consoles');
  },

  async getStats() {
    return this.request('/api/stats');
  },

  async toggleFavorite(id) {
    return this.request(`/api/games/${id}/favorite`, { method: 'POST' });
  },

  async setRating(id, rating) {
    return this.request(`/api/games/${id}/rating`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating })
    });
  },

  async uploadCover(id, file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request(`/api/games/${id}/cover`, {
      method: 'POST',
      body: formData
    });
  },

  async launchGame(id) {
    return this.request(`/api/launch/${id}`, { method: 'POST' });
  },

  async scanRoms(console = null) {
    const endpoint = console ? `/api/scan/${console}` : '/api/scan';
    return this.request(endpoint, { method: 'POST' });
  },

  async fetchCovers() {
    return this.request('/api/covers/fetch', { method: 'POST' });
  },

  async getConfig() {
    return this.request('/api/config');
  },

  async updateEmulator(consoleId, data) {
    return this.request(`/api/config/emulator/${consoleId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  }
};
