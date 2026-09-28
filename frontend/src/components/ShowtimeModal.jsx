import React, { useState, useEffect } from 'react';
import { X, MapPin, Clock, Film, Calendar, Users, AlertCircle, Check, RefreshCw } from 'lucide-react';
import api from '../api';

export default function ShowtimeModal({ showtime, onClose, isOpen }) {
    const [selectedSeats, setSelectedSeats] = useState([]);
    const [seatData, setSeatData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [bookingLoading, setBookingLoading] = useState(false);
    const [bookingSuccess, setBookingSuccess] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (isOpen && showtime) {
            loadSeats();
            setSelectedSeats([]);
            setBookingSuccess(false);
            setError(null);
        }
    }, [isOpen, showtime]);

    useEffect(() => {
        if (!isOpen) {
            setSelectedSeats([]);
            setSeatData(null);
            setBookingSuccess(false);
            setError(null);
        }
    }, [isOpen]);

    const loadSeats = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await api.getSeats(showtime._id);
            console.log('座位數據:', response);
            setSeatData(response);
        } catch (err) {
            console.error('載入座位失敗:', err);
            setError('載入座位資訊失敗，請稍後再試');
        } finally {
            setLoading(false);
        }
    };

    const toggleSeatSelection = (seat) => {
        if (seat.status === 'sold') return;
        
        // ✅ 使用唯一的 seat_id
        const seatId = seat.seat_id || `${seat.row}-${seat.seat_number || seat.number}`;
        
        if (selectedSeats.includes(seatId)) {
            setSelectedSeats(selectedSeats.filter(id => id !== seatId));
        } else {
            if (selectedSeats.length >= 6) {
                alert('最多只能選擇 6 個座位');
                return;
            }
            setSelectedSeats([...selectedSeats, seatId]);
        }
    };

    const handleBooking = async () => {
        if (selectedSeats.length === 0) {
            alert('請選擇座位');
            return;
        }

        setBookingLoading(true);
        try {
            await new Promise(resolve => setTimeout(resolve, 1500));
            setBookingSuccess(true);
            setTimeout(() => {
                onClose();
            }, 3000);
        } catch (error) {
            console.error('訂票失敗:', error);
            alert('訂票失敗，請重試');
        } finally {
            setBookingLoading(false);
        }
    };

    if (!isOpen || !showtime) return null;

    const ticketPrice = 300;
    const totalPrice = selectedSeats.length * ticketPrice;

    // ✅ 秀泰座位組織邏輯（絕對定位，不需要分組）
    const organizeShowtimeSeats = (seats) => {
        if (!seats || seats.length === 0) return [];
        
        console.log('🎫 秀泰座位數據:', seats.slice(0, 5));
        console.log('🎫 總座位數:', seats.length);
        
        // ✅ 去重
        const uniqueSeats = [];
        const seenIds = new Set();
        
        seats.forEach(seat => {
            const id = seat.seat_id || `${seat.row}-${seat.seat_number}`;
            if (!seenIds.has(id)) {
                seenIds.add(id);
                uniqueSeats.push(seat);
            }
        });
        
        console.log('🎫 去重後座位數:', uniqueSeats.length);
        
        // ✅ 直接返回所有座位（用絕對定位）
        return uniqueSeats;
    };

    // ✅ 威秀座位組織邏輯（按 row 和 number）
    const organizeVieshowSeats = (seats) => {
        if (!seats || seats.length === 0) return [];
        
        const rows = {};
        seats.forEach(seat => {
            const row = seat.row || 'A';
            if (!rows[row]) {
                rows[row] = [];
            }
            rows[row].push(seat);
        });

        // ✅ 按 col_idx 排序（保持走道位置）
        Object.keys(rows).forEach(row => {
            rows[row].sort((a, b) => (a.col_idx || 0) - (b.col_idx || 0));
        });

        // ✅ 按 row_idx 排序（而不是字母順序）
        return Object.entries(rows).sort((a, b) => {
            const rowIdxA = a[1][0]?.row_idx ?? 0;  // 取第一個座位的 row_idx
            const rowIdxB = b[1][0]?.row_idx ?? 0;
            return rowIdxA - rowIdxB;
        });
    };

    // ✅ 根據影城鏈選擇組織方式
    const seatRows = seatData?.seats 
        ? (showtime.chain === 'showtime' 
            ? organizeShowtimeSeats(seatData.seats)
            : organizeVieshowSeats(seatData.seats))
        : [];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div 
                className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
                onClick={onClose}
            ></div>

            <div 
                className="relative bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 z-10 p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                    <X size={24} className="text-gray-600" />
                </button>

                {bookingSuccess ? (
                    <div className="p-12 text-center">
                        <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6">
                            <Check size={48} className="text-green-600" />
                        </div>
                        <h2 className="text-3xl font-bold text-gray-800 mb-4">訂票成功！</h2>
                        <p className="text-gray-600 mb-2">已成功預訂 {selectedSeats.length} 個座位</p>
                        <p className="text-sm text-gray-500">座位: {selectedSeats.sort().join(', ')}</p>
                        <p className="text-2xl font-bold text-blue-600 mt-6">NT${totalPrice}</p>
                        <p className="text-sm text-gray-500 mt-8">視窗將自動關閉...</p>
                    </div>
                ) : (
                    <>
                        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
                            <h2 className="text-2xl font-bold mb-4">{showtime.movie_title_cn}</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                                <div className="flex items-center gap-2">
                                    <MapPin size={18} />
                                    <div>
                                        <p className="text-blue-100 text-xs">影城</p>
                                        <p className="font-semibold">{showtime.cinema_name}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Calendar size={18} />
                                    <div>
                                        <p className="text-blue-100 text-xs">日期</p>
                                        <p className="font-semibold">{showtime.date}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Clock size={18} />
                                    <div>
                                        <p className="text-blue-100 text-xs">時間</p>
                                        <p className="font-semibold text-lg">{showtime.show_time || showtime.time}</p>
                                    </div>
                                </div>
                                {showtime.screen_number && (
                                    <div className="flex items-center gap-2">
                                        <Film size={18} />
                                        <div>
                                            <p className="text-blue-100 text-xs">廳別</p>
                                            <p className="font-semibold">{showtime.screen_number}</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                            {seatData?.stats && (
                                <div className="mt-4 pt-4 border-t border-white border-opacity-20">
                                    <div className="flex gap-6 text-sm">
                                        <div>
                                            <span className="text-blue-100">總: </span>
                                            <span className="font-semibold">{seatData.stats.total}</span>
                                        </div>
                                        <div>
                                            <span className="text-blue-100">可售: </span>
                                            <span className="font-semibold text-green-300">{seatData.stats.available}</span>
                                        </div>
                                        <div>
                                            <span className="text-blue-100">已售: </span>
                                            <span className="font-semibold text-red-300">{seatData.stats.sold}</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="p-6">
                            <div className="mb-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-xl font-bold flex items-center gap-2">
                                        <Users size={24} className="text-blue-600" />
                                        選擇座位
                                        {seatData?.has_real_data === false && (
                                            <span className="text-sm font-normal text-orange-600 bg-orange-100 px-2 py-1 rounded">
                                                模擬資料
                                            </span>
                                        )}
                                        {seatData?.from_cache && (
                                            <span className="text-sm font-normal text-green-600 bg-green-100 px-2 py-1 rounded">
                                                快取
                                            </span>
                                        )}
                                    </h3>
                                    <button
                                        onClick={loadSeats}
                                        disabled={loading}
                                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50"
                                    >
                                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                                        刷新
                                    </button>
                                </div>

                                {loading ? (
                                    <div className="text-center py-12">
                                        <div className="inline-block animate-spin">
                                            <div className="border-4 border-gray-200 border-t-blue-600 rounded-full w-8 h-8"></div>
                                        </div>
                                        <p className="mt-4 text-gray-500">載入座位圖中...</p>
                                        {showtime.chain === 'showtime' && (
                                            <p className="text-xs text-gray-400 mt-2">秀泰座位查詢需要 8-12 秒</p>
                                        )}
                                    </div>
                                ) : error ? (
                                    <div className="text-center py-12 bg-red-50 rounded-lg">
                                        <AlertCircle size={48} className="mx-auto text-red-500 mb-4" />
                                        <p className="text-red-600">{error}</p>
                                        <button onClick={loadSeats} className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg">重試</button>
                                    </div>
                                ) : seatData?.seats && seatData.seats.length > 0 ? (
                                    <>
                                        <div className="text-center mb-6">
                                            <div className="inline-block w-full max-w-3xl border-b-8 border-gray-400 rounded-b-3xl pb-2 bg-gradient-to-b from-gray-200 to-gray-300">
                                                <p className="text-gray-600 font-semibold text-sm">銀幕</p>
                                            </div>
                                        </div>

                                        {/* ✅ 秀泰：絕對定位 */}
                                        {showtime.chain === 'showtime' ? (
                                            <div className="relative mx-auto mb-6" style={{
                                                width: '700px',
                                                height: '500px',
                                                overflow: 'auto'
                                            }}>
                                                {/* ✅ 座位 */}
                                                {seatRows.map((seat, idx) => {
                                                    const seatId = seat.seat_id || `${seat.row}-${seat.seat_number}`;
                                                    const isSelected = selectedSeats.includes(seatId);
                                                    const isSold = seat.status === 'sold';
                                                    
                                                    // ✅ 使用原始座標
                                                    const left = seat.position?.left || 0;
                                                    const top = seat.position?.top || 0;
                                                    
                                                    return (
                                                        <button
                                                            key={seatId}
                                                            onClick={() => toggleSeatSelection(seat)}
                                                            disabled={isSold}
                                                            className={`absolute rounded text-[10px] font-bold transition-all ${
                                                                isSold
                                                                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                                                    : isSelected
                                                                        ? 'bg-blue-600 text-white scale-110 shadow-lg'
                                                                        : 'bg-green-400 text-white hover:scale-110 hover:bg-green-500'
                                                            }`}
                                                            style={{
                                                                left: `${left}px`,
                                                                top: `${top}px`,
                                                                width: '24px',
                                                                height: '24px'
                                                            }}
                                                            title={`${seat.row}排 ${seat.seat_number}號 - ${isSold ? '已售' : '可選'}`}
                                                        >
                                                            {seat.seat_number}
                                                        </button>
                                                    );
                                                })}
                                                
                                                {/* ✅ 排號標籤（左側） */}
                                                {Array.from(new Set(seatRows.map(s => s.row))).map(row => {
                                                    // 找到這一排的座位
                                                    const rowSeats = seatRows.filter(s => s.row === row);
                                                    if (rowSeats.length === 0) return null;
                                                    
                                                    // 使用第一個座位的 top 座標
                                                    const top = rowSeats[0].position?.top || 0;
                                                    
                                                    return (
                                                        <div
                                                            key={`row-label-${row}`}
                                                            className="absolute text-sm font-bold text-gray-600"
                                                            style={{
                                                                left: '5px',
                                                                top: `${top}px`,
                                                                width: '20px',
                                                                height: '24px',
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center'
                                                            }}
                                                        >
                                                            {row}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        ) : (
                                            /* ✅ 威秀：原來的排列方式 */
                                            <div className="space-y-2 max-h-96 overflow-y-auto pb-4">
                                                {seatRows.map(([rowKey, seats], rowIndex) => {
                                                    // ✅ 檢查是否是橫向走道
                                                    const isHorizontalAisle = seats.length === 1 && seats[0].type === 'horizontal_aisle';
                                                    
                                                    if (isHorizontalAisle) {
                                                        // ✅ 橫向走道：顯示空白區域（高度 24px）
                                                        return (
                                                            <div 
                                                                key={rowKey} 
                                                                style={{ height: '24px' }}
                                                            ></div>
                                                        );
                                                    }
                                                    
                                                    // ✅ 一般排：顯示座位
                                                    return (
                                                        <div key={rowKey} className="flex items-center gap-2 justify-center">
                                                            <div className="w-8 text-center font-bold text-gray-600">
                                                                {rowKey}
                                                            </div>
                                                            
                                                            <div className="flex gap-1 justify-center">
                                                                {seats.map((seat, idx) => {
                                                                    const seatId = seat.seat_id || `${seat.row}-${seat.seat_number}`;
                                                                    const isSelected = selectedSeats.includes(seatId);
                                                                    const isSold = seat.status === 'sold';
                                                                    const displayNumber = seat.seat_number || seat.number;
                                                                    const seatType = seat.type || 'seat';
                                                                    
                                                                    // ✅ 縱向走道
                                                                    if (seatType === 'empty') {
                                                                        return (
                                                                            <div
                                                                                key={seatId}
                                                                                style={{
                                                                                    width: '24px',
                                                                                    height: '24px'
                                                                                }}
                                                                            ></div>
                                                                        );
                                                                    }
                                                                    
                                                                    // ✅ 輪椅位
                                                                    if (seatType === 'wheelchair') {
                                                                        return (
                                                                            <div
                                                                                key={seatId}
                                                                                className="rounded bg-purple-400 text-white text-[10px] font-bold flex items-center justify-center"
                                                                                style={{
                                                                                    width: '24px',
                                                                                    height: '24px'
                                                                                }}
                                                                                title="輪椅位（需至影城購買）"
                                                                            >
                                                                                ♿
                                                                            </div>
                                                                        );
                                                                    }
                                                                    
                                                                    // ✅ 一般座位
                                                                    return (
                                                                        <button
                                                                            key={seatId}
                                                                            onClick={() => toggleSeatSelection(seat)}
                                                                            disabled={isSold}
                                                                            className={`rounded text-[10px] font-bold transition-all ${
                                                                                isSold
                                                                                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                                                                    : isSelected
                                                                                        ? 'bg-blue-600 text-white scale-110 shadow-lg'
                                                                                        : 'bg-green-400 text-white hover:scale-110 hover:bg-green-500'
                                                                            }`}
                                                                            style={{
                                                                                width: '24px',
                                                                                height: '24px'
                                                                            }}
                                                                            title={`${seat.row}排 ${displayNumber}號 - ${isSold ? '已售' : '可選'}`}
                                                                        >
                                                                            {displayNumber}
                                                                        </button>
                                                                    );
                                                                })}
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        )}

                                        <div className="flex justify-center gap-6 text-sm mt-6 pb-6 border-b">
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 bg-green-400 rounded"></div>
                                                <span>可選</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 bg-blue-600 rounded"></div>
                                                <span>已選</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 bg-gray-300 rounded"></div>
                                                <span>已售</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 bg-purple-400 rounded text-white flex items-center justify-center text-xs">♿</div>
                                                <span>輪椅位</span>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <p className="text-center text-gray-500 py-8">無座位資訊</p>
                                )}
                            </div>

                            <div className="bg-gray-50 rounded-lg p-6">
                                <h4 className="font-bold text-lg mb-4">訂票摘要</h4>
                                <div className="space-y-3 mb-6">
                                    <div className="flex justify-between">
                                        <span>已選座位:</span>
                                        <span className="font-semibold">
                                            {selectedSeats.length > 0 ? selectedSeats.sort().join(', ') : '未選擇'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>座位數:</span>
                                        <span className="font-semibold">{selectedSeats.length} 張</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>單價:</span>
                                        <span className="font-semibold">NT${ticketPrice}</span>
                                    </div>
                                    <div className="flex justify-between text-lg border-t pt-3">
                                        <span className="font-bold">總金額:</span>
                                        <span className="text-2xl font-bold text-blue-600">NT${totalPrice}</span>
                                    </div>
                                </div>
                                <button
                                    onClick={handleBooking}
                                    disabled={selectedSeats.length === 0 || bookingLoading}
                                    className={`w-full py-4 rounded-lg font-bold text-white text-lg ${
                                        selectedSeats.length === 0 || bookingLoading
                                            ? 'bg-gray-400 cursor-not-allowed'
                                            : 'bg-blue-600 hover:bg-blue-700'
                                    }`}
                                >
                                    {bookingLoading ? '處理中...' : '確認訂票'}
                                </button>
                                <p className="text-xs text-gray-500 text-center mt-4">* 此為示範系統，不會實際扣款</p>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}