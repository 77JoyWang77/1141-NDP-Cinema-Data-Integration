import React, { useState, useEffect } from 'react';
import api from '../api';
import ShowtimesForMovie from './ShowtimesForMovie';
import ShowtimeModal from './ShowtimeModal';
import { Calendar, Clock, Film, Users, MapPin } from 'lucide-react';

export default function MovieDetail({ movie }) {
    const [showtimes, setShowtimes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedShowtime, setSelectedShowtime] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        loadShowtimes();
    }, [movie._id]);

    const loadShowtimes = async () => {
        setLoading(true);
        try {
            const results = await api.getMovieShowtimes(movie._id);
            setShowtimes(results);
        } catch (error) {
            console.error('載入場次失敗:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectShowtime = (showtime) => {
        setSelectedShowtime(showtime);
        setIsModalOpen(true);
    };

    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedShowtime(null);
    };

    return (
        <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 左側：電影信息 */}
                <div className="lg:col-span-1 space-y-4">
                    <div className="bg-white rounded-lg shadow-lg p-6">
                        <h1 className="text-2xl font-bold mb-2">{movie.title_cn}</h1>
                        <p className="text-gray-600 mb-4">{movie.title_en}</p>

                        {/* 基本信息 */}
                        <div className="space-y-3 mb-6">
                            {/* 評分 */}
                            <div className="flex items-center gap-2">
                                <span className="font-semibold">評分:</span>
                                <span className={`px-3 py-1 rounded font-bold text-white ${
                                    movie.rating === '普遍級' ? 'bg-green-500' :
                                    movie.rating === '保護級' ? 'bg-blue-500' :
                                    movie.rating === '輔12級' ? 'bg-yellow-500' :
                                    movie.rating === '輔15級' ? 'bg-orange-500' :
                                    movie.rating === '限制級' ? 'bg-red-500' :
                                    'bg-gray-500'
                                }`}>
                                    {movie.rating || '未分級'}
                                </span>
                            </div>

                            {/* 發行日期 */}
                            {movie.release_date && (
                                <div className="flex items-center gap-2">
                                    <Calendar size={20} className="text-blue-600" />
                                    <div>
                                        <p className="font-semibold">發行日期</p>
                                        <p className="text-gray-700">{movie.release_date}</p>
                                    </div>
                                </div>
                            )}

                            {/* 片長 */}
                            {movie.runtime_min && (
                                <div className="flex items-center gap-2">
                                    <Clock size={20} className="text-blue-600" />
                                    <div>
                                        <p className="font-semibold">片長</p>
                                        <p className="text-gray-700">{movie.runtime_min} 分鐘</p>
                                    </div>
                                </div>
                            )}

                            {/* 類型 */}
                            {movie.genres && movie.genres.length > 0 && (
                                <div className="flex items-center gap-2">
                                    <Film size={20} className="text-blue-600" />
                                    <div>
                                        <p className="font-semibold">類型</p>
                                        <div className="flex flex-wrap gap-2 mt-1">
                                            {movie.genres.map(genre => (
                                                <span key={genre} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                                    {genre}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* 導演 */}
                            {movie.director && (
                                <div>
                                    <p className="font-semibold">導演</p>
                                    <p className="text-gray-700">{movie.director}</p>
                                </div>
                            )}

                            {/* 主演 */}
                            {movie.actors && movie.actors.length > 0 && (
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <Users size={20} className="text-blue-600" />
                                        <p className="font-semibold">主演</p>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {movie.actors.slice(0, 5).map(actor => (
                                            <span key={actor} className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">
                                                {actor}
                                            </span>
                                        ))}
                                        {movie.actors.length > 5 && (
                                            <span className="text-xs text-gray-500 px-2 py-1">
                                                +{movie.actors.length - 5} 位
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* 來源 */}
                            {movie.sources && movie.sources.length > 0 && (
                                <div className="pt-4 border-t">
                                    <p className="font-semibold mb-2">資料來源</p>
                                    <div className="flex gap-2">
                                        {movie.sources.includes('showtime') && (
                                            <span className="bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded">
                                                秀泰影城
                                            </span>
                                        )}
                                        {movie.sources.includes('vieshow') && (
                                            <span className="bg-purple-100 text-purple-800 text-xs px-3 py-1 rounded">
                                                威秀影城
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* 上映影城 */}
                    {movie.available_cinemas && movie.available_cinemas.length > 0 && (
                        <div className="bg-white rounded-lg shadow-lg p-6">
                            <div className="flex items-center gap-2 mb-4">
                                <MapPin size={20} className="text-red-500" />
                                <p className="font-semibold">上映影城 ({movie.available_cinemas.length})</p>
                            </div>
                            <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                                {movie.available_cinemas.map(cinema => (
                                    <div key={cinema} className="flex items-center gap-2 text-sm text-gray-700 p-2 hover:bg-gray-50 rounded">
                                        <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                                        {cinema}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* 劇情 */}
                    {movie.synopsis && (
                        <div className="bg-white rounded-lg shadow-lg p-6">
                            <p className="font-semibold mb-3">劇情簡介</p>
                            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
                                {movie.synopsis}
                            </p>
                        </div>
                    )}
                </div>

                {/* 右側：場次列表 */}
                <div className="lg:col-span-2">
                    <ShowtimesForMovie 
                        showtimes={showtimes} 
                        loading={loading}
                        onSelectShowtime={handleSelectShowtime}
                    />
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