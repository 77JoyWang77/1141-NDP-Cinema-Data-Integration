import React, { useState, useEffect } from 'react';
import api from '../api';
import CinemaDetail from './CinemaDetail';
import { MapPin, Phone, Film, ChevronLeft } from 'lucide-react';

export default function CinemaList() {
    const [cinemas, setCinemas] = useState([]);
    const [selectedCinema, setSelectedCinema] = useState(null);
    const [loading, setLoading] = useState(false);
    const [filterChain, setFilterChain] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        loadCinemas();
    }, [filterChain]);

    const loadCinemas = async () => {
        setLoading(true);
        try {
            const chainParam = filterChain !== 'all' ? filterChain : null;
            const results = await api.getCinemas(chainParam);
            setCinemas(results);
        } catch (error) {
            console.error('載入影城失敗:', error);
        } finally {
            setLoading(false);
        }
    };

    // 如果選擇了影城，顯示詳情頁
    if (selectedCinema) {
        return (
            <div className="container mx-auto px-4 py-6">
                <button
                    onClick={() => setSelectedCinema(null)}
                    className="flex items-center gap-2 mb-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                    <ChevronLeft size={20} />
                    返回影城列表
                </button>
                <CinemaDetail cinema={selectedCinema} />
            </div>
        );
    }

    // 過濾影城
    const filteredCinemas = cinemas.filter(cinema => 
        cinema.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (cinema.address && cinema.address.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="container mx-auto px-4 py-6">
            {/* 標題和篩選 */}
            <div className="mb-6">
                <h2 className="text-3xl font-bold mb-4">選擇影城</h2>
                
                <div className="flex flex-col md:flex-row gap-4">
                    {/* 搜尋框 */}
                    <input
                        type="text"
                        placeholder="搜尋影城名稱..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />

                    {/* 影城鏈篩選 */}
                    <select
                        value={filterChain}
                        onChange={(e) => setFilterChain(e.target.value)}
                        className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="all">所有類型</option>
                        <option value="showtime">秀泰影城</option>
                        <option value="vieshow">威秀影城</option>
                    </select>
                </div>

                <p className="text-gray-500 text-sm mt-2">
                    共 {filteredCinemas.length} 家影城
                </p>
            </div>

            {/* 影城列表 */}
            {loading ? (
                <div className="text-center py-12">
                    <div className="inline-block animate-spin">
                        <div className="border-4 border-gray-200 border-t-blue-600 rounded-full w-8 h-8"></div>
                    </div>
                    <p className="mt-4 text-gray-500">載入中...</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {filteredCinemas.map(cinema => (
                        <div
                            key={cinema._id}
                            onClick={() => setSelectedCinema(cinema)}
                            className="bg-white rounded-lg shadow-lg hover:shadow-xl transition-all cursor-pointer overflow-hidden border hover:border-blue-500"
                        >
                            {/* ✅ 影城卡片頭部 - 移除按鈕 */}
                            <div className={`p-4 text-white ${
                                cinema.chain === 'showtime' 
                                    ? 'bg-gradient-to-r from-blue-600 to-blue-500'
                                    : 'bg-gradient-to-r from-purple-600 to-purple-500'
                            }`}>
                                <div className="flex items-center gap-2 mb-2">
                                    <Film size={20} />
                                    <h3 className="font-bold text-lg">{cinema.name}</h3>
                                </div>
                                {cinema.chain_name && (
                                    <span className="text-xs bg-white bg-opacity-20 px-2 py-1 rounded">
                                        {cinema.chain_name}
                                    </span>
                                )}
                            </div>

                            {/* ✅ 卡片內容 - 移除按鈕 */}
                            <div className="p-4">
                                {/* 地址 */}
                                {cinema.address && (
                                    <div className="flex items-start gap-2 text-sm text-gray-600 mb-2">
                                        <MapPin size={16} className="text-red-500 mt-0.5 flex-shrink-0" />
                                        <span className="line-clamp-2">{cinema.address}</span>
                                    </div>
                                )}

                                {/* 電話 */}
                                {cinema.phone && (
                                    <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
                                        <Phone size={16} className="text-green-500" />
                                        <span>{cinema.phone}</span>
                                    </div>
                                )}

                                {/* 廳數 */}
                                {cinema.screen_count && (
                                    <div className="flex items-center gap-2 text-sm text-gray-600">
                                        <Film size={16} className="text-purple-500" />
                                        <span>{cinema.screen_count} 廳</span>
                                    </div>
                                )}

                                {/* ✅ 完全移除「查看場次」按鈕 - 只保留點擊卡片 */}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* 無結果提示 */}
            {!loading && filteredCinemas.length === 0 && (
                <div className="text-center py-12">
                    <p className="text-gray-500 text-lg">沒有找到符合條件的影城</p>
                    <button
                        onClick={() => {
                            setSearchQuery('');
                            setFilterChain('all');
                        }}
                        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        清除篩選
                    </button>
                </div>
            )}
        </div>
    );
}