import { useEffect, useState } from "react";
import { getHome } from "../../api/action/userGymDay.api";
import { BsPeople } from "react-icons/bs";
import { FaMoneyBillWave } from "react-icons/fa";
import { HiOutlineExclamationCircle } from "react-icons/hi";


const MetricsSection = () => {
    const [stats, setStats] = useState({
        num_miembros: 0,
        total_month: 0,
        miembros_mes: 0,
        total: 0,
        por_cobrar: 0,
        al_dia: 0,
        con_deuda: 0,
    });

    useEffect(() => {
        const loadStats = async () => {
            try {
                const data = await getHome();
                setStats(data);
            } catch (error) {
                console.error("Error al cargar estadísticas:", error);
            }
        };
        loadStats();
    }, []);
    //Función para dar formato a la moneda en este caso pesos colombianos
    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount);
    };
    //Array de objetos con las estadísticas
    const cards = [
        {
            value: stats.num_miembros,
            subtitle: "Total de miembros",
            change: "+6.2%",
            progress: 75,
            icon: <BsPeople size={24} className="text-text-primary" />,
            bgIcon: "bg-primary/7",
            color: "bg-blue-400",
        },
        {
            value: stats.miembros_mes,
            subtitle: "Registrados este mes",
            change: "+4.2%",
            progress: 35,
            icon: <BsPeople size={24} className="text-purple-500" />,
            bgIcon: "bg-purple-500/5",
            color: "bg-purple-400",
        },
        {
            value: formatCurrency(stats.total),
            subtitle: "Dinero Total",
            change: "+7.2%",
            progress: 55,
            icon: <FaMoneyBillWave size={24} className="text-green-500" />,
            bgIcon: "bg-green-500/5",
            color: "bg-green-400",
        },
        {
            value: formatCurrency(stats.total_month),
            subtitle: "Dinero del mes",
            change: "+5.2%",
            progress: 85,
            icon: <FaMoneyBillWave size={24} className="text-tertiary" />,
            bgIcon: "bg-tertiary/5",
            color: "bg-tertiary",
        },
    ];


    return (
        <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                {cards.map((card, index) => (
                    <div
                        key={index}
                        className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm hover:shadow-md transition"
                    >
                        {/* Header */}
                        <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-lg ${card.bgIcon}`}>
                                {card.icon}
                            </div>

                            {card.change && (
                                <span className="text-xs font-semibold text-green-600 bg-green-100 px-2 py-1 rounded-full">
                                    {card.change}
                                </span>
                            )}
                        </div>
                        {/* Subtitle */}
                        <p className="font-bold mb-1 text-sm tracking-widest text-on-surface uppercase">
                            {card.subtitle}
                        </p>
                        {/* Value */}
                        <h2 className="text-3xl font-black text-on-surface tracking-tighter">
                            {card.value}
                        </h2>
                        {/* Progress bar */}
                        {card.progress != null && card.progress > 0 && (
                            <div className="mt-4">
                                <div className="w-full h-1 bg-slate-100 mt-4 overflow-hidden rounded-full">
                                    <div
                                        className={`h-full rounded-full ${card.color} transition-all w-[85%]`}
                                        style={{ width: `${card.progress}%` }}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Resumen de Cobranza - formato compacto tipo tabla */}
            <div className="bg-white border border-gray-200 mt-4 p-5 rounded-xl shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                    <HiOutlineExclamationCircle size={20} className="text-orange-500" />
                    <h3 className="font-bold text-sm tracking-widest text-on-surface uppercase">
                        Resumen de Cobranza
                    </h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center gap-3 p-3 bg-orange-50 rounded-lg">
                        <div className="p-2 bg-orange-100 rounded-lg">
                            <FaMoneyBillWave size={18} className="text-orange-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">Por Cobrar</p>
                            <p className="text-lg font-bold text-gray-900">{formatCurrency(stats.por_cobrar)}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                        <div className="p-2 bg-green-100 rounded-lg">
                            <BsPeople size={18} className="text-green-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">Al Día</p>
                            <p className="text-lg font-bold text-gray-900">{stats.al_dia} miembros</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                        <div className="p-2 bg-red-100 rounded-lg">
                            <HiOutlineExclamationCircle size={18} className="text-red-600" />
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">Con Deuda</p>
                            <p className="text-lg font-bold text-gray-900">{stats.con_deuda} miembros</p>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};
export default MetricsSection;