import React, { useState } from 'react';
import { Film, MapPin, Calendar, Clock } from 'lucide-react';
import ShowtimeModal from './ShowtimeModal';

function ShowtimesList({ showtimes }) {
    const [selectedShowtime, setSelectedShowtime] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    if (!showtimes || showtimes.length === 0) {
        return (
            <div className="text-center py-12">
                <div className="text-gray-400 mb-2">
                    <Film size={48} className="mx-auto" />
                </div>
                <p className="text-gray-500">沒有找到放映場次</p>
                <p className="text-gray-400 text-sm mt-2">請調整篩選條件</p>
            </div>
        );
    }

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
            <div className="px-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">

                    {showtimes.map((showtime, index) => (
                        <div
                        key={index}
                        onClick={() => handleSelectShowtime(showtime)}
                        className="bg-white rounded-md border hover:shadow-md transition
                                    cursor-pointer p-3 space-y-2"
                        >
                        {/* 電影名稱 */}
                        <h4 className="font-semibold text-sm line-clamp-1">
                            {showtime.movie_title_cn}
                        </h4>

                        {/* 影城 */}
                        <div className="flex items-center text-xs text-gray-600">
                            <MapPin size={12} className="mr-1 text-red-500" />
                            <span className="line-clamp-1">{showtime.cinema_name}</span>
                        </div>

                        {/* 日期 + 星期 + 時間 range */}
                        <div className="flex items-center justify-between text-xs">
                            <div className="flex items-center text-gray-600">
                            <Calendar size={12} className="mr-1 text-green-500" />
                            <span>
                                {showtime.date}
                                {showtime.weekday && (
                                <span className="ml-1 text-gray-400">
                                    ({showtime.weekday})
                                </span>
                                )}
                            </span>
                            </div>

                            {showtime.time_range && (
                            <div className="flex items-center font-semibold text-blue-600">
                                <Clock size={12} className="mr-1" />
                                {showtime.time_range}
                            </div>
                            )}
                        </div>

                        {/* 廳別 / 版本 */}
                        {(showtime.screen_type || showtime.screen_number) && (
                            <div className="flex flex-wrap gap-1">
                            {showtime.screen_type && (
                                <span className="text-[11px] px-2 py-0.5 rounded bg-blue-50 text-blue-700">
                                {showtime.screen_type}
                                </span>
                            )}
                            {showtime.screen_number && (
                                <span className="text-[11px] px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                                {showtime.screen_number}
                                </span>
                            )}
                        </div>
                        )}
                    </div>
                    ))}
                </div>
            </div>


            <ShowtimeModal
                showtime={selectedShowtime}
                isOpen={isModalOpen}
                onClose={handleCloseModal}
            />
        </>
    );
}

export default ShowtimesList;
