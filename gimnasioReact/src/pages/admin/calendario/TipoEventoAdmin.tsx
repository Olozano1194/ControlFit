import { useCallback, useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import { getTiposEvento } from '../../../api/action/calendario.api';
import { TipoEvento } from '../../../model/calendario.model';
import TipoEventoList from './TipoEventoList';
import TipoEventoForm from './TipoEventoForm';

// ─── Componente ──────────────────────────────────────────────────────────────

const TipoEventoAdmin = () => {
    const [tipos, setTipos] = useState<TipoEvento[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingTipo, setEditingTipo] = useState<TipoEvento | null>(null);

    // ── Carga de datos ───────────────────────────────────────────────────────

    const fetchTipos = useCallback(async () => {
        setIsLoading(true);
        try {
            const data = await getTiposEvento();
            setTipos(data);
        } catch (error) {
            const msg =
                error instanceof Error
                    ? error.message
                    : 'Error al cargar tipos de evento';
            toast.error(msg);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTipos();
    }, [fetchTipos]);

    // ── Handlers ─────────────────────────────────────────────────────────────

    const handleCreate = useCallback(() => {
        setEditingTipo(null);
        setIsFormOpen(true);
    }, []);

    const handleEdit = useCallback((tipo: TipoEvento) => {
        setEditingTipo(tipo);
        setIsFormOpen(true);
    }, []);

    const handleCloseForm = useCallback(() => {
        setIsFormOpen(false);
        setEditingTipo(null);
    }, []);

    const handleSuccess = useCallback(() => {
        fetchTipos();
    }, [fetchTipos]);

    // ── Render ───────────────────────────────────────────────────────────────

    return (
        <section>
            {isLoading ? (
                <div className="text-center py-8 text-secondary">
                    Cargando tipos de evento...
                </div>
            ) : (
                <TipoEventoList
                    tipos={tipos}
                    onEdit={handleEdit}
                    onCreate={handleCreate}
                    onRefresh={fetchTipos}
                />
            )}

            <TipoEventoForm
                isOpen={isFormOpen}
                onClose={handleCloseForm}
                tipo={editingTipo}
                onSuccess={handleSuccess}
            />
        </section>
    );
};

export default TipoEventoAdmin;