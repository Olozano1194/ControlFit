import { useEffect, useState } from "react";
import { toast } from "react-hot-toast";
// API
import { getDemoRequests, updateDemoRequestEstado, type DemoRequest } from "../../../api/action/demoRequests.api";
// Table
import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import Table from "../../../components/Table";
// Components
import HeaderSection from "../../../components/table/section/HeaderSection";
// Icons
import { IoSearch } from "react-icons/io5";
import { MdFitnessCenter } from "react-icons/md";

// Badge de estado con toggle al hacer click
const EstadoBadge = ({ id, estado, onToggle }: { id: number; estado: DemoRequest['estado']; onToggle: (id: number, estado: DemoRequest['estado']) => void }) => {
    const config = {
        pendiente: { label: 'Pendiente', class: 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' },
        contactado: { label: 'Contactado', class: 'bg-green-100 text-green-700 hover:bg-green-200' },
    };
    const c = config[estado];
    return (
        <button
            type="button"
            onClick={() => onToggle(id, estado)}
            className={`inline-block px-3 py-1 rounded-full text-xs font-semibold transition-colors cursor-pointer ${c.class}`}
            title="Click para cambiar estado"
        >
            {c.label}
        </button>
    );
};

const DemoRequestsPage = () => {
    const [requests, setRequests] = useState<DemoRequest[]>([]);
    const [filtered, setFiltered] = useState<DemoRequest[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const data = await getDemoRequests();
                setRequests(data);
                setFiltered(data);
            } catch {
                toast.error('Error al cargar las solicitudes de demo');
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.toLowerCase();
        setSearch(value);
        setFiltered(
            requests.filter(r =>
                r.nombre.toLowerCase().includes(value) ||
                r.nombre_gimnasio.toLowerCase().includes(value) ||
                r.email.toLowerCase().includes(value) ||
                r.telefono.includes(value)
            )
        );
    };

    const handleToggleEstado = async (id: number, estadoActual: DemoRequest['estado']) => {
        const nuevoEstado = estadoActual === 'pendiente' ? 'contactado' : 'pendiente';
        try {
            const updated = await updateDemoRequestEstado(id, nuevoEstado);
            setRequests(prev => prev.map(r => r.id === id ? updated : r));
            setFiltered(prev => prev.map(r => r.id === id ? updated : r));
            toast.success(`Marcado como ${nuevoEstado}`);
        } catch {
            toast.error('No se pudo actualizar el estado');
        }
    };

    const columnHelper = createColumnHelper<DemoRequest>();

    const columns = [
        columnHelper.accessor((_, i) => i + 1, {
            id: 'index',
            header: 'N°',
            cell: info => info.row.index + 1,
        }),
        columnHelper.accessor('nombre_gimnasio', {
            header: 'Gimnasio',
            cell: info => <span className="font-medium">{info.getValue()}</span>,
        }),
        columnHelper.accessor('nombre', {
            header: 'Contacto',
            cell: info => info.getValue(),
        }),
        columnHelper.accessor('email', {
            header: 'Email',
            cell: info => (
                <a href={`mailto:${info.getValue()}`} className="text-primary hover:underline">
                    {info.getValue()}
                </a>
            ),
        }),
        columnHelper.accessor('telefono', {
            header: 'Teléfono / WhatsApp',
            cell: info => (
                <a
                    href={`https://wa.me/${info.getValue().replace(/\D/g, '')}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 hover:underline font-medium"
                >
                    {info.getValue()}
                </a>
            ),
        }),
        columnHelper.accessor('fecha_solicitud', {
            header: 'Fecha',
            cell: info => new Date(info.getValue()).toLocaleDateString('es-CO', {
                day: '2-digit', month: 'short', year: 'numeric'
            }),
        }),
        columnHelper.accessor('estado', {
            header: 'Estado',
            cell: info => (
                <EstadoBadge
                    id={info.row.original.id}
                    estado={info.getValue()}
                    onToggle={handleToggleEstado}
                />
            ),
        }),
    ] as ColumnDef<DemoRequest>[];

    const pendientes = requests.filter(r => r.estado === 'pendiente').length;

    return (
        <main className="bg-surface-container-lowest w-full flex flex-col justify-center items-center gap-y-4 p-4 rounded-xl">
            <HeaderSection title="Solicitudes de" highlight="Demo" />

            {/* Stats rápidas */}
            <section className="w-full grid grid-cols-2 gap-4 md:grid-cols-3">
                <div className="bg-surface-container-high p-4 rounded-xl flex items-center gap-3">
                    <span className="text-2xl text-primary"><MdFitnessCenter /></span>
                    <div>
                        <p className="text-xs text-secondary uppercase tracking-wide font-semibold">Total</p>
                        <p className="text-2xl font-black text-on-surface">{requests.length}</p>
                    </div>
                </div>
                <div className="bg-yellow-50 p-4 rounded-xl flex items-center gap-3">
                    <span className="text-2xl">⏳</span>
                    <div>
                        <p className="text-xs text-yellow-700 uppercase tracking-wide font-semibold">Pendientes</p>
                        <p className="text-2xl font-black text-yellow-700">{pendientes}</p>
                    </div>
                </div>
                <div className="bg-green-50 p-4 rounded-xl flex items-center gap-3">
                    <span className="text-2xl">✅</span>
                    <div>
                        <p className="text-xs text-green-700 uppercase tracking-wide font-semibold">Contactados</p>
                        <p className="text-2xl font-black text-green-700">{requests.length - pendientes}</p>
                    </div>
                </div>
            </section>

            {/* Buscador */}
            <section className="relative w-full">
                <span className="absolute left-3 text-lg text-nav top-1/2 -translate-y-1/2"><IoSearch /></span>
                <input
                    type="text"
                    placeholder="Buscar por nombre, gimnasio, email o teléfono..."
                    className="bg-surface-container-high border-none pl-10 pr-4 py-2 rounded-lg text-sm transition-all outline-none w-full focus:ring-primary/20 focus:ring-2 md:w-1/2"
                    value={search}
                    onChange={handleSearch}
                />
            </section>

            {isLoading ? (
                <div className="text-center py-8 text-secondary animate-pulse">Cargando solicitudes...</div>
            ) : (
                <Table data={filtered} columns={columns} />
            )}
        </main>
    );
};

export default DemoRequestsPage;
