import React, { useState, useEffect } from 'react';
import api from '../api';
import SearchShowtimes from './SearchShowtimes';
import ShowtimesList from './ShowtimesList';

function Showtimes() {
    const [cinemas, setCinemas] = useState([]);
    const [allShowtimes, setAllShowtimes] = useState([]);
    const [filteredShowtimes, setFilteredShowtimes] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    // 載入影城列表
    useEffect(() => {
        const fetchCinemas = async () => {
            try {
                const response = await api.get('/cinemas');
                setCinemas(response.data);
            } catch (error) {
                console.error('載入影城失敗:', error);
            }
        };
        fetchCinemas();
    }, []);

    // 載入未來 7 天的所有場次
    useEffect(() => {
        const fetchAllShowtimes = async () => {
            setIsLoading(true);
            try {
                const response = await api.get('/showtimes/all');
                setAllShowtimes(response.data);
                setFilteredShowtimes(response.data);
            } catch (error) {
                console.error('載入場次失敗:', error);
                setAllShowtimes([]);
                setFilteredShowtimes([]);
            } finally {
                setIsLoading(false);
            }
        };
        fetchAllShowtimes();
    }, []);

    // 前端篩選（即時）
    const handleSearch = (filters) => {
        let results = allShowtimes;
        
        if (filters.chain) {
            results = results.filter(s => s.chain_name === filters.chain);
        }
        if (filters.cinema_name) {
            results = results.filter(s => s.cinema_name === filters.cinema_name);
        }
        if (filters.date) {
            results = results.filter(s => s.date === filters.date);
        }
        if (filters.movie_title) {
            results = results.filter(s => s.movie_title_cn === filters.movie_title);
        }
        
        setFilteredShowtimes(results);
    };

    return (
       <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-6">搜尋放映場次</h1>

            <div className="max-w-6xl mx-auto space-y-6">
                <SearchShowtimes
                cinemas={cinemas}
                allShowtimes={allShowtimes}
                onSearch={handleSearch}
                />

                {isLoading ? (
                <div className="text-center py-12">載入中…</div>
                ) : (
                <ShowtimesList showtimes={filteredShowtimes} />
                )}
            </div>
        </div>

    );
}

export default Showtimes;