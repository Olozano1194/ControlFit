//Estados
import { useCallback, useEffect, useState } from "react";
//API
import { getAsignarMemberList, deleteAsignarMemberShips } from '../../../api//action/asignarMemberShips.api';
//models
import { AsignarMemberShips } from '../../../model/asignarMemberShips.model';
// Table
import { createColumnHelper, ColumnDef } from '@tanstack/react-table';
//Componente principal para la listas
import Table from '../../../components/Table';
import ActionButtons from "../../../components/table/ActionButton";
// components Sections
import HeaderSection from "../../../components/table/section/HeaderSection";
//Mensajes
import { toast } from 'react-hot-toast';
// icons
import { IoSearch } from "react-icons/io5";
import { FaMoneyBillWave } from "react-icons/fa";
// Modal de pago
import PagoMembresiaModal from "./PagoMembresiaModal";


interface AsignacionTotal {
    id: 'total';
    name: string;
    miembro_details?: {
        id: number;
        name: string;
        lastname: string;        
    };
    membresia_details?: {
        id: number;
        name: string;
        price: number;        
    };
    dateInitial?: string;
    dateFinal?:   string;
    price: number | string;
    estado_pago?: string;
    multiplier?: never;
}

type Asignacion = AsignacionTotal | AsignarMemberShips;

const ListAsignarMemberShips = () => {    
    const [asignarMemberShips, setAsignarMemberShips] = useState<Asignacion[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [filteredData, setFilteredData] = useState<ReturnType<typeof setTimeout> | null>(null);
    const [search, setSearch] = useState('');
    const [pagoModal, setPagoModal] = useState<{
        open: boolean;
        id: number;
        price: number | string;
        totalPagado: number | string;
        saldoPendiente: number | string;
    }>({ open: false, id: 0, price: 0, totalPagado: 0, saldoPendiente: 0 });

    // Función en donde se buscan los datos
    const handleSearch = useCallback(async(user: string) => {
        setIsLoading(true);
        try {
            const response = await getAsignarMemberList(user);
            setAsignarMemberShips(response);
        } catch (error) {
            console.error('Error al buscar el miembro diario:', error);
        }finally {
            setIsLoading(false);
        }       
    }, []);

    const refreshList = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await getAsignarMemberList();
            setAsignarMemberShips(response);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Error al cargar los datos';
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        refreshList();
        //Limpiamos el timeout cada vez que se renderiza la página
        return () => {
            if (filteredData) clearTimeout(filteredData);
        };
    }, [filteredData, refreshList]);

    //Manejamos el evento de búsqueda
    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const searchValue = e.target.value.toLowerCase();
        setSearch(searchValue);

        if (filteredData) clearTimeout(filteredData);

        setFilteredData(setTimeout(() => {
            handleSearch(searchValue)
        }, 500));
    }

    const columnHelper = createColumnHelper<Asignacion>();

    //Función para dar formato a la moneda en este caso pesos colombianos
    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
        }).format(amount);
    };

    //Calculamos el total de los precios
    const total = asignarMemberShips.reduce((acc, item) => {
        const price = typeof item.price === 'string' ? parseFloat(item.price) : item.price;
        return acc + price;
    }, 0);        

    const totalRow: AsignacionTotal & { nombreCompleto?: string } = {
        id: 'total',
        name: 'Total',
        nombreCompleto: 'Total',
        price: formatCurrency(total),
        estado_pago: '',
    };

    // Badge de estado de pago
    const EstadoBadge = ({ estado }: { estado: string }) => {
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

    const columns = [
        columnHelper.display({
            id: 'index',
            header: 'N°',
            cell: info => info.row.index + 1,                      
        }),
        columnHelper.accessor(row => {
            if (row.id === 'total') return row.name;
            return `${row.miembro_details?.name} ${row.miembro_details?.lastname}`;
        }, {
            id: 'nombreCompleto',
            header: 'Nombre',
            cell: (info) => info.getValue(),            
        }),
        columnHelper.accessor(row => {
            const name = row.membresia_details?.name || '-';
            const mult = row.multiplier ? Number(row.multiplier) : 1;
            return mult > 1 ? name + ' x' + mult : name;
        }, {
            id: 'membresia',
            header: 'Membresía',
            cell: info => info.getValue(),
        }),
        columnHelper.accessor(row => row.dateInitial, {
            id: 'dateInitial',
            header: 'Fecha Inicial',
            cell: (info) => info.getValue()
        }),
        columnHelper.accessor(row => row.dateFinal, {
            id: 'dateFinal',
            header: 'Fecha Final',
            cell: (info) => info.getValue()
        }),
        columnHelper.accessor('price', {
            id: 'price',
            header: 'Precio',
            cell: info => {
                const isTotalRow = info.row.original.id === 'total';
                const raw = info.getValue<Asignacion['price']>();
                const priceNum  = typeof raw === 'string' ? parseFloat(raw) : raw;                              
                return (
                    <div className={isTotalRow ? 'font-bold text-gray-50' : ''}>
                        {formatCurrency(priceNum)}
                    </div>
                )          
            },
        }),
        columnHelper.accessor(row => {
            if (row.id === 'total') return '';
            return (row as AsignarMemberShips).estado_pago || 'pending';
        }, {
            id: 'estado_pago',
            header: 'Estado',
            cell: info => {
                const val = info.getValue();
                if (!val) return null;
                return <EstadoBadge estado={val} />;
            },
        }),
        columnHelper.display({
            id: 'actions',
            header: 'Acciones',
            cell: props => {
                const row = props.row.original;
                const id = row.id;
                if(typeof id !== 'number') return null;
                const asignacion = row as AsignarMemberShips;
                const puedePagar = asignacion.estado_pago && asignacion.estado_pago !== 'paid';
                return (
                    <div className="flex items-center gap-2">
                        {puedePagar && (
                            <button
                                onClick={() => setPagoModal({
                                    open: true,
                                    id: id,
                                    price: asignacion.price,
                                    totalPagado: asignacion.total_pagado,
                                    saldoPendiente: asignacion.saldo_pendiente,
                                })}
                                className="flex items-center gap-1 text-sm bg-sky-600 text-white px-2 py-1 rounded-md hover:bg-sky-500 transition"
                                title="Registrar pago"
                            >
                                <FaMoneyBillWave /> Pagar
                            </button>
                        )}
                        <ActionButtons
                            id={id}
                            editPath={`/dashboard/miembro/${id}`}
                            onDelete={async (id) => { await deleteAsignarMemberShips(id);
                            setAsignarMemberShips(asignarMemberShips.filter(asignarmemberShips => asignarmemberShips.id !== id)); 
                            }}
                            confirmMessage="¿Estas seguro de eliminar esta asignación?"
                        />
                    </div>
                );
            },
        }),               
                
        ] as ColumnDef<Asignacion>[];
        
        return (
            <main className="bg-surface-container-lowest w-full flex flex-col justify-center items-center gap-y-4 p-4 rounded-xl">
            <HeaderSection
                title="Listado de Asignación"
                highlight="Membresías" 
            />
            
            {/* Busqueda */}
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
                            data={asignarMemberShips} 
                            columns={columns} 
                            totalRow={totalRow} 
                        />
                    )
            }

            {/* Modal de pago */}
            <PagoMembresiaModal
                isOpen={pagoModal.open}
                onClose={() => setPagoModal(prev => ({ ...prev, open: false }))}
                onSuccess={refreshList}
                membresiaAsignadaId={pagoModal.id}
                totalPrice={pagoModal.price}
                totalPagado={pagoModal.totalPagado}
                saldoPendiente={pagoModal.saldoPendiente}
            />
        </main>
        );
};
export default ListAsignarMemberShips;