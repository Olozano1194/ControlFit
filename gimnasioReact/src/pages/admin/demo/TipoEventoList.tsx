// Table
import { ColumnDef, createColumnHelper } from "@tanstack/react-table";
import Table from "../../../components/Table";
// API
import { type DemoRequest } from "../../../api/action/demoRequests.api";
// Icons
import { IoTrashBinOutline } from "react-icons/io5";



// ─── Props ───────────────────────────────────────────────────────────────────

interface TipoEventoListProps {
    requests: DemoRequest[];
    handleToggleEstado: (id: number, estado: DemoRequest['estado']) => void;
    loadingIds: Set<number>;
    handleOpenDeleteModal: (request: DemoRequest) => void;
    isDeleting: boolean;
    
}

// Badge de estado con toggle al hacer click
const EstadoBadge = ({
    id,
    estado,
    onToggle,
    isLoading,
}: {
    id: number;
    estado: DemoRequest['estado'];
    onToggle: (id: number, estado: DemoRequest['estado']) => void;
    isLoading: boolean;
}) => {
    const config = {
        pendiente: { label: 'Pendiente', class: 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' },
        contactado: { label: 'Contactado', class: 'bg-green-100 text-green-700 hover:bg-green-200' },
        cancelada: { label: 'Cancelada', class: 'bg-red-100 text-red-700' },
    };
    const c = config[estado];
    
    // Cancelada is read-only, no toggle
    if (estado === 'cancelada') {
        return (
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${c.class}`}>
                {c.label}
            </span>
        );
    }
    
    return (
        <button
            type="button"
            onClick={() => !isLoading && onToggle(id, estado)}
            disabled={isLoading}
            className={`inline-block px-3 py-1 rounded-full text-xs font-semibold transition-colors ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${c.class}`}
            title={isLoading ? "Actualizando..." : "Click para cambiar estado"}
        >
            {isLoading ? (
                <span className="flex items-center gap-1">
                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Cargando...</span>
                </span>
            ) : (
                c.label
            )}
        </button>
    );
};

const TipoEventoList = ({ requests, handleToggleEstado, loadingIds, handleOpenDeleteModal, isDeleting }: TipoEventoListProps) => {

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
                    isLoading={loadingIds.has(info.row.original.id)}
                />
            ),
        }),
        columnHelper.accessor('id', {
            header: 'Acciones',
            id: 'actions',
            cell: info => {
                const estado = info.row.original.estado;
                // Only show delete button for pendiente or contactado
                if (estado !== 'pendiente' && estado !== 'contactado') {
                    return null;
                }
                return (
                    <button
                        type="button"
                        onClick={() => handleOpenDeleteModal(info.row.original)}
                        disabled={isDeleting}
                        className="text-red-600 hover:text-red-800 transition-colors p-1 rounded hover:bg-red-50"
                        title="Cancelar solicitud"
                    >
                        <IoTrashBinOutline className="w-5 h-5" />
                    </button>
                );
            },
        }),
    ] as ColumnDef<DemoRequest>[];


    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-on-surface">Solicitudes de Demo</h2>                
            </div>
            <Table data={requests} columns={columns} />
        </div>
    );
}
export default TipoEventoList;