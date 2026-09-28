// src/api.js
const API_BASE_URL = 'http://localhost:8000';

const api = {
    // 影城相關
    getCinemas: async (chain = null) => {
        const url = chain 
            ? `${API_BASE_URL}/api/cinemas?chain=${chain}`
            : `${API_BASE_URL}/api/cinemas`;
        const response = await fetch(url);
        return response.json();
    },

    getCinema: async (name) => {
        const response = await fetch(`${API_BASE_URL}/api/cinemas/${encodeURIComponent(name)}`);
        return response.json();
    },

    getCinemaShowtimes: async (cinemaName, date = null) => {
        const url = date
            ? `${API_BASE_URL}/api/showtimes/cinema/${encodeURIComponent(cinemaName)}?date=${date}`
            : `${API_BASE_URL}/api/showtimes/cinema/${encodeURIComponent(cinemaName)}`;
        const response = await fetch(url);
        return response.json();
    },

    // 電影相關
    getMovies: async (skip = 0, limit = 20, chain = null) => {
        let url = `${API_BASE_URL}/api/movies?skip=${skip}&limit=${limit}`;
        if (chain) {
            url += `&chain=${chain}`;
        }
        const response = await fetch(url);
        return response.json();
    },

    getMovie: async (movieId) => {
        const response = await fetch(`${API_BASE_URL}/api/movies/${encodeURIComponent(movieId)}`);
        return response.json();
    },

    getMovieShowtimes: async (movieId) => {
        const response = await fetch(`${API_BASE_URL}/api/showtimes/movie/${encodeURIComponent(movieId)}`);
        return response.json();
    },

    // 場次相關
    getShowtimes: async (params = {}) => {
        const queryParams = new URLSearchParams();
        
        if (params.cinema_name) queryParams.append('cinema_name', params.cinema_name);
        if (params.movie_id) queryParams.append('movie_id', params.movie_id);
        if (params.movie_title) queryParams.append('movie_title', params.movie_title);
        if (params.chain) queryParams.append('chain', params.chain);
        if (params.date) queryParams.append('date', params.date);
        if (params.skip !== undefined) queryParams.append('skip', params.skip);
        if (params.limit !== undefined) queryParams.append('limit', params.limit);
        
        const response = await fetch(`${API_BASE_URL}/api/showtimes?${queryParams}`);
        return response.json();
    },

    searchShowtimes: async (query, cinemaName = null) => {
        const url = cinemaName
            ? `${API_BASE_URL}/api/search/showtimes?q=${encodeURIComponent(query)}&cinema_name=${encodeURIComponent(cinemaName)}`
            : `${API_BASE_URL}/api/search/showtimes?q=${encodeURIComponent(query)}`;
        const response = await fetch(url);
        return response.json();
    },

    // ✅ 座位相關（新增）
    getSeats: async (showtimeId) => {
        const response = await fetch(`${API_BASE_URL}/api/seats/${encodeURIComponent(showtimeId)}`);
        if (!response.ok) {
            throw new Error('無法獲取座位資訊');
        }
        return response.json();
    },

    // 訂票相關
    createBooking: async (bookingData) => {
        const response = await fetch(`${API_BASE_URL}/api/bookings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bookingData),
        });
        return response.json();
    },

    getBooking: async (orderNumber) => {
        const response = await fetch(`${API_BASE_URL}/api/bookings/${orderNumber}`);
        return response.json();
    },

    // 統計相關
    getStats: async () => {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        return response.json();
    },
};

export default api;