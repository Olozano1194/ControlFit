//Estados
import { useCallback,useEffect, useState } from "react";
//API
import { getMembersDay, deleteMember } from '../../../api/action/userGymDay.api';
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
import { MemberDay } from "../../../model/memberDay.model";
// icons
import { IoSearch } from "react-icons/io5";


interface MiembroTotal {
    id: 'total';
    name: string;
    lastname?: string;
    phone?: string;
    dateInitial?: string;
    price: number | string;
};

type DayMember = MiembroTotal | MemberDay;


const ListMiembroDay = () => {
    const [users, setUser] = useState<MemberDay[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [filteredData, setFilteredData] = useState<ReturnType<typeof setTimeout> | null>(null);
    const [search, setSearch] = useState('');

    // Función en donde se buscan los datos
    const handleSearch = useCallback(async(user: string) => {
            setIsLoading(true);
            try {
                const response = await getMembersDay(user);
                setUser(response);
            } catch (error) {
                console.error('Error al buscar el miembro diario:', error);
                
            }finally {
                setIsLoading(false);
            }       
    }, []);

    useEffect(() => {
        const fetchUserData = async () => {
            setIsLoading(true);
            try {
                const data = await getMembersDay();
                setUser(data);
            }catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Error al cargar los datos';
                toast.error(errorMessage);
            }finally {
                setIsLoading(false);
            }
        };
        fetchUserData();
        //Limpiamos el timeout cada vez que se renderiza la página
        return () => {
            if (filteredData) clearTimeout(filteredData);
        };
    }, []);

    //Manejamos el evento de búsqueda
    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const searchValue = e.target.value.toLowerCase();
        setSearch(searchValue);

        if (filteredData) clearTimeout(filteredData);

        setFilteredData(setTimeout(() => {
            handleSearch(searchValue)
        }, 500));
    }

    const columnHelper = createColumnHelper<DayMember>();

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
     const total = users.reduce((acc, user) => {
        const price = typeof user.price === 'string' ? parseFloat(user.price) : user.price;
        return acc + price;
    }, 0);

    const totalRow: MiembroTotal = {
        id: 'total',
        name: 'Total',
        price: `${formatCurrency(total)}`, 
    };

    const columns = [
        columnHelper.accessor((_, index) => index + 1, {
            id: 'index',
            header: 'N°',
            cell: (info) => {
                // Solo mostrar el número si no es la fila de total
                return info.row.index + 1;
            },
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
        columnHelper.accessor(row => row.dateInitial, {
            id: 'dateInitial',
            header: 'Fecha Inicial',
            cell: (info) => info.getValue()
        }),
        columnHelper.accessor('price', {
            id: 'price',
            header: 'Precio',
            cell: info => {
                const isTotalRow = info.row.original.id === 'total';
                const raw = info.getValue<DayMember['price']>();
                const priceNum  = typeof raw === 'string' ? parseFloat(raw) : raw;              
                // Si es la fila de total, mostrar en negrita
                return (
                    <div className={isTotalRow ? 'font-bold' : ''}>
                        {formatCurrency(priceNum)}
                    </div>
                )              
            },
        }),
        columnHelper.display({
            id: 'actions',
            header: 'Acciones',
            cell: props => {
                const id = props.row.original.id;
                //si es la fila total, no mostrar botones
                if(typeof id !== 'number') return null;

                return (                    
                    <ActionButtons
                        id={id}
                        editPath={`/dashboard/miembro-day/${id}`}
                        onDelete={async (id) => { await deleteMember(id);
                        setUser(users.filter(user => user.id !== id)); 
                        }}
                        confirmMessage="¿Estas seguro de eliminar este miembro?"
                    />
                );
            },
        }),
    ] as ColumnDef<DayMember>[];
    
    return (
        <main className="bg-surface-container-lowest w-full flex flex-col justify-center items-center gap-y-4 p-4 rounded-xl">
            <HeaderSection
                title="Listado de Miembros por"
                highlight="Día" 
            />
            <StatsOverviewSection />
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
                            data={users} 
                            columns={columns} 
                            totalRow={totalRow} 
                        />
                    )
            }                         
        </main>
    );
}
export default ListMiembroDay; 