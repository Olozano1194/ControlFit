import { useMemo } from 'react';
import { ColumnDef } from '@tanstack/react-table';
import { toast } from 'react-hot-toast';
import { FiEdit2, FiTrash2, FiPlus } from 'react-icons/fi';
import Table from '../../../components/Table';
import { TipoEvento } from '../../../model/calendario.model';
import { deleteTipoEvento } from '../../../api/action/calendario.api';

// ─── Props ───────────────────────────────────────────────────────────────────

interface TipoEventoListProps {
    tipos: TipoEvento[];
    onEdit: (tipo: TipoEvento) => void;
    onCreate: () => void;
    onRefresh: () => void;
}

// ─── Componente ──────────────────────────────────────────────────────────────

const TipoEventoList = ({ tipos, onEdit, onCreate, onRefresh }: TipoEventoListProps) => {
    const columns = useMemo<ColumnDef<TipoEvento>[]>(
        () => [
            {
                header: 'Color',
                accessorKey: 'color',
                cell: ({ row }) => (
                    <div className="flex items-center gap-2">
                        <span
                            className="inline-block w-6 h-6 rounded-full border border-outline-variant/20"
                            style={{ backgroundColor: row.original.color }}
                        />
                        <span className="font-mono text-xs text-secondary">
                            {row.original.color}
                        </span>
                    </div>
                ),
            },
            {
                header: 'Nombre',
                accessorKey: 'nombre',
                cell: ({ row }) => (
                    <span className="font-medium text-on-surface">
                        {row.original.nombre}
                    </span>
                ),
            },
            {
                header: 'Acciones',
                id: 'acciones',
                cell: ({ row }) => (
                    <div className="flex gap-2">
                        <button
                            onClick={() => onEdit(row.original)}
                            className="p-2 text-sky-600 hover:bg-sky-50 rounded-lg transition-colors cursor-pointer"
                            title="Editar"
                            aria-label={`Editar ${row.original.nombre}`}
                        >
                            <FiEdit2 size={16} />
                        </button>
                        <button
                            onClick={async () => {
                                if (
                                    !window.confirm(
                                        `¿Eliminar el tipo "${row.original.nombre}"?`
                                    )
                                )
                                    return;
                                try {
                                    await deleteTipoEvento(row.original.id);
                                    toast.success('Tipo eliminado correctamente');
                                    onRefresh();
                                } catch (error: unknown) {
                                    const err = error as {
                                        response?: { status?: number };
                                    };
                                    if (err?.response?.status === 409) {
                                        toast.error(
                                            'No se puede eliminar: el tipo tiene eventos asociados'
                                        );
                                    } else {
                                        toast.error('Error al eliminar el tipo');
                                    }
                                }
                            }}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                            title="Eliminar"
                            aria-label={`Eliminar ${row.original.nombre}`}
                        >
                            <FiTrash2 size={16} />
                        </button>
                    </div>
                ),
            },
        ],
        [onEdit, onRefresh]
    );

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h4 className="font-bold text-lg text-on-surface">
                    Tipos de Evento
                </h4>
                <button
                    onClick={onCreate}
                    className="bg-sky-600 cursor-pointer flex font-semibold gap-2 items-center px-4 py-2 rounded-lg text-sm text-white transition-colors hover:bg-sky-500"
                >
                    <FiPlus size={16} />
                    Nuevo Tipo
                </button>
            </div>
            <Table<TipoEvento> data={tipos} columns={columns} />
        </div>
    );
};

export default TipoEventoList;