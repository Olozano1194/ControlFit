//Estados
import { useCallback, useEffect, useMemo, useState } from "react";
//API
import { getMembers, deleteMember } from '../../../api/action/userGym.api';
import { getAsignarMemberList } from '../../../api/action/asignarMemberShips.api';
//Table
import { ColumnDef, createColumnHelper } from '@tanstack/react-table';
//Componente principal para la listas
import Table from '../../../components/Table';
import ActionButtons from "../../../components/table/ActionButton";
// components Sections
import HeaderSection from "../../../components/table/section/HeaderSection";
import StatsOverviewSection from "../../../components/table/section/StatsOverviewSection";
//Mensajes
import { toast } from 'react-hot-toast';
//Models
import { Miembro } from "../../../model/member.model";
import { AsignarMemberShips } from "../../../model/asignarMemberShips.model";
// icons
import { IoSearch } from "react-icons/io5";

interface MiembroConEstado extends Miembro {
    membresia?: string;
    totalMembresia?: number | string;
    totalPagado?: number | string;
    saldoPendiente?: number | string;
    estadoPago?: string;
    multiplier?: number | string;
}

interface MiembroTotal {
    id: 'total';
    name: string;
    lastname?: string;
    phone?: string;
    address?: string;
    membresia?: string;
    totalMembresia?: number | string;
    totalPagado?: number | string;
    saldoPendiente?: number | string;
    estadoPago?: string;
}

type Member = MiembroTotal | MiembroConEstado;

const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
};

const EstadoBadge = ({ estado }: { estado?: string }) => {
    if (!estado) return null;
    const config: Record<string, { label: string; class: string }> = {
        paid: { label: 'Al día', class: 'bg-green-100 text-green-700' },
        partial: { label: 'Parcial', class: 'bg-yellow-100 text-yellow-700' },
        pending: { label: 'Pendiente', class: 'bg-red-100 text-red-700' },
    };
    const c = config[estado] || { label: estado, class: 'bg-gray-100 text-gray-700' };
    return (
        <span className={`inline-block px-2 py-1 rounded-full text-xs font-semibold ${c.class}`}>
            {c.label}
        </span>
    );
};

const ListMiembro = () => {
    const [users, setUser] = useState<Miembro[]>([]);
    const [asignaciones, setAsignaciones] = useState<AsignarMemberShips[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [filteredData, setFilteredData] = useState<ReturnType<typeof setTimeout> | null>(null);
    const [search, setSearch] = useState('');

    // Mapa de miembro_id -> última membresía asignada
    const miembrosConEstado = useMemo(() => {
        const map = new Map<number, AsignarMemberShips>();
        for (const a of asignaciones) {
            const mid = typeof a.miembro === 'number' ? a.miembro : a.miembro?.id;
            if (mid != null && !map.has(mid)) {
                map.set(mid, a);
            }
        }
        return map;
    }, [asignaciones]);

    const enrichedUsers = useMemo((): Member[] => {
        return users.map((u) => {
            const asignacion = miembrosConEstado.get(u.id);
            if (!asignacion) return u;
            const mult = Number(asignacion.multiplier || 1);
            return {
                ...u,
                membresia: mult > 1
                    ? (asignacion.membresia_details?.name || '-') + ' x' + mult
                    : (asignacion.membresia_details?.name || '-'),
                totalMembresia: asignacion.price,
                totalPagado: asignacion.total_pagado,
                saldoPendiente: asignacion.saldo_pendiente,
                estadoPago: asignacion.estado_pago,
                multiplier: mult,
            } as MiembroConEstado;
        });
    }, [users, miembrosConEstado]);

    // Función en donde se buscan los datos
    const handleSearch = useCallback(async(user: string) => {
        setIsLoading(true);
        try {
            const [membersRes, asignacionesRes] = await Promise.all([
                getMembers(user),
                getAsignarMemberList()
            ]);
            setUser(membersRes);
            setAsignaciones(asignacionesRes);
        } catch (error) {
            console.error('Error al buscar el miembro:', error);
        }finally {
            setIsLoading(false);
        }       
    }, []);
    
    useEffect(() => {
        const fetchUserData = async () => {
            setIsLoading(true);
            try {
                const [membersRes, asignacionesRes] = await Promise.all([
                    getMembers(),
                    getAsignarMemberList()
                ]);
                setUser(membersRes);
                setAsignaciones(asignacionesRes);
            }catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Error al cargar los datos';
                toast.error(errorMessage);
            }finally {
                setIsLoading(false);
            }
        };
        fetchUserData();

        return () => {
            if (filteredData) clearTimeout(filteredData);
        };
    }, [filteredData]);

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const searchValue = e.target.value.toLowerCase();
        setSearch(searchValue);

        if (filteredData) clearTimeout(filteredData);

        setFilteredData(setTimeout(() => {
            handleSearch(searchValue)
        }, 500));
    }

    const columnHelper = createColumnHelper<Member>();

    const columns = [
        columnHelper.accessor((_, index) => index + 1, {
            id: 'index',
            header: 'N°',
            cell: (info) => info.row.index + 1,
        }),
        columnHelper.accessor(row => `${row.name}`, {
            id: 'name',
            header: 'Nombre',
            cell: (info) => info.getValue(),
        }),
        columnHelper.accessor(row => row.lastname, {
            id: 'lastname',
            header: 'Apellido',
            cell: (info) => info.getValue(),
        }),
        columnHelper.accessor(row => row.phone, {
            id: 'phone',
            header: 'Telefono',
            cell: (info) => info.getValue()
        }),
        columnHelper.accessor(row => row.address, {
            id: 'address',
            header: 'Dirección',
            cell: (info) => info.getValue()
        }),
        columnHelper.accessor(row => {
            return (row as MiembroConEstado).membresia || '-';
        }, {
            id: 'membresia',
            header: 'Membresía',
            cell: (info) => {
                const val = info.getValue();
                return <span className="text-sm">{val}</span>;
            },
        }),
        columnHelper.accessor(row => {
            const val = (row as MiembroConEstado).totalMembresia;
            return val ? formatCurrency(Number(val)) : '-';
        }, {
            id: 'totalMembresia',
            header: 'Total',
            cell: (info) => <span className="font-medium">{info.getValue()}</span>,
        }),
        columnHelper.accessor(row => {
            const val = (row as MiembroConEstado).totalPagado;
            return val ? formatCurrency(Number(val)) : '-';
        }, {
            id: 'totalPagado',
            header: 'Pagado',
            cell: (info) => <span className="font-medium">{info.getValue()}</span>,
        }),
        columnHelper.accessor(row => {
            const val = (row as MiembroConEstado).saldoPendiente;
            return val ? formatCurrency(Number(val)) : '-';
        }, {
            id: 'saldoPendiente',
            header: 'Saldo Pend.',
            cell: (info) => <span className="font-medium">{info.getValue()}</span>,
        }),
        columnHelper.accessor(row => (row as MiembroConEstado).estadoPago, {
            id: 'estadoPago',
            header: 'Estado',
            cell: (info) => <EstadoBadge estado={info.getValue()} />,
        }),
        columnHelper.display({
            id: 'actions',
            header: 'Acciones',
            cell: props => {
                const id = props.row.original.id;
                if(typeof id !== 'number') return null;
                return(
                    <ActionButtons
                        id={id}
                        editPath={`/dashboard/miembro/${id}`}
                        onDelete={async (id) => { await deleteMember(id);
                        setUser(users.filter(user => user.id !== id)); 
                        }}
                        confirmMessage="¿Estas seguro de eliminar este miembro?"
                    />
                );
            },           
        }),
    ] as ColumnDef<Member>[];    

    return (
        <main className="bg-surface-container-lowest w-full flex flex-col justify-center items-center gap-y-4 p-4 rounded-xl">
            <HeaderSection
                title="Listado de"
                highlight="Miembros" 
            />
            <StatsOverviewSection />            
            <section className="relative w-full">
                <span className="absolute left-3 text-lg text-nav top-1/2 -translate-y-1/2"><IoSearch /></span>
                <input 
                    type="text"
                    placeholder="Buscar miembro..."
                    className="bg-surface-container-high border-none pl-10 pr-4 py-2 rounded-lg text-sm transition-all outline-none p-2 w-full focus:ring-primary/20 focus:ring-2 md:w-1/2"
                    value={search}
                    onChange={handleSearchChange}
                />
            </section>
            {
                isLoading ? (
                    <div className="text-center py-4">Buscando...</div>
                ) : (
                        <Table 
                            data={enrichedUsers} 
                            columns={columns} 
                        />
                    )
            }                         
        </main>
    );
}
export default ListMiembro;