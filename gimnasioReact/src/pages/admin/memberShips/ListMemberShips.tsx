//Estados
import { useEffect, useState } from "react";
//API
import { getMemberList, deleteMemberShips } from '../../../api/action/memberShips.api';
//Table
import { ColumnDef, createColumnHelper } from '@tanstack/react-table';
//Componente principal para la listas
import Table from '../../../components/Table';
import ActionButtons from "../../../components/table/ActionButton";
// components Sections
import HeaderSection from "../../../components/table/section/HeaderSection";
//Mensajes
import { toast } from 'react-hot-toast';
//Models
import { Membresia } from "../../../model/memberShips.model";
//Error handling
import { getApiErrorMessage } from "../../../utils/apiError";



interface MembresiaTotal {
    id: 'total';
    name: string;
    duration?: string;
    price: number | string;
};

type MemberShips = MembresiaTotal | Membresia;

const ListMemberShips = () => {
    const [memberShips, setMemberShips] = useState<MemberShips[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const fetchUserData = async () => {
            setIsLoading(true);
            try {
                const data = await getMemberList();
                setMemberShips(data);
            } catch (error) {
                toast.error(getApiErrorMessage(error, 'Error al cargar los datos'));
            } finally {
                setIsLoading(false);
            }
        };
        fetchUserData();
    }, []);

    const columnHelper = createColumnHelper<MemberShips>();

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
        columnHelper.accessor(row => `${row.duration}`, {
            id: 'duration',
            header: 'Duración de la membresía',
            cell: (info) => info.getValue(),
        }),
        columnHelper.accessor('price', {
            id: 'price',
            header: 'Precio',
            cell: info => {
                const isTotalRow = info.row.original.id === 'total';
                const raw = info.getValue<MemberShips['price']>();
                const priceNum = typeof raw === 'string' ? parseFloat(raw) : raw;
                // Si es la fila de total, mostrar en negrita
                return (
                    <div className={isTotalRow ? 'font-bold' : ''}>
                        ${priceNum.toFixed(2)}
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
                if (typeof id !== 'number') return null;

                return (
                    // <div className="flex justify-center items-center gap-x-4">
                    //     <Link to={`/dashboard/membresia/${id}`} className="bg-green-500 text-white p-2 rounded-md hover:scale-110">
                    //         <RiPencilLine />
                    //     </Link>
                    //     <button
                    //         onClick={ async () => {
                    //             if (window.confirm('¿Estás seguro de eliminar este miembro?')){
                    //                 try {
                    //                     await deleteMemberShips(id);
                    //                     setMemberShips(memberShips.filter(memberShips => memberShips.id !== id));
                    //                     toast.success('Membresía Eliminada', {
                    //                         duration: 3000,
                    //                         position: 'bottom-right',
                    //                         style: {
                    //                             background: '#4b5563',   // Fondo negro
                    //                             color: '#fff',           // Texto blanco
                    //                             padding: '16px',
                    //                             borderRadius: '8px',
                    //                         },                    
                    //                     });  
                    //                 } catch (error) {
                    //                     const errorMessage = error instanceof Error ? error.message : 'Error al eliminar la membresía';
                    //                     toast.error(errorMessage);
                    //                 }
                    //             }                               
                    //         }} 
                    //         className="bg-red-500 text-white p-2 rounded-md hover:scale-110">
                    //             <RiDeleteBinLine />
                    //     </button>
                    // </div>
                    <ActionButtons
                        id={id}
                        editPath={`/dashboard/membresia/${id}`}
                        onDelete={async (id) => {
                            await deleteMemberShips(id);
                            setMemberShips(memberShips.filter(memberShip => memberShip.id !== id));
                        }}
                        confirmMessage="¿Estas seguro de eliminar este miembro?"
                    />
                );
            },
        }),
    ] as ColumnDef<MemberShips>[];

    //Calculamos el total de los precios
    const total = memberShips.reduce((acc, user) => {
        const price = typeof user.price === 'string' ? parseFloat(user.price) : user.price;
        return acc + price;
    }, 0);

    const totalRow: MembresiaTotal = {
        id: 'total',
        name: 'Total',
        price: `$ ${total}`,
    };

    // Añadir una fila extra con el total
    //const dataWithTotal = [...users, { id: 'total', name: 'Total', price: total.toFixed(2) }];

    return (
        <main className="bg-surface-container-lowest w-full flex flex-col justify-center items-center gap-y-4 p-4 rounded-xl">
            <HeaderSection
                title="Listado de"
                highlight="Membresías" 
            />

            {
                isLoading ? (
                    <div className="text-center py-4">Buscando...</div>
                ) : (
                    <Table
                        data={memberShips}
                        columns={columns}
                        totalRow={totalRow}
                    />
                )
            }
        </main>
    );
}
export default ListMemberShips;