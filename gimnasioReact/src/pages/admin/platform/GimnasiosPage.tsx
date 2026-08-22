import { useEffect, useState, useRef, type ChangeEvent } from "react";
import { getGimnasios, toggleGimnasioActive } from "../../../api/action/platform.api";
import type { GimnasioPlatform } from "../../../model/dto/platform.dto";
import Table from "../../../components/Table";
import { ColumnDef } from "@tanstack/react-table";
import { RiToggleLine, RiToggleFill } from "react-icons/ri";
import { IoSearch } from "react-icons/io5";

const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
};

interface GimnasiosPageData extends GimnasioPlatform {
    ingresos_mes_formatted: string;
    estado_badge: string;
}

const GimnasiosPage = () => {
    const [data, setData] = useState<GimnasiosPageData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [togglingId, setTogglingId] = useState<number | null>(null);
    const [search, setSearch] = useState("");
    const searchTimeout = useRef<number | null>(null);

    const fetchGimnasios = async (pageNum: number = 1, searchTerm: string = "") => {
        setLoading(true);
        setError(null);
        try {
            const response = await getGimnasios(pageNum, searchTerm);
            setData(response.results.map(g => ({
                ...g,
                ingresos_mes_formatted: formatCurrency(Number(g.ingresos_mes)),
                estado_badge: g.is_active ? 'Activo' : 'Inactivo',
            })));
            setTotalCount(response.count);
        } catch {
            setError("Error al cargar los gimnasios");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchGimnasios(page);
        return () => {
            if (searchTimeout.current) clearTimeout(searchTimeout.current);
        };
    }, [page]);

    const handleSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
        const searchValue = e.target.value.toLowerCase();
        setSearch(searchValue);

        if (searchTimeout.current) clearTimeout(searchTimeout.current);

        searchTimeout.current = window.setTimeout(() => {
            setPage(1);
            fetchGimnasios(1, searchValue);
        }, 500);
    };

    const columns: ColumnDef<GimnasiosPageData>[] = [
        {
            accessorKey: "name",
            header: "Nombre",
            cell: ({ row }) => <span className="font-semibold">{row.getValue("name")}</span>,
        },
        {
            accessorKey: "address",
            header: "Dirección",
            cell: ({ row }) => <span>{row.getValue("address") ?? "-"}</span>,
        },
        {
            accessorKey: "phone",
            header: "Teléfono",
            cell: ({ row }) => <span>{row.getValue("phone") ?? "-"}</span>,
        },
        {
            accessorKey: "estado_badge",
            header: "Estado",
            cell: ({ row }) => {
                const isActive = row.original.is_active;
                return (
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${isActive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {isActive ? <RiToggleFill size={14} className="inline-block align-middle mr-1" /> : <RiToggleLine size={14} className="inline-block align-middle mr-1" />}
                        {row.getValue("estado_badge")}
                    </span>
                );
            },
        },
        {
            accessorKey: "usuarios_count",
            header: "Usuarios",
            cell: ({ row }) => <span className="text-center">{row.getValue("usuarios_count")}</span>,
        },
        {
            accessorKey: "miembros_activos_count",
            header: "Miembros Activos",
            cell: ({ row }) => <span className="text-center">{row.getValue("miembros_activos_count")}</span>,
        },
        {
            accessorKey: "ingresos_mes_formatted",
            header: "Ingresos Mes",
            cell: ({ row }) => <span className="font-mono text-right pr-4">{row.getValue("ingresos_mes_formatted")}</span>,
        },
        {
            id: "actions",
            header: "Acciones",
            cell: ({ row }) => {
                const isActive = row.original.is_active;
                const toggling = togglingId === row.original.id;

                const handleToggle = async () => {
                    setTogglingId(row.original.id);
                    try {
                        await toggleGimnasioActive(row.original.id, !isActive);
                        await fetchGimnasios(page);
                    } catch (toggleErr) {
                        console.error("Error toggling gym:", toggleErr);
                    } finally {
                        setTogglingId(null);
                    }
                };

                return (
                    <button
                        onClick={handleToggle}
                        disabled={toggling}
                        className={`px-3 py-1 rounded text-sm font-medium transition ${isActive ? 'bg-red-50 text-red-600 hover:bg-red-100' : 'bg-green-50 text-green-600 hover:bg-green-100'}`}
                    >
                        {toggling ? "..." : isActive ? "Desactivar" : "Activar"}
                    </button>
                );
            },
        },
    ];

    if (loading) {
        return <div className="text-center py-12 text-on-surface/60">Cargando gimnasios...</div>;
    }

    if (error) {
        return <div className="text-center py-12 text-red-600">{error}</div>;
    }

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-on-surface">Gimnasios de la Plataforma</h2>
            <section className="relative w-full md:w-1/2">
                <span className="absolute left-3 text-lg text-nav top-1/2 -translate-y-1/2"><IoSearch /></span>
                <input
                    type="text"
                    placeholder="Buscar gimnasio..."
                    className="bg-surface-container-high border-none pl-10 pr-4 py-2 rounded-lg text-sm transition-all outline-none w-full focus:ring-primary/20 focus:ring-2"
                    value={search}
                    onChange={handleSearchChange}
                />
            </section>
            <Table
                data={data}
                columns={columns}
                totalRow={{ name: "TOTAL", usuarios_count: data.reduce((a, b) => a + b.usuarios_count, 0), miembros_activos_count: data.reduce((a, b) => a + b.miembros_activos_count, 0) }}
            />
            {totalCount > 20 && (
                <nav className="flex justify-center items-center mt-6">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1 border rounded hover:bg-slate-100 disabled:opacity-50"
                        >
                            Anterior
                        </button>
                        <span className="px-3">
                            Página {page} de {Math.ceil(totalCount / 20)}
                        </span>
                        <button
                            onClick={() => setPage(p => Math.min(Math.ceil(totalCount / 20), p + 1))}
                            disabled={page >= Math.ceil(totalCount / 20)}
                            className="px-3 py-1 border rounded hover:bg-slate-100 disabled:opacity-50"
                        >
                            Siguiente
                        </button>
                    </div>
                </nav>
            )}
        </div>
    );
};
export default GimnasiosPage;