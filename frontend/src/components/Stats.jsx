import React, { useState, useEffect } from 'react';
import api from '../api';
import { Film, MapPin, Ticket, ShoppingCart, TrendingUp, Database } from 'lucide-react';

function Stats() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const data = await api.getStats();
            setStats(data);
        } catch (error) {
            console.error('載入統計失敗:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-6">
                <div className="text-center py-12">
                    <div className="inline-block animate-spin">
                        <div className="border-4 border-gray-200 border-t-blue-600 rounded-full w-12 h-12"></div>
                    </div>
                    <p className="mt-4 text-gray-500">載入統計中...</p>
                </div>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="container mx-auto px-4 py-6">
                <p className="text-center text-red-500">載入統計失敗</p>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-6 space-y-6">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold flex items-center gap-2">
                    <TrendingUp size={32} className="text-blue-600" />
                    系統統計
                </h2>
                <button
                    onClick={loadStats}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
                >
                    刷新數據
                </button>
            </div>

            {/* 總覽卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* 影城總數 */}
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <p className="text-blue-100 text-sm mb-1">影城總數</p>
                            <p className="text-4xl font-bold">{stats.cinemas.total}</p>
                        </div>
                        <div className="p-3 bg-white bg-opacity-20 rounded-full">
                            <MapPin size={32} />
                        </div>
                    </div>
                    <div className="text-sm text-blue-100">
                        秀泰 {stats.cinemas.showtime} | 威秀 {stats.cinemas.vieshow}
                    </div>
                </div>

                {/* 電影總數 */}
                <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <p className="text-purple-100 text-sm mb-1">電影總數</p>
                            <p className="text-4xl font-bold">{stats.movies.total}</p>
                        </div>
                        <div className="p-3 bg-white bg-opacity-20 rounded-full">
                            <Film size={32} />
                        </div>
                    </div>
                    <div className="text-sm text-purple-100">
                        兩邊都有 {stats.movies.both} 部
                    </div>
                </div>

                {/* 場次總數 */}
                <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg p-6 text-white">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <p className="text-green-100 text-sm mb-1">放映場次</p>
                            <p className="text-4xl font-bold">{stats.showtimes.total.toLocaleString()}</p>
                        </div>
                        <div className="p-3 bg-white bg-opacity-20 rounded-full">
                            <Ticket size={32} />
                        </div>
                    </div>
                    <div className="text-sm text-green-100">
                        秀泰 {stats.showtimes.showtime.toLocaleString()} | 威秀 {stats.showtimes.vieshow.toLocaleString()}
                    </div>
                </div>

                {/* 訂票記錄 */}
                <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <p className="text-orange-100 text-sm mb-1">訂票記錄</p>
                            <p className="text-4xl font-bold">{stats.bookings}</p>
                        </div>
                        <div className="p-3 bg-white bg-opacity-20 rounded-full">
                            <ShoppingCart size={32} />
                        </div>
                    </div>
                </div>
            </div>

            {/* 詳細統計 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 影城詳細 */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <MapPin className="text-blue-600" />
                        影城分布
                    </h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                            <span className="font-semibold">秀泰影城</span>
                            <span className="text-2xl font-bold text-blue-600">
                                {stats.cinemas.showtime}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                            <span className="font-semibold">威秀影城</span>
                            <span className="text-2xl font-bold text-purple-600">
                                {stats.cinemas.vieshow}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border-2 border-gray-200">
                            <span className="font-semibold">總計</span>
                            <span className="text-2xl font-bold text-gray-700">
                                {stats.cinemas.total}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 電影詳細 */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <Film className="text-purple-600" />
                        電影統計
                    </h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                            <span className="font-semibold">兩邊都有</span>
                            <span className="text-2xl font-bold text-green-600">
                                {stats.movies.both}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                            <span className="font-semibold">僅秀泰</span>
                            <span className="text-2xl font-bold text-blue-600">
                                {stats.movies.showtime_only}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                            <span className="font-semibold">僅威秀</span>
                            <span className="text-2xl font-bold text-purple-600">
                                {stats.movies.vieshow_only}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border-2 border-gray-200">
                            <span className="font-semibold">總計</span>
                            <span className="text-2xl font-bold text-gray-700">
                                {stats.movies.total}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 場次詳細 */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <Ticket className="text-green-600" />
                        場次統計
                    </h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                            <span className="font-semibold">秀泰場次</span>
                            <span className="text-2xl font-bold text-blue-600">
                                {stats.showtimes.showtime.toLocaleString()}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                            <span className="font-semibold">威秀場次</span>
                            <span className="text-2xl font-bold text-purple-600">
                                {stats.showtimes.vieshow.toLocaleString()}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border-2 border-gray-200">
                            <span className="font-semibold">總計</span>
                            <span className="text-2xl font-bold text-gray-700">
                                {stats.showtimes.total.toLocaleString()}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 系統資訊 */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <Database className="text-gray-600" />
                        系統資訊
                    </h3>
                    <div className="space-y-3">
                        <div className="p-3 bg-gray-50 rounded-lg">
                            <p className="text-sm text-gray-600 mb-1">最後更新</p>
                            <p className="font-mono text-sm">
                                {new Date(stats.timestamp).toLocaleString('zh-TW', {
                                    year: 'numeric',
                                    month: '2-digit',
                                    day: '2-digit',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    second: '2-digit'
                                })}
                            </p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded-lg">
                            <p className="text-sm text-gray-600 mb-1">資料庫</p>
                            <p className="font-semibold">MongoDB</p>
                        </div>
                        <div className="p-3 bg-gray-50 rounded-lg">
                            <p className="text-sm text-gray-600 mb-1">API 版本</p>
                            <p className="font-semibold">v1.0.0</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Stats;