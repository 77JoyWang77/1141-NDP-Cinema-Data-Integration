import React, { useState, useMemo } from 'react';
import { MapPin, Calendar, Clock, Film, Filter } from 'lucide-react';

export default function ShowtimesForMovie({ showtimes, loading, onSelectShowtime }) {
    const [activeTab, setActiveTab] = useState('all');
    const [selectedDate, setSelectedDate] = useState('all');
    const [selectedCinema, setSelectedCinema] = useState('all');

    // 按影城鏈分組
    const showtimesByChain = {
        all: showtimes || [],
        showtime: (showtimes || []).filter(s => s.chain === 'showtime'),
        vieshow: (showtimes || []).filter(s => s.chain === 'vieshow')
    };

    // ✅ 取得所有可用日期
    const availableDates = useMemo(() => {
        const dates = new Set();
        (showtimesByChain[activeTab] || []).forEach(s => {
            if (s.date) dates.add(s.date);
        });
        return Array.from(dates).sort();
    }, [showtimesByChain, activeTab]);

    // ✅ 取得所有可用影城
    const availableCinemas = useMemo(() => {
        const cinemas = new Set();
        (showtimesByChain[activeTab] || []).forEach(s => {
            if (s.cinema_name) cinemas.add(s.cinema_name);
        });
        return Array.from(cinemas).sort();
    }, [showtimesByChain, activeTab]);

    // ✅ 篩選場次
    const filteredShowtimes = useMemo(() => {
        let times = showtimesByChain[activeTab] || [];
        
        if (selectedDate !== 'all') {
            times = times.filter(s => s.date === selectedDate);
        }
        
        if (selectedCinema !== 'all') {
            times = times.filter(s => s.cinema_name === selectedCinema);
        }
        
        return times;
    }, [showtimesByChain, activeTab, selectedDate, selectedCinema]);

    // 重置篩選器（當切換分頁時）
    const handleTabChange = (tab) => {
        setActiveTab(tab);
        setSelectedDate('all');
        setSelectedCinema('all');
    };

    const renderShowtimeCards = (times) => {
        if (!times || times.length === 0) {
            return (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <p className="text-gray-500 text-lg">目前沒有場次資料</p>
                    <p className="text-gray-400 text-sm mt-2">請稍後再試或選擇其他篩選條件</p>
                </div>
            );
        }

        // 按日期分組
        const groupedByDate = {};
        times.forEach(time => {
            const date = time.date || '未知日期';
            if (!groupedByDate[date]) {
                groupedByDate[date] = [];
            }
            groupedByDate[date].push(time);
        });

        return (
            <div className="space-y-6">
                {Object.entries(groupedByDate).map(([date, timesForDate]) => {
                    // 按影城分組
                    const groupedByCinema = {};
                    timesForDate.forEach(time => {
                        const cinema = time.cinema_name || '未知影城';
                        if (!groupedByCinema[cinema]) {
                            groupedByCinema[cinema] = [];
                        }
                        groupedByCinema[cinema].push(time);
                    });

                    return (
                        <div key={date} className="border rounded-lg overflow-hidden">
                            {/* 日期標題 */}
                            <div className="bg-gradient-to-r from-blue-600 to-blue-500 px-4 py-3 text-white">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Calendar size={20} />
                                        <span className="font-semibold text-lg">{date}</span>
                                    </div>
                                    <span className="text-sm bg-white bg-opacity-20 px-3 py-1 rounded">
                                        {timesForDate.length} 場
                                    </span>
                                </div>
                            </div>

                            {/* 按影城顯示場次 */}
                            <div className="p-4 space-y-4">
                                {Object.entries(groupedByCinema).map(([cinema, cinemaTimes]) => (
                                    <div key={cinema} className="border-l-4 border-blue-500 pl-4">
                                        <div className="flex items-center gap-2 mb-3">
                                            <MapPin size={18} className="text-red-500" />
                                            <span className="font-semibold text-gray-800">{cinema}</span>
                                            <span className="text-xs text-gray-500">
                                                ({cinemaTimes.length} 場)
                                            </span>
                                            {cinemaTimes[0].chain === 'showtime' && (
                                                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                                                    秀泰
                                                </span>
                                            )}
                                            {cinemaTimes[0].chain === 'vieshow' && (
                                                <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                                                    威秀
                                                </span>
                                            )}
                                        </div>

                                        {/* 場次時間卡片 */}
                                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                                            {cinemaTimes.map((showtime, idx) => (
                                                <div
                                                    key={idx}
                                                    onClick={() => onSelectShowtime?.(showtime)}
                                                    className="p-3 border rounded-lg hover:shadow-lg transition-all cursor-pointer hover:border-blue-500 bg-white group"
                                                >
                                                    {/* 時間 */}
                                                    <div className="flex items-center gap-2 font-semibold text-lg text-blue-600 mb-2">
                                                        <Clock size={16} />
                                                        {showtime.show_time || showtime.time || '時間未定'}
                                                    </div>

                                                    {/* 廳別 */}
                                                    {showtime.screen_number && (
                                                        <div className="text-xs text-gray-600 mb-1">
                                                            {showtime.screen_number}
                                                        </div>
                                                    )}

                                                    {/* 版本類型 */}
                                                    {showtime.screen_type && (
                                                        <div className="flex items-center gap-1 text-xs text-gray-600 mb-2">
                                                            <Film size={12} className="text-green-600" />
                                                            <span className="truncate">{showtime.screen_type}</span>
                                                        </div>
                                                    )}

                                                    {/* 時間範圍（秀泰有） */}
                                                    {showtime.time_range && (
                                                        <div className="text-xs text-gray-500 mb-2">
                                                            {showtime.time_range}
                                                        </div>
                                                    )}

                                                    {/* 星期（秀泰有） */}
                                                    {showtime.weekday && (
                                                        <div className="text-xs text-gray-500">
                                                            {showtime.weekday}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-6">上映場次</h2>

            {loading ? (
                <div className="text-center py-12">
                    <div className="inline-block animate-spin">
                        <div className="border-4 border-gray-200 border-t-blue-600 rounded-full w-8 h-8"></div>
                    </div>
                    <p className="mt-4 text-gray-500">載入中...</p>
                </div>
            ) : (
                <>
                    {/* ✅ 影城鏈分頁標籤 */}
                    {(showtimesByChain.showtime.length > 0 || showtimesByChain.vieshow.length > 0) && (
                        <div className="flex gap-2 mb-6 border-b">
                            <button
                                onClick={() => handleTabChange('all')}
                                className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
                                    activeTab === 'all'
                                        ? 'border-blue-600 text-blue-600'
                                        : 'border-transparent text-gray-600 hover:text-gray-900'
                                }`}
                            >
                                全部 ({showtimesByChain.all.length})
                            </button>
                            {showtimesByChain.showtime.length > 0 && (
                                <button
                                    onClick={() => handleTabChange('showtime')}
                                    className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
                                        activeTab === 'showtime'
                                            ? 'border-blue-600 text-blue-600'
                                            : 'border-transparent text-gray-600 hover:text-gray-900'
                                    }`}
                                >
                                    秀泰 ({showtimesByChain.showtime.length})
                                </button>
                            )}
                            {showtimesByChain.vieshow.length > 0 && (
                                <button
                                    onClick={() => handleTabChange('vieshow')}
                                    className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
                                        activeTab === 'vieshow'
                                            ? 'border-purple-600 text-purple-600'
                                            : 'border-transparent text-gray-600 hover:text-gray-900'
                                    }`}
                                >
                                    威秀 ({showtimesByChain.vieshow.length})
                                </button>
                            )}
                        </div>
                    )}

                    {/* ✅ 篩選器 */}
                    {showtimesByChain[activeTab].length > 0 && (
                        <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg border">
                            <div className="flex items-center gap-2 text-gray-700">
                                <Filter size={18} />
                                <span className="font-semibold">篩選：</span>
                            </div>
                            
                            {/* 日期篩選 */}
                            <select
                                value={selectedDate}
                                onChange={(e) => setSelectedDate(e.target.value)}
                                className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                            >
                                <option value="all">所有日期</option>
                                {availableDates.map(date => (
                                    <option key={date} value={date}>{date}</option>
                                ))}
                            </select>

                            {/* 影城篩選 */}
                            <select
                                value={selectedCinema}
                                onChange={(e) => setSelectedCinema(e.target.value)}
                                className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                            >
                                <option value="all">所有影城</option>
                                {availableCinemas.map(cinema => (
                                    <option key={cinema} value={cinema}>{cinema}</option>
                                ))}
                            </select>

                            {/* 顯示篩選結果數量 */}
                            <div className="ml-auto text-sm text-gray-600 flex items-center">
                                顯示 <span className="font-semibold mx-1">{filteredShowtimes.length}</span> 場
                            </div>
                        </div>
                    )}

                    {/* 場次內容 */}
                    {renderShowtimeCards(filteredShowtimes)}
                </>
            )}
        </div>
    );
}