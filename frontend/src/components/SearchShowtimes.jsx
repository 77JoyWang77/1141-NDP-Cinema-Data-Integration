import React, { useState, useMemo, useEffect } from 'react';
import { Search, Filter, Calendar, MapPin, Film, X } from 'lucide-react';

function SearchShowtimes({ cinemas, onSearch, allShowtimes = [] }) {
    const [filters, setFilters] = useState({
        cinema_name: '',
        chain: '',
        date: '',
        movie_title: ''
    });
    const [isExpanded, setIsExpanded] = useState(false);

    // 提取影城鏈（秀泰、威秀）
    const chains = useMemo(() => {
        const chainSet = new Set(cinemas.map(c => c.chain_name).filter(Boolean));
        return Array.from(chainSet).sort();
    }, [cinemas]);

    // 根據選擇的影城鏈過濾影城
    const filteredCinemas = useMemo(() => {
        if (!filters.chain) return cinemas;
        return cinemas.filter(c => c.chain_name === filters.chain);
    }, [cinemas, filters.chain]);

    // ✅ 生成未來 7 天的日期選項
    const dateOptions = useMemo(() => {
        const dates = [];
        const today = new Date();
        
        for (let i = 0; i < 7; i++) {
            const date = new Date(today);
            date.setDate(today.getDate() + i);
            
            const month = date.getMonth() + 1;
            const day = date.getDate();
            const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()];
            
            dates.push({
                value: `${month}月${day}日`,
                label: `${month}月${day}日 (${weekday})`,
                isToday: i === 0
            });
        }
        
        return dates;
    }, []);

    // ✅ 提取電影列表（從場次中去重）
    const movieOptions = useMemo(() => {
        if (!allShowtimes || allShowtimes.length === 0) return [];
        
        const movieSet = new Set();
        allShowtimes.forEach(showtime => {
            if (showtime.movie_title_cn) {
                movieSet.add(showtime.movie_title_cn);
            }
        });
        
        return Array.from(movieSet).sort();
    }, [allShowtimes]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => {
            const newFilters = { ...prev, [name]: value };
            // 如果更改影城鏈，清空影城選擇
            if (name === 'chain') {
                newFilters.cinema_name = '';
            }
            return newFilters;
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSearch(filters);
    };

    const handleReset = () => {
        setFilters({ cinema_name: '', chain: '', date: '', movie_title: '' });
        onSearch({ cinema_name: '', chain: '', date: '', movie_title: '' });
    };

    // ✅ 自動搜尋（當篩選條件改變時）
    useEffect(() => {
        onSearch(filters);
    }, [filters]);

    const hasActiveFilters = Object.values(filters).some(v => v !== '');

    return (
        <div className="px-4">
            <div className="bg-white rounded-lg shadow-md mb-6">
                {/* 標題列 */}
                <div 
                    className="p-4 border-b border-gray-200 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <h2 className="text-xl font-bold flex items-center">
                        <Filter className="mr-2 text-blue-600" size={22} />
                        篩選場次
                        {hasActiveFilters && (
                            <span className="ml-2 text-sm bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                                {Object.values(filters).filter(v => v !== '').length}
                            </span>
                        )}
                    </h2>
                    <button className="text-gray-500 hover:text-gray-700">
                        {isExpanded ? '收起' : '展開'}
                    </button>
                </div>

                {/* 篩選器內容 */}
                {isExpanded && (
                    <div className="p-4 space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {/* 影城篩選 */}
                            <div>
                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                    <MapPin size={16} className="mr-1.5 text-red-600" />
                                    影城
                                </label>
                                <select
                                    name="cinema_name"
                                    value={filters.cinema_name}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">所有影城</option>
                                    {filteredCinemas.map(cinema => (
                                        <option key={cinema.name} value={cinema.name}>
                                            {cinema.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* ✅ 日期下拉選單（未來 7 天）*/}
                            <div>
                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                    <Calendar size={16} className="mr-1.5 text-green-600" />
                                    日期
                                </label>
                                <select
                                    name="date"
                                    value={filters.date}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">所有日期</option>
                                    {dateOptions.map(date => (
                                        <option key={date.value} value={date.value}>
                                            {date.label} {date.isToday ? '(今天)' : ''}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* ✅ 電影下拉選單 */}
                            {/* <div>
                                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                                    <Search size={16} className="mr-1.5 text-purple-600" />
                                    電影
                                </label>
                                <select
                                    name="movie_title"
                                    value={filters.movie_title}
                                    onChange={handleChange}
                                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">所有電影</option>
                                    {movieOptions.map(movie => (
                                        <option key={movie} value={movie}>
                                            {movie}
                                        </option>
                                    ))}
                                </select>
                            </div> */}
                        </div>

                        {/* 清除按鈕 */}
                        {hasActiveFilters && (
                            <div className="flex justify-end pt-2">
                                <button
                                    type="button"
                                    onClick={handleReset}
                                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition text-sm font-medium flex items-center"
                                >
                                    <X size={16} className="mr-1.5" />
                                    清除所有篩選
                                </button>
                            </div>
                        )}

                        {/* 活動篩選標籤 */}
                        {hasActiveFilters && (
                            <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
                                <span className="text-xs text-gray-500">目前篩選：</span>
                                {filters.chain && (
                                    <span className="inline-flex items-center text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                                        {filters.chain}
                                        <button
                                            type="button"
                                            onClick={() => handleChange({ target: { name: 'chain', value: '' } })}
                                            className="ml-1 hover:text-blue-900"
                                        >
                                            <X size={12} />
                                        </button>
                                    </span>
                                )}
                                {filters.cinema_name && (
                                    <span className="inline-flex items-center text-xs bg-red-50 text-red-700 px-2 py-1 rounded">
                                        {filters.cinema_name}
                                        <button
                                            type="button"
                                            onClick={() => handleChange({ target: { name: 'cinema_name', value: '' } })}
                                            className="ml-1 hover:text-red-900"
                                        >
                                            <X size={12} />
                                        </button>
                                    </span>
                                )}
                                {filters.date && (
                                    <span className="inline-flex items-center text-xs bg-green-50 text-green-700 px-2 py-1 rounded">
                                        {filters.date}
                                        <button
                                            type="button"
                                            onClick={() => handleChange({ target: { name: 'date', value: '' } })}
                                            className="ml-1 hover:text-green-900"
                                        >
                                            <X size={12} />
                                        </button>
                                    </span>
                                )}
                                {filters.movie_title && (
                                    <span className="inline-flex items-center text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
                                        {filters.movie_title}
                                        <button
                                            type="button"
                                            onClick={() => handleChange({ target: { name: 'movie_title', value: '' } })}
                                            className="ml-1 hover:text-purple-900"
                                        >
                                            <X size={12} />
                                        </button>
                                    </span>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default SearchShowtimes;