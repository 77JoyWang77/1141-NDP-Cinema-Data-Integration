import React, { useState, useEffect } from 'react';
import api from './api';
import SearchShowtimes from './components/SearchShowtimes';
import ShowtimesList from './components/ShowtimesList';
import MovieList from './components/MovieList';
import MovieDetail from './components/MovieDetail';
import CinemaList from './components/CinemaList';
import CinemaDetail from './components/CinemaDetail';
import ShowtimeDetail from './components/ShowtimeDetail';
import Stats from './components/Stats';
import { Film, Building, Clock, BarChart3, Search } from 'lucide-react';

function App() {
    const [activeTab, setActiveTab] = useState('movies');
    const [showtimes, setShowtimes] = useState([]);
    const [cinemas, setCinemas] = useState([]);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState(null);

    // 詳情頁面狀態
    const [selectedMovie, setSelectedMovie] = useState(null);
    const [selectedCinema, setSelectedCinema] = useState(null);
    const [selectedShowtime, setSelectedShowtime] = useState(null);

    useEffect(() => {
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        try {
            const [cinemasData, statsData] = await Promise.all([
                api.getCinemas(),
                api.getStats()
            ]);
            setCinemas(cinemasData);
            setStats(statsData);
        } catch (error) {
            console.error('載入初始數據失敗:', error);
        }
    };

    const handleSearch = async (filters) => {
        setLoading(true);
        try {
            const results = await api.getShowtimes(filters);
            setShowtimes(results);
        } catch (error) {
            console.error('搜尋失敗:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            {/* 導航欄 */}
            <nav className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg sticky top-0 z-40">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between mb-4">
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            🎬 電影票訂系統
                        </h1>
                    </div>

                    {/* 分頁按鈕 */}
                    <div className="flex overflow-x-auto gap-2 pb-2">
                        <button
                            onClick={() => {
                                setActiveTab('search');
                                setSelectedMovie(null);
                                setSelectedCinema(null);
                                setSelectedShowtime(null);
                            }}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-all ${activeTab === 'search'
                                ? 'bg-white text-blue-600 font-semibold'
                                : 'hover:bg-blue-500'
                                }`}
                        >
                            <Search size={18} />
                            搜尋場次
                        </button>

                        <button
                            onClick={() => {
                                setActiveTab('movies');
                                setSelectedMovie(null);
                            }}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-all ${activeTab === 'movies'
                                ? 'bg-white text-blue-600 font-semibold'
                                : 'hover:bg-blue-500'
                                }`}
                        >
                            <Film size={18} />
                            電影
                        </button>

                        <button
                            onClick={() => {
                                setActiveTab('cinemas');
                                setSelectedCinema(null);
                            }}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-all ${activeTab === 'cinemas'
                                ? 'bg-white text-blue-600 font-semibold'
                                : 'hover:bg-blue-500'
                                }`}
                        >
                            <Building size={18} />
                            影城
                        </button>

                        <button
                            onClick={() => setActiveTab('stats')}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg whitespace-nowrap transition-all ${activeTab === 'stats'
                                ? 'bg-white text-blue-600 font-semibold'
                                : 'hover:bg-blue-500'
                                }`}
                        >
                            <BarChart3 size={18} />
                            統計
                        </button>
                    </div>
                </div>
            </nav>

            {/* 返回按鈕（用於詳情頁面） */}
            {(selectedMovie || selectedCinema || selectedShowtime) && (
                <div className="bg-white border-b shadow-sm">
                    <div className="container mx-auto px-4 py-3">
                        <button
                            onClick={() => {
                                if (selectedShowtime) setSelectedShowtime(null);
                                else if (selectedMovie) setSelectedMovie(null);
                                else if (selectedCinema) setSelectedCinema(null);
                            }}
                            className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-2"
                        >
                            ← 返回
                        </button>
                    </div>
                </div>
            )}

            {/* 主容器 */}
            <div className="container mx-auto px-4 py-8">
                {/* 搜尋場次頁面 */}
                {activeTab === 'search' && (
                    <>
                        <SearchShowtimes cinemas={cinemas} onSearch={handleSearch} />
                        {loading && <div className="text-center py-8">載入中...</div>}
                        {!loading && showtimes.length > 0 && (
                            <ShowtimesList showtimes={showtimes} />
                        )}
                        {!loading && showtimes.length === 0 && (
                            <div className="text-center py-8 text-gray-500">
                                搜尋結果將在此顯示
                            </div>
                        )}
                    </>
                )}

                {/* 電影頁面 */}
                {activeTab === 'movies' && !selectedMovie && (
                    <MovieList onSelectMovie={setSelectedMovie} />
                )}

                {activeTab === 'movies' && selectedMovie && (
                    <MovieDetail
                        movie={selectedMovie}
                        onSelectShowtime={setSelectedShowtime}
                    />
                )}

                {/* 影城頁面 */}
                {activeTab === 'cinemas' && !selectedCinema && (
                    <CinemaList onSelectCinema={setSelectedCinema} />
                )}

                {activeTab === 'cinemas' && selectedCinema && (
                    <CinemaDetail
                        cinema={selectedCinema}
                        onSelectShowtime={setSelectedShowtime}
                    />
                )}

                {/* 場次詳情頁面 */}
                {selectedShowtime && (
                    <ShowtimeDetail
                        showtime={selectedShowtime}
                        onBook={() => {
                            alert('預訂成功！');
                            setSelectedShowtime(null);
                        }}
                    />
                )}

                {/* 統計頁面 */}
                {activeTab === 'stats' && stats && (
                    <Stats stats={stats} />
                )}
            </div>
        </div>
    );
}

export default App;
