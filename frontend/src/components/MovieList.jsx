import React, { useState, useEffect } from 'react';
import api from '../api';
import MovieDetail from './MovieDetail';
import { ChevronLeft, Clock, Calendar, Film } from 'lucide-react';

export default function MovieList() {
    const [movies, setMovies] = useState([]);
    const [selectedMovie, setSelectedMovie] = useState(null);
    const [loading, setLoading] = useState(false);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [filterChain, setFilterChain] = useState('all');
    const limit = 12;

    useEffect(() => {
        loadMovies();
    }, [page, filterChain]);

    const loadMovies = async () => {
        setLoading(true);
        try {
            const chainParam = filterChain !== 'all' ? filterChain : null;
            const results = await api.getMovies(page * limit, limit, chainParam);
            
            if (page === 0) {
                setMovies(results);
            } else {
                setMovies(prev => [...prev, ...results]);
            }
            setHasMore(results.length === limit);
        } catch (error) {
            console.error('載入電影失敗:', error);
        } finally {
            setLoading(false);
        }
    };

    if (selectedMovie) {
        return (
            <div className="container mx-auto px-4 py-6">
                <button
                    onClick={() => setSelectedMovie(null)}
                    className="flex items-center gap-2 mb-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                    <ChevronLeft size={20} />
                    返回電影列表
                </button>
                <MovieDetail movie={selectedMovie} />
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-6">
            {/* 標題和篩選 */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <h2 className="text-3xl font-bold">🎬 電影列表</h2>
                
                {/* 影城鏈篩選 */}
                <div className="flex gap-2">
                    <button
                        onClick={() => { setFilterChain('all'); setPage(0); }}
                        className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                            filterChain === 'all' 
                                ? 'bg-blue-600 text-white' 
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                    >
                        全部
                    </button>
                    <button
                        onClick={() => { setFilterChain('showtime'); setPage(0); }}
                        className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                            filterChain === 'showtime' 
                                ? 'bg-blue-600 text-white' 
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                    >
                        秀泰
                    </button>
                    <button
                        onClick={() => { setFilterChain('vieshow'); setPage(0); }}
                        className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                            filterChain === 'vieshow' 
                                ? 'bg-purple-600 text-white' 
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                    >
                        威秀
                    </button>
                </div>
            </div>

            {/* 電影網格 */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-6">
                {movies.map(movie => (
                    <div
                        key={movie._id}
                        onClick={() => setSelectedMovie(movie)}
                        className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer overflow-hidden border hover:border-blue-500 transform hover:scale-105"
                    >
                        {/* 電影卡片頭部 */}
                        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-3 text-white">
                            <h3 className="font-bold text-sm mb-1 line-clamp-2 min-h-[40px]">
                                {movie.title_cn}
                            </h3>
                            <p className="text-xs opacity-90 line-clamp-1">
                                {movie.title_en}
                            </p>
                        </div>

                        {/* ✅ 卡片內容（移除按鈕） */}
                        <div className="p-4">
                            {/* 評分 */}
                            <div className="mb-3">
                                <span className={`inline-block text-xs px-3 py-1 rounded font-bold ${
                                    movie.rating === '普遍級' ? 'bg-green-500 text-white' :
                                    movie.rating === '保護級' ? 'bg-blue-500 text-white' :
                                    movie.rating === '輔12級' ? 'bg-yellow-500 text-white' :
                                    movie.rating === '輔15級' ? 'bg-orange-500 text-white' :
                                    movie.rating === '限制級' ? 'bg-red-500 text-white' :
                                    'bg-gray-500 text-white'
                                }`}>
                                    {movie.rating || '未分級'}
                                </span>
                            </div>

                            {/* 片長 */}
                            {movie.runtime_min && (
                                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                                    <Clock size={14} />
                                    <span>{movie.runtime_min} 分鐘</span>
                                </div>
                            )}

                            {/* 上映日期 */}
                            {movie.release_date && (
                                <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                                    <Calendar size={14} />
                                    <span>{movie.release_date}</span>
                                </div>
                            )}

                            {/* 類型 */}
                            {movie.genres && movie.genres.length > 0 && (
                                <div className="flex items-center gap-2 text-xs text-gray-600 mb-3">
                                    <Film size={14} />
                                    <span className="line-clamp-1">{movie.genres.join(', ')}</span>
                                </div>
                            )}

                            {/* 來源標籤 */}
                            <div className="flex gap-1 mb-3">
                                {movie.sources && movie.sources.includes('showtime') && (
                                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                        秀泰
                                    </span>
                                )}
                                {movie.sources && movie.sources.includes('vieshow') && (
                                    <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">
                                        威秀
                                    </span>
                                )}
                            </div>

                            {/* 上映影城數 */}
                            {movie.available_cinemas && movie.available_cinemas.length > 0 && (
                                <p className="text-xs text-gray-500">
                                    {movie.available_cinemas.length} 家影城上映
                                </p>
                            )}

                            {/* ✅ 移除了「查看詳情」按鈕 - 只保留點擊卡片 */}
                        </div>
                    </div>
                ))}
            </div>

            {/* 載入狀態 */}
            {loading && (
                <div className="text-center py-8">
                    <div className="inline-block animate-spin">
                        <div className="border-4 border-gray-200 border-t-blue-600 rounded-full w-8 h-8"></div>
                    </div>
                    <p className="mt-4 text-gray-500">載入中...</p>
                </div>
            )}

            {/* 分頁 */}
            {!loading && (
                <div className="flex justify-center gap-4 mt-6">
                    <button
                        disabled={page === 0}
                        onClick={() => setPage(Math.max(0, page - 1))}
                        className="px-6 py-2 bg-gray-300 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-400 transition-colors"
                    >
                        上一頁
                    </button>
                    <span className="py-2 px-4 bg-gray-100 rounded-lg font-semibold">
                        第 {page + 1} 頁
                    </span>
                    <button
                        disabled={!hasMore}
                        onClick={() => setPage(page + 1)}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors"
                    >
                        下一頁
                    </button>
                </div>
            )}

            {/* 無結果提示 */}
            {!loading && movies.length === 0 && (
                <div className="text-center py-12">
                    <p className="text-gray-500 text-lg">沒有找到電影</p>
                </div>
            )}
        </div>
    );
}