import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { toast } from "react-hot-toast";
import { createPago } from "../../../api/action/pagoMembresia.api";
import { Input, Label, Button, Select } from "../../../components/ui/index";
import { getApiErrorMessage } from "../../../utils/apiError";

const METODOS_PAGO = [
    { value: "efectivo", label: "Efectivo" },
    { value: "transferencia", label: "Transferencia" },
    { value: "nequi", label: "Nequi" },
] as const;

interface PagoMembresiaModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    membresiaAsignadaId: number;
    totalPrice: number | string;
    totalPagado: number | string;
    saldoPendiente: number | string;
}

const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
};

const PagoMembresiaModal: React.FC<PagoMembresiaModalProps> = ({
    isOpen,
    onClose,
    onSuccess,
    membresiaAsignadaId,
    totalPrice,
    totalPagado,
    saldoPendiente,
}) => {
    const [monto, setMonto] = useState<string>("");
    const [metodoPago, setMetodoPago] = useState<string>("efectivo");
    const [nota, setNota] = useState<string>("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const saldoNum = Number(saldoPendiente);

    // Bloquear scroll del body cuando el modal está abierto (crítico en mobile)
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const montoNum = parseFloat(monto);
        if (isNaN(montoNum) || montoNum <= 0) {
            toast.error("El monto debe ser mayor a cero");
            return;
        }

        if (montoNum > saldoNum) {
            toast.error(`El monto no puede exceder el saldo pendiente (${formatCurrency(saldoNum)})`);
            return;
        }

        setIsSubmitting(true);
        try {
            await createPago(membresiaAsignadaId, {
                monto: montoNum,
                metodo_pago: metodoPago as 'efectivo' | 'transferencia' | 'nequi',
                nota: nota || undefined,
            });
            toast.success("Pago registrado correctamente", {
                duration: 3000,
                position: 'bottom-right',
                style: {
                    background: '#4b5563',
                    color: '#fff',
                    padding: '16px',
                    borderRadius: '8px',
                },
            });
            setMonto("");
            setNota("");
            setMetodoPago("efectivo");
            onSuccess();
            onClose();
        } catch (error: unknown) {
            toast.error(getApiErrorMessage(error, "Error al registrar el pago"));
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-white p-6 rounded-2xl shadow-xl w-full max-w-md mx-4">
                <h3 className="font-bold text-xl mb-6">Registrar Pago</h3>

                {/* Resumen de la membresía */}
                <div className="bg-sky-50 border border-sky-200 p-3 rounded-lg mb-6 space-y-1 text-sm">
                    <div className="flex justify-between">
                        <span className="text-sky-700">Total membresía:</span>
                        <span className="font-semibold">{formatCurrency(Number(totalPrice))}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-sky-700">Total pagado:</span>
                        <span className="font-semibold">{formatCurrency(Number(totalPagado))}</span>
                    </div>
                    <div className="flex justify-between border-t border-sky-200 pt-1">
                        <span className="text-sky-800 font-bold">Saldo pendiente:</span>
                        <span className="font-bold text-sky-800">{formatCurrency(saldoNum)}</span>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Monto */}
                    <div className="relative pt-5">
                        <Input
                            type="number"
                            step="0.01"
                            min="0"
                            placeholder=""
                            value={monto}
                            onChange={(e) => setMonto(e.target.value)}
                            required
                        />
                        <Label>Monto a pagar</Label>
                    </div>

                    {/* Método de pago */}
                    <div className="relative pt-5">
                        <Select
                            value={metodoPago}
                            onChange={(e) => setMetodoPago(e.target.value)}
                        >
                            {METODOS_PAGO.map((mp) => (
                                <option key={mp.value} value={mp.value}>
                                    {mp.label}
                                </option>
                            ))}
                        </Select>
                        <Label>Método de pago</Label>
                    </div>

                    {/* Nota (opcional) */}
                    <div className="relative pt-5">
                        <Input
                            type="text"
                            placeholder=""
                            value={nota}
                            onChange={(e) => setNota(e.target.value)}
                        />
                        <Label>Nota (opcional)</Label>
                    </div>

                    {/* Acciones */}
                    <div className="flex gap-3 justify-end">
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={onClose}
                        >
                            Cancelar
                        </Button>
                        <Button
                            type="submit"
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? "Registrando..." : "Registrar Pago"}
                        </Button>
                    </div>
                </form>
            </div>
        </div>,
        document.body
    );
};
export default PagoMembresiaModal;