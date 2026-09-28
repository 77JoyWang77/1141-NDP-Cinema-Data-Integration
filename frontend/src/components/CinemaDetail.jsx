import React, { useState, useEffect } from 'react';
import api from '../api';
import ShowtimeModal from './ShowtimeModal';
import { MapPin, Phone, Globe, Calendar, Clock, Film, Info } from 'lucide-react';

export default function CinemaDetail({ cinema }) {
    const [showtimes, setShowtimes] = useState([]);
    const [filteredShowtimes, setFilteredShowtimes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedDate, setSelectedDate] = useState(null);
    const [availableDates, setAvailableDates] = useState([]);
    const [selectedShowtime, setSelectedShowtime] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        loadShowtimes();
    }, [cinema._id]);

    useEffect(() => {
        filterShowtimes();
    }, [showtimes, selectedDate]);

    const loadShowtimes = async () => {
        setLoading(true);
        try {
            const results = await api.getCinemaShowtimes(cinema._id);
            setShowtimes(results);

            const dates = [...new Set(results.map(s => s.date))].sort();
            setAvailableDates(dates);
            if (dates.length > 0) {
                setSelectedDate(dates[0]);
            }
        } catch (error) {
            console.error('載入場次失敗:', error);
        } finally {
            setLoading(false);
        }
    };

    const filterShowtimes = () => {
        if (!selectedDate) {
            setFilteredShowtimes(showtimes);
            return;
        }
        const filtered = showtimes.filter(s => s.date === selectedDate);
        setFilteredShowtimes(filtered);
    };

    const handleSelectShowtime = (showtime) => {
        setSelectedShowtime(showtime);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedShowtime(null);
    };

    const groupedByMovie = {};
    filteredShowtimes.forEach(showtime => {
        const movieTitle = showtime.movie_title_cn || showtime.movie_title || '未知電影';
        if (!groupedByMovie[movieTitle]) {
            groupedByMovie[movieTitle] = [];
        }
        groupedByMovie[movieTitle].push(showtime);
    });

    return (
        <>
            <div className="space-y-6">
                {/* 影城信息卡 */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                        <div>
                            <h1 className="text-3xl font-bold mb-2">{cinema.name}</h1>
                            {cinema.chain_name && (
                                <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${
                                    cinema.chain === 'showtime' 
                                        ? 'bg-blue-100 text-blue-800' 
                                        : 'bg-purple-100 text-purple-800'
                                }`}>
                                    {cinema.chain_name}
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {cinema.address && (
                            <div className="flex items-start gap-3">
                                <MapPin size={24} className="text-red-500 flex-shrink-0 mt-1" />
                                <div>
                                    <p className="font-semibold">地址</p>
                                    <p className="text-gray-700">{cinema.address}</p>
                                </div>
                            </div>
                        )}

                        {cinema.phone && (
                            <div className="flex items-start gap-3">
                                <Phone size={24} className="text-green-500 flex-shrink-0 mt-1" />
                                <div>
                                    <p className="font-semibold">電話</p>
                                    <p className="text-gray-700">{cinema.phone}</p>
                                </div>
                            </div>
                        )}

                        {cinema.website && (
                            <div className="flex items-start gap-3">
                                <Globe size={24} className="text-blue-500 flex-shrink-0 mt-1" />
                                <div>
                                    <p className="font-semibold">網站</p>
                                    <a
                                        href={cinema.website}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline"
                                    >
                                        {cinema.website}
                                    </a>
                                </div>
                            </div>
                        )}

                        {cinema.screen_count && (
                            <div className="flex items-start gap-3">
                                <Film size={24} className="text-purple-500 flex-shrink-0 mt-1" />
                                <div>
                                    <p className="font-semibold">廳數</p>
                                    <p className="text-gray-700">{cinema.screen_count} 廳</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {cinema.ticket_prices && cinema.ticket_prices.length > 0 && (
                        <div className="mt-6 pt-6 border-t">
                            <div className="flex items-center gap-2 mb-4">
                                <Info size={20} className="text-blue-600" />
                                <h3 className="font-semibold text-lg">票價資訊</h3>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {cinema.ticket_prices.map((price, idx) => (
                                    <div key={idx} className="bg-gray-50 rounded-lg p-3">
                                        <p className="font-semibold text-sm text-gray-800 mb-2">
                                            {price.version}
                                        </p>
                                        <div className="grid grid-cols-2 gap-2 text-xs">
                                            {price.prices.full && (
                                                <div>
                                                    <span className="text-gray-600">全票: </span>
                                                    <span className="font-semibold">${price.prices.full}</span>
                                                </div>
                                            )}
                                            {price.prices.discount && (
                                                <div>
                                                    <span className="text-gray-600">優待: </span>
                                                    <span className="font-semibold">${price.prices.discount}</span>
                                                </div>
                                            )}
                                            {price.prices.morning && (
                                                <div>
                                                    <span className="text-gray-600">早場: </span>
                                                    <span className="font-semibold">${price.prices.morning}</span>
                                                </div>
                                            )}
                                            {price.prices.charity && (
                                                <div>
                                                    <span className="text-gray-600">愛心: </span>
                                                    <span className="font-semibold">${price.prices.charity}</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            {cinema.ticket_extra_rules && (
                                <div className="mt-3 p-3 bg-yellow-50 rounded-lg">
                                    <p className="text-xs text-gray-700">
                                        <span className="font-semibold">加價規則: </span>
                                        {cinema.ticket_extra_rules}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* 場次列表 */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h2 className="text-2xl font-bold mb-6">上映場次</h2>

                    {loading ? (
                        <div className="text-center py-8">
                            <div className="inline-block animate-spin">
                                <div className="border-4 border-gray-200 border-t-blue-600 rounded-full w-8 h-8"></div>
                            </div>
                            <p className="mt-4 text-gray-500">載入中...</p>
                        </div>
                    ) : (
                        <>
                            {availableDates.length > 0 && (
                                <div className="mb-6">
                                    <p className="font-semibold mb-3 flex items-center gap-2">
                                        <Calendar size={18} />
                                        選擇日期
                                    </p>
                                    <div className="flex flex-wrap gap-2">
                                        {availableDates.map(date => (
                                            <button
                                                key={date}
                                                onClick={() => setSelectedDate(date)}
                                                className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                                                    selectedDate === date
                                                        ? 'bg-blue-600 text-white'
                                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                                }`}
                                            >
                                                {date}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {Object.keys(groupedByMovie).length > 0 ? (
                                <div className="space-y-6">
                                    {Object.entries(groupedByMovie).map(([movieTitle, times]) => (
                                        <div key={movieTitle} className="border rounded-lg overflow-hidden">
                                            <div className="bg-gradient-to-r from-blue-600 to-blue-500 px-4 py-3 text-white">
                                                <div className="flex items-center justify-between">
                                                    <h3 className="font-semibold text-lg">{movieTitle}</h3>
                                                    <span className="text-sm bg-white bg-opacity-20 px-3 py-1 rounded">
                                                        {times.length} 場
                                                    </span>
                                                </div>
                                            </div>
                                            
                                            {/* ✅ 移除按鈕，只保留點擊卡片 */}
                                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 p-4">
                                                {times.map((showtime, idx) => (
                                                    <div
                                                        key={idx}
                                                        onClick={() => handleSelectShowtime(showtime)}
                                                        className="p-3 border rounded-lg hover:shadow-lg transition-all cursor-pointer hover:border-blue-500 bg-white group"
                                                    >
                                                        <div className="flex items-center gap-2 font-bold text-blue-600 text-lg mb-2">
                                                            <Clock size={16} />
                                                            {showtime.show_time || showtime.time || '未定'}
                                                        </div>

                                                        {showtime.screen_number && (
                                                            <p className="text-xs text-gray-600 mb-1">
                                                                {showtime.screen_number}
                                                            </p>
                                                        )}

                                                        {showtime.screen_type && (
                                                            <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                                                                {showtime.screen_type}
                                                            </p>
                                                        )}

                                                        {showtime.time_range && (
                                                            <p className="text-xs text-gray-500 mb-2">
                                                                {showtime.time_range}
                                                            </p>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 bg-gray-50 rounded-lg">
                                    <p className="text-gray-500 text-lg">
                                        {selectedDate ? `${selectedDate} 沒有場次` : '沒有場次資料'}
                                    </p>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* 座位選擇彈窗 */}
            <ShowtimeModal
                showtime={selectedShowtime}
                isOpen={isModalOpen}
                onClose={handleCloseModal}
            />
        </>
    );
}