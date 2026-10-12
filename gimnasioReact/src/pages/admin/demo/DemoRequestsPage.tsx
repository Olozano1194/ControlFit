import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
// API
import { getDemoRequests, updateDemoRequestEstado, deleteDemoRequest, type DemoRequest } from "../../../api/action/demoRequests.api";
// Components
import HeaderSection from "../../../components/table/section/HeaderSection";
// Icons
import { IoSearch } from "react-icons/io5";
import { MdFitnessCenter } from "react-icons/md";
// List
import TipoEventoList from "./TipoEventoList";
// Modal
import ConfirmationModal from "../../../components/ui/ConfirmationModal";


const DemoRequestsPage = () => {
    const [requests, setRequests] = useState<DemoRequest[]>([]);
    const [filtered, setFiltered] = useState<DemoRequest[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [search, setSearch] = useState('');
    const queryClient = useQueryClient();
    const [loadingIds, setLoadingIds] = useState<Set<number>>(new Set());
    
    // Delete modal state
    const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean; demo: DemoRequest | null }>({
        isOpen: false,
        demo: null,
    });

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

    const { mutate: toggleEstado } = useMutation<DemoRequest, Error, { id: number; estado: 'pendiente' | 'contactado' }>({
        mutationFn: ({ id, estado }) => updateDemoRequestEstado(id, estado),
        onMutate: async ({ id }) => {
            setLoadingIds(prev => new Set(prev).add(id));
        },
        onSuccess: (updatedDemo, { id, estado }) => {
            setLoadingIds(prev => {
                const next = new Set(prev);
                next.delete(id);
                return next;
            });

            queryClient.invalidateQueries({ queryKey: ['demoRequests'] });

            if (estado === 'contactado' && updatedDemo.gym_creado) {
                toast.success(
                    `¡Gimnasio creado! 🎉 Credenciales enviadas a ${updatedDemo.email}. El admin recibirá su contraseña temporal por email.`,
                    { duration: 6000 }
                );
            } else if (estado === 'pendiente' && updatedDemo.gym_creado === null) {
                toast(
                    'Revertido a pendiente. El gimnasio asociado ha sido desactivado. Puede contactar nuevamente al lead.',
                    { icon: '↩️', duration: 5000 }
                );
            } else {
                toast.success(`Estado actualizado: la solicitud ahora está ${estado === 'contactado' ? 'contactada' : 'pendiente'}.`);
            }
        },
        onError: (error: { response?: { data?: Record<string, string[]> }; message?: string }, { id }) => {
            setLoadingIds(prev => {
                const next = new Set(prev);
                next.delete(id);
                return next;
            });

            const response = error?.response?.data;

            if (response?.email && Array.isArray(response.email)) {
                toast.error(response.email[0] || 'Este email ya está registrado. Usá otro email o contactá a soporte.', { duration: 6000 });
                return;
            }

            const detailMsg = response?.detail;
            const genericMsg = Array.isArray(detailMsg) ? detailMsg[0] : (detailMsg as string | undefined);
            toast.error(genericMsg || error.message || 'No se pudo cambiar el estado');
        },
    });

    const handleToggleEstado = (id: number, estadoActual: DemoRequest['estado']) => {
        if (loadingIds.has(id)) return;
        // Only allow toggle for pendiente <-> contactado
        if (estadoActual === 'cancelada') return;
        const nuevoEstado = estadoActual === 'pendiente' ? 'contactado' : 'pendiente';
        toggleEstado({ id, estado: nuevoEstado });
    };

    // Delete mutation
    const { mutate: deleteDemo, isPending: isDeleting } = useMutation<DemoRequest, Error, number>({
        mutationFn: deleteDemoRequest,
        onSuccess: () => {
            setDeleteModal({ isOpen: false, demo: null });
            queryClient.invalidateQueries({ queryKey: ['demoRequests'] });
            toast.success('Solicitud cancelada correctamente');
        },
        onError: (error: { response?: { data?: Record<string, string[]> }; message?: string }) => {
            const response = error?.response?.data;
            const detailMsg = response?.detail;
            const genericMsg = Array.isArray(detailMsg) ? detailMsg[0] : (detailMsg as string | undefined);
            toast.error(genericMsg || error.message || 'No se pudo cancelar la solicitud');
        },
    });

    const handleOpenDeleteModal = (demo: DemoRequest) => {
        setDeleteModal({ isOpen: true, demo });
    };

    const handleConfirmDelete = () => {
        if (deleteModal.demo) {
            deleteDemo(deleteModal.demo.id);
        }
    };    

    const pendientes = requests.filter(r => r.estado === 'pendiente').length;
    const contactados = requests.filter(r => r.estado === 'contactado').length;
    const canceladas = requests.filter(r => r.estado === 'cancelada').length;

    return (
        <main className="bg-surface-container-lowest w-full flex flex-col justify-center items-center gap-y-4 p-4 rounded-xl">
            <HeaderSection title="Solicitudes de" highlight="Demo" />
            {/* Stats rápidas */}
            <section className="w-full grid grid-cols-2 gap-4 md:grid-cols-4">
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
                        <p className="text-2xl font-black text-green-700">{contactados}</p>
                    </div>
                </div>
                <div className="bg-red-50 p-4 rounded-xl flex items-center gap-3">
                    <span className="text-2xl">❌</span>
                    <div>
                        <p className="text-xs text-red-700 uppercase tracking-wide font-semibold">Canceladas</p>
                        <p className="text-2xl font-black text-red-700">{canceladas}</p>
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
                <TipoEventoList
                    requests={filtered}                    
                    handleToggleEstado={handleToggleEstado}
                    loadingIds={loadingIds}
                    handleOpenDeleteModal={handleOpenDeleteModal}
                    isDeleting={isDeleting}                    
                />
            )}
            {/* Delete Confirmation Modal */}
            <ConfirmationModal
                isOpen={deleteModal.isOpen}
                onClose={() => setDeleteModal({ isOpen: false, demo: null })}
                onConfirm={handleConfirmDelete}
                title="Cancelar solicitud"
                message={`¿Estás seguro de que quieres cancelar la solicitud de "${deleteModal.demo?.nombre_gimnasio}"? Esta acción no se puede deshacer.`}
                confirmText="Sí, cancelar"
                cancelText="No, mantener"
                isLoading={isDeleting}
            />
        </main>
    );
};
export default DemoRequestsPage;