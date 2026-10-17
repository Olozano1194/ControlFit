//Enlaces
import { Link } from "react-router-dom";
//Mensajes
import { toast } from 'react-hot-toast';
//Icons
import { RiDeleteBinLine, RiPencilLine } from "react-icons/ri";
//Error handling
import { getApiErrorMessage } from "../../utils/apiError";

interface ActionButtonsProps {
    id: number;
    editPath: string;
    onDelete: (id: number) => Promise<void>;
    confirmMessage: string;
};

const ActionButtons: React.FC<ActionButtonsProps> = ({ id, editPath, onDelete, confirmMessage = '¿Estas seguro de eliminar este registro?' }) => {

    const handleDelete = async () => {
        if (!window.confirm(confirmMessage)) return;

        try {
            await onDelete(id);
            toast.success('Membresía Eliminada', {
                duration: 3000,
                position: 'bottom-right',
                style: {
                    background: '#4b5563',   
                    color: '#fff',           
                    padding: '16px',
                    borderRadius: '8px',
                },
            });             
        } catch (error) {
            toast.error(getApiErrorMessage(error, 'Error al eliminar'));
        }
    };

    return (
        <div className="flex justify-center items-center gap-x-4">
            <Link
                to={editPath}
                className="text-green-600 text-2xl p-2 rounded-md hover:scale-110"
            >
                <RiPencilLine />
            </Link>
            <button
                onClick={handleDelete}
                className="cursor-pointer text-red-500 text-xl p-2 rounded-md hover:scale-110"
            >
                <RiDeleteBinLine />
            </button>
        </div>

    );
};
export default ActionButtons;