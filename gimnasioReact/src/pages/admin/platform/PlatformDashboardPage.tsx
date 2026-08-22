import { useEffect, useState } from "react";
import { getPlatformStats } from "../../../api/action/platform.api";
import type { PlatformStats } from "../../../model/dto/platform.dto";
import { BsBuilding, BsPeople, BsCurrencyDollar, BsPersonCheck, BsExclamationTriangle } from "react-icons/bs";

const PlatformDashboardPage = () => {
    const [stats, setStats] = useState<PlatformStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadStats = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await getPlatformStats();
                setStats(data);
            } catch {
                setError("Error al cargar las estadísticas de la plataforma");
            } finally {
                setLoading(false);
            }
        };
        loadStats();
    }, []);

    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount);
    };

    const formatNumber = (num: number): string => {
        return new Intl.NumberFormat("es-CO").format(num);
    };

    if (loading) {
        return <div className="text-center py-12 text-on-surface/60">Cargando estadísticas...</div>;
    }

    if (error || !stats) {
        return <div className="text-center py-12 text-red-600">{error ?? "No se pudieron cargar las estadísticas"}</div>;
    }

    const cards = [
        {
            value: stats.total_gimnasios,
            subtitle: "Gimnasios Totales",
            icon: <BsBuilding size={24} className="text-primary" />,
            bgIcon: "bg-primary/7",
            color: "bg-blue-400",
            progress: stats.total_gimnasios > 0 ? (stats.gimnasios_activos / stats.total_gimnasios) * 100 : 0,
        },
        {
            value: stats.gimnasios_activos,
            subtitle: "Gimnasios Activos",
            icon: <BsBuilding size={24} className="text-green-500" />,
            bgIcon: "bg-green-500/5",
            color: "bg-green-400",
            progress: stats.total_gimnasios > 0 ? (stats.gimnasios_activos / stats.total_gimnasios) * 100 : 0,
        },
        {
            value: stats.total_usuarios_staff,
            subtitle: "Usuarios Staff",
            icon: <BsPeople size={24} className="text-purple-500" />,
            bgIcon: "bg-purple-500/5",
            color: "bg-purple-400",
            progress: 0,
        },
        {
            value: stats.demo_pendientes,
            subtitle: "Demos Pendientes",
            icon: <BsExclamationTriangle size={24} className="text-orange-500" />,
            bgIcon: "bg-orange-500/5",
            color: "bg-orange-400",
            progress: 0,
        },
    ];

    return (
        <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
                {cards.map((card, index) => (
                    <div key={index} className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm hover:shadow-md transition">
                        <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-lg ${card.bgIcon}`}>
                                {card.icon}
                            </div>
                        </div>
                        <p className="font-bold mb-1 text-sm tracking-widest text-on-surface uppercase">
                            {card.subtitle}
                        </p>
                        <h2 className="text-3xl font-black text-on-surface tracking-tighter">
                            {card.value}
                        </h2>
                        {card.progress > 0 && (
                            <div className="mt-4">
                                <div className="w-full h-1 bg-slate-100 mt-4 overflow-hidden rounded-full">
                                    <div
                                        className={`h-full rounded-full ${card.color} transition-all`}
                                        style={{ width: `${Math.min(card.progress, 100)}%` }}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Resumen Global */}
            <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm mb-8">
                <h3 className="font-bold text-sm tracking-widest text-on-surface uppercase mb-4 flex items-center gap-2">
                    <BsCurrencyDollar size={20} className="text-green-500" />
                    Resumen Global del Mes
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                        <div className="p-2 bg-green-100 rounded-lg">
                            <BsCurrencyDollar size={18} className="text-green-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">Ingresos Mes Global</p>
                            <p className="text-lg font-bold text-gray-900">{formatCurrency(Number(stats.ingresos_mes_global))}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                        <div className="p-2 bg-blue-100 rounded-lg">
                            <BsPersonCheck size={18} className="text-blue-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">Miembros Activos Global</p>
                            <p className="text-lg font-bold text-gray-900">{formatNumber(stats.miembros_activos_global)}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                        <div className="p-2 bg-purple-100 rounded-lg">
                            <BsPeople size={18} className="text-purple-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">Retención Promedio</p>
                            <p className="text-lg font-bold text-gray-900">{Number(stats.retencion_promedio).toFixed(1)}%</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Estado de Demos */}
            <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm">
                <h3 className="font-bold text-sm tracking-widest text-on-surface uppercase mb-4 flex items-center gap-2">
                    <BsExclamationTriangle size={20} className="text-orange-500" />
                    Estado de Solicitudes Demo
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center gap-3 p-3 bg-orange-50 rounded-lg">
                        <div className="p-2 bg-orange-100 rounded-lg">
                            <BsExclamationTriangle size={18} className="text-orange-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">Pendientes</p>
                            <p className="text-lg font-bold text-gray-900">{stats.demo_pendientes}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                        <div className="p-2 bg-green-100 rounded-lg">
                            <BsPersonCheck size={18} className="text-green-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">Contactados</p>
                            <p className="text-lg font-bold text-gray-900">{stats.demo_contactados}</p>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};
export default PlatformDashboardPage;