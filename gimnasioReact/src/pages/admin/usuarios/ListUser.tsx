import { useEffect, useState } from "react";
//API
import { getUsers } from "../../../api/users/users.api";
//Table
import { ColumnDef, createColumnHelper } from '@tanstack/react-table';
//Componente principal para la listas
import Table from '../../../components/Table';
// components Sections
import HeaderSection from "../../../components/table/section/HeaderSection";
//Mensajes
import { toast } from 'react-hot-toast';
//Models
import { User } from '../../../model/user.model';
//Error handling
import { getApiErrorMessage } from '../../../utils/apiError';


const ListUser = () => {
    const [users, setUser] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const fetchUserData = async () => {
            setIsLoading(true);
            try {
                const data = await getUsers();
                //console.log('User data received:', data);                
                setUser(data);
            }catch (error) {
                toast.error(getApiErrorMessage(error, 'Error al cargar los datos'));
            }finally {
                setIsLoading(false);
            }
        };
        fetchUserData();
    }, []);

    const columnHelper = createColumnHelper<User>();

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
        columnHelper.accessor(row => row.email, {
            id: 'email',
            header: 'Correo',
        }),
        columnHelper.accessor(row => row.roles, {
            id: 'roles',
            header: 'Rol',
        }),
        // columnHelper.accessor('actions', {
        //     header: 'Acciones',
        //     cell: (({ row }) => (
        //         <div className="flex justify-center items-center gap-x-4">
        //             <Link to={`/edit/usuarios/${row.original.id}`} className="bg-green-500 text-white p-2 rounded-md">Editar</Link>
        //             <button className="bg-red-500 text-white p-2 rounded-md">Eliminar</button>
        //         </div>
        //     )),
        // }),
    ] as ColumnDef<User>[];

    return (
        <main className="bg-surface-container-lowest w-full flex flex-col justify-center items-center gap-y-4 p-4 rounded-xl">
            <HeaderSection
                title="Listado de"
                highlight="Usuarios" 
            />
            {
                isLoading ? (
                    <div className="text-center py-4">Cargando...</div>

                ): (
                    <Table 
                        data={users} 
                        columns={columns}                          
                    />
                )
            }               
        </main>
    );
}
export default ListUser;