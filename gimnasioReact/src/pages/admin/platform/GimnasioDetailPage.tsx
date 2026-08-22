import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getGimnasioDetail } from "../../../api/action/platform.api";
import type { GimnasioPlatformDetail } from "../../../model/dto/platform.dto";
import { BsBuilding, BsPeople, BsPerson, BsCalendar, BsCreditCard, BsArrowLeft, BsTelephone } from "react-icons/bs";
import { Link } from "react-router-dom";

const formatCurrency = (amount: number): string => new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount);
const formatNumber = (num: number): string => new Intl.NumberFormat("es-CO").format(num);

const formatDate = (dateStr: string): string => {
    const d = new Date(dateStr);
    return d.toLocaleDateString("es-CO", { year: "numeric", month: "short", day: "numeric" });
};

const formatDateTime = (dateStr: string): string => {
    const d = new Date(dateStr);
    return d.toLocaleString("es-CO", { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
};

const GimnasioDetailPage = () => {
    const { id } = useParams<{ id: string }>();

    const [data, setData] = useState<GimnasioPlatformDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        const gimnasioId = parseInt(id, 10);
        const loadDetail = async () => {
            setLoading(true);
            setError(null);
            try {
                const result = await getGimnasioDetail(gimnasioId);
                setData(result);
            } catch {
                setError("Error al cargar el detalle del gimnasio");
            } finally {
                setLoading(false);
            }
        };
        loadDetail();
    }, [id]);

    if (loading) {
        return <div className="text-center py-12 text-on-surface/60">Cargando detalle...</div>;
    }

    if (error || !data) {
        return <div className="text-center py-12 text-red-600">{error ?? "No se pudo cargar el detalle"}</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <Link to="/platform/gimnasios" className="flex items-center gap-2 text-primary hover:underline">
                    <BsArrowLeft size={20} /> Volver
                </Link>
                <h2 className="text-2xl font-bold text-on-surface">{data.name}</h2>
            </div>

            {/* Info básica */}
            <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="p-2 bg-primary/10 rounded-lg"><BsBuilding size={20} className="text-primary" /></div>
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider">Dirección</p>
                        <p className="font-medium">{data.address ?? "-"}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="p-2 bg-green-100 rounded-lg"><BsTelephone size={20} className="text-green-600" /></div>
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider">Teléfono</p>
                        <p className="font-medium">{data.phone ?? "-"}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="p-2 bg-purple-100 rounded-lg"><BsCalendar size={20} className="text-purple-600" /></div>
                    <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wider">Creado</p>
                        <p className="font-medium">{formatDate(data.created_at)}</p>
                    </div>
                </div>
            </div>

            {/* Stats rápidas */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-green-100 rounded-lg"><BsPeople size={24} className="text-green-600" /></div>
                        <div>
                            <p className="text-sm text-gray-500">Miembros Activos</p>
                            <p className="text-2xl font-bold">{formatNumber(data.miembros_activos_count)}</p>
                        </div>
                    </div>
                </div>
                <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-purple-100 rounded-lg"><BsCreditCard size={24} className="text-purple-600" /></div>
                        <div>
                            <p className="text-sm text-gray-500">Ingresos Mes</p>
                            <p className="text-2xl font-bold">{formatCurrency(Number(data.ingresos_mes))}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Usuarios del gimnasio */}
            <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm">
                <h3 className="font-bold text-sm tracking-widest text-on-surface uppercase mb-4 flex items-center gap-2">
                    <BsPeople size={20} className="text-primary" />
                    Usuarios del Gimnasio ({data.usuarios?.length ?? 0})
                </h3>
                {data.usuarios && data.usuarios.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-200">
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Nombre</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Email</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Rol</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Estado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.usuarios.map((u) => (
                                    <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                                        <td className="py-2 px-3">{u.name} {u.lastname}</td>
                                        <td className="py-2 px-3">{u.email}</td>
                                        <td className="py-2 px-3 capitalize">{u.roles}</td>
                                        <td className="py-2 px-3">
                                            <span className={`px-2 py-1 rounded-full text-xs ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                                {u.is_active ? 'Activo' : 'Inactivo'}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-gray-500 text-center py-4">Sin usuarios asignados</p>
                )}
            </div>

            {/* Miembros activos */}
            <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm">
                <h3 className="font-bold text-sm tracking-widest text-on-surface uppercase mb-4 flex items-center gap-2">
                    <BsPerson size={20} className="text-green-500" />
                    Miembros Activos ({data.miembros_activos?.length ?? 0})
                </h3>
                {data.miembros_activos && data.miembros_activos.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-200">
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Miembro</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Membresía</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Fecha Fin</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Saldo Pendiente</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.miembros_activos.map((m) => (
                                    <tr key={m.id} className="border-b border-gray-100 hover:bg-gray-50">
                                        <td className="py-2 px-3">{m.name} {m.lastname}</td>
                                        <td className="py-2 px-3">{m.membresia}</td>
                                        <td className="py-2 px-3">{formatDate(m.dateFinal)}</td>
                                        <td className="py-2 px-3 font-mono">
                                            {Number(m.saldo_pendiente) > 0
                                                ? <span className="text-red-600">{formatCurrency(Number(m.saldo_pendiente))}</span>
                                                : <span className="text-green-600">Al día</span>}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-gray-500 text-center py-4">Sin miembros activos</p>
                )}
            </div>

            {/* Últimos pagos */}
            <div className="bg-white border border-gray-200 p-5 rounded-xl shadow-sm">
                <h3 className="font-bold text-sm tracking-widest text-on-surface uppercase mb-4 flex items-center gap-2">
                    <BsCreditCard size={20} className="text-purple-500" />
                    Últimos Pagos ({data.ultimos_pagos?.length ?? 0})
                </h3>
                {data.ultimos_pagos && data.ultimos_pagos.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-200">
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Fecha</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Miembro</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Membresía</th>
                                    <th className="text-left py-2 px-3 font-semibold text-gray-500">Método</th>
                                    <th className="text-right py-2 px-3 font-semibold text-gray-500">Monto</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.ultimos_pagos.map((p) => (
                                    <tr key={p.id} className="border-b border-gray-100 hover:bg-gray-50">
                                        <td className="py-2 px-3">{formatDateTime(p.fecha_pago)}</td>
                                        <td className="py-2 px-3">{p.miembro_name} {p.miembro_lastname}</td>
                                        <td className="py-2 px-3">{p.membresia_name}</td>
                                        <td className="py-2 px-3 capitalize">{p.metodo_pago}</td>
                                        <td className="py-2 px-3 font-mono text-right">{formatCurrency(Number(p.monto))}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-gray-500 text-center py-4">Sin pagos recientes</p>
                )}
            </div>
        </div>
    );
};

export default GimnasioDetailPage;