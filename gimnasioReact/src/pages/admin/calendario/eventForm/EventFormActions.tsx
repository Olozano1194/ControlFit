

interface EventFormActionsProps {
    isSubmitting: boolean;
    isEditing: boolean;
    onClose: () => void;
}

const EventFormActions = ({ isSubmitting, isEditing, onClose }: EventFormActionsProps) => (
    <div className = "flex gap-3 pt-4 border-t border-surface-container-high" >
        <button
            type="button"
            onClick={onClose}
            className="flex-1 bg-surface-container-high cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-on-surface transition-colors hover:bg-surface-container-high/80"
        >
            Cancelar
        </button>
        <button
            type="submit"
            disabled={isSubmitting}
            className="flex-1 bg-sky-600 cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-white transition-colors hover:bg-sky-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
            {isSubmitting
            ? 'Guardando...'
            : isEditing
            ? 'Actualizar'
            : 'Crear Evento'}
        </button>
    </div>
);
export default EventFormActions;