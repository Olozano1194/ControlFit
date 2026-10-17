import { useEffect, useId, useRef } from 'react';
import { IoClose } from 'react-icons/io5';

interface ModalWrapperProps {
    onClose: () => void;
    title: string;
    children: React.ReactNode;
}

const FOCUSABLE_SELECTOR =
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

const ModalWrapper = ({ onClose, title, children }: ModalWrapperProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const titleId = useId();

    // Keep the latest onClose without re-running the trap effect on every render
    const onCloseRef = useRef(onClose);
    onCloseRef.current = onClose;

    useEffect(() => {
        const dialog = dialogRef.current;
        if (!dialog) return;

        const previouslyFocused = document.activeElement as HTMLElement | null;
        const getFocusable = () =>
            Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));

        getFocusable()[0]?.focus();

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                event.preventDefault();
                onCloseRef.current();
                return;
            }
            if (event.key !== 'Tab') return;

            const focusable = getFocusable();
            if (focusable.length === 0) return;

            const first = focusable[0];
            const last = focusable[focusable.length - 1];

            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            previouslyFocused?.focus();
        };
    }, []);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby={titleId}
                className="bg-surface-container-lowest rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6 relative max-h-[90vh] overflow-y-auto"
            >
                <div className="flex items-center justify-between mb-6">
                    <h3 id={titleId} className="text-xl font-bold text-on-surface">
                        {title}
                    </h3>
                    <button
                        type="button"
                        onClick={onClose}
                        className="text-secondary cursor-pointer hover:text-on-surface transition-colors"
                        aria-label="Cerrar"
                    >
                        <IoClose size={24} />
                    </button>
                </div>
                {children}
            </div>
        </div>
    );
};
export default ModalWrapper;
