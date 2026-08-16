import { useForm } from 'react-hook-form';
import { useParams, useNavigate } from "react-router-dom";
//Estados
import { useEffect, useState, useMemo } from "react";
//Icons
import { RiLoginBoxLine, RiUserAddLine } from "react-icons/ri";
import { MdPeople } from "react-icons/md";
// sections
import BreadCrumbsSection from "../../../components/form/section/BreadCrumbsSection";
//Mensajes
import { toast } from "react-hot-toast";
//ui
import { Input, Label, Button, Select } from '../../../components/ui/index';
//API
//MemberShips
import { getMemberList } from '../../../api/action/memberShips.api';
//Member
import { getMembers, createMember } from '../../../api/action/userGym.api';
//Asignación Membresías
import { createAsignarMemberShips, updateAsignarMemberShips, getAsignarMemberShips } from '../../../api/action/asignarMemberShips.api';
//Models
import { Membresia } from '../../../model/memberShips.model';
import { Miembro } from '../../../model/member.model';
import { CreateAsignarMemberShipsDto } from '../../../model/dto/asignarMemberShips.dto';
import { CreateMemberDto } from '../../../model/dto/member.dto';

const DISCOUNT_TIERS: Record<number, number> = {
    1: 0, 2: 0, 3: 5, 6: 10, 12: 20
};

interface FormData {
    miembro: string;
    membresia: string;
    multiplier: string;
    dateInitial: string;
    // Campos para nuevo miembro
    nuevoName: string;
    nuevoLastname: string;
    nuevoPhone: string;
    nuevoAddress: string;
}

type ModoFormulario = 'existente' | 'nuevo';

const MemberShipsForm = () => {
    const [modo, setModo] = useState<ModoFormulario>('existente');
    const [selectedMembresia, setSelectedMembresia] = useState<Membresia | null>(null);
    const [multiplier, setMultiplier] = useState<number>(1);
    const [discountPercent, setDiscountPercent] = useState<number>(0);
    const [membresias, setMembresias] = useState<Membresia[]>([]);
    const [miembros, setMiembros] = useState<Miembro[]>([]);
    const params = useParams<{ id?: string }>();
    const isEditing = !!params.id;
    const navigate = useNavigate();
    const { register, handleSubmit, formState: { errors }, reset, watch } = useForm<FormData>({
        shouldUnregister: true,
    });
    const dateInitial = watch('dateInitial');

    const formatCurrency = (amount: number): string => {
        return new Intl.NumberFormat("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount);
    };

    // Precio estimado: base * multiplier * (1 - discount/100)
    const estimatedPrice = useMemo(() => {
        if (!selectedMembresia) return 0;
        const base = Number(selectedMembresia.price);
        return base * multiplier * (1 - discountPercent / 100);
    }, [selectedMembresia, multiplier, discountPercent]);

    // Días totales
    const totalDays = useMemo(() => {
        if (!selectedMembresia) return 0;
        return selectedMembresia.duration * multiplier;
    }, [selectedMembresia, multiplier]);

    // Fecha final estimada
    const estimatedDateFinal = useMemo(() => {
        if (!dateInitial || !selectedMembresia) return '';
        const initial = new Date(dateInitial);
        const final = new Date(initial);
        final.setDate(final.getDate() + selectedMembresia.duration * multiplier);
        return final.toLocaleDateString('es-CO', {
            year: 'numeric', month: '2-digit', day: '2-digit'
        });
    }, [dateInitial, selectedMembresia, multiplier]);

    // Limpiar errores al cambiar de modo (existente ↔ nuevo)
    useEffect(() => {
        reset(undefined, { keepValues: false });
    }, [modo, reset]);

    // Auto-sugerir descuento cuando cambia multiplier
    const handleMultiplierChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const val = parseInt(e.target.value);
        setMultiplier(val);
        setDiscountPercent(DISCOUNT_TIERS[val] ?? 0);
    };

    const onSubmit = handleSubmit(async (data: FormData) => {
        try {
            const membresiaId = parseInt(data.membresia);
            if (isNaN(membresiaId)) {
                toast.error('Por favor, selecciona una membresía');
                return;
            }

            const selectMembresia = membresias.find((m) => m.id === membresiaId);
            if (!selectMembresia) {
                toast.error('Membresía no encontrada');
                return;
            }

            const initialDate = new Date(data.dateInitial);
            const finalDate = new Date(initialDate);
            finalDate.setDate(finalDate.getDate() + selectMembresia.duration * multiplier);

            const dateInitialStr = initialDate.toISOString().split('T')[0];
            const dateFinal = finalDate.toISOString().split('T')[0];

            if (modo === 'nuevo' && !params.id) {
                // === CREAR MIEMBRO NUEVO + ASIGNAR MEMBRESÍA ===
                if (!data.nuevoName || !data.nuevoLastname) {
                    toast.error('Nombre y apellido son requeridos');
                    return;
                }

                const memberData: CreateMemberDto = {
                    name: data.nuevoName,
                    lastname: data.nuevoLastname,
                    phone: data.nuevoPhone || '',
                    address: data.nuevoAddress || '',
                    initial_membership_id: membresiaId,
                    dateInitial: dateInitialStr,
                    multiplier: multiplier,
                    discount_percent: discountPercent,
                };

                await createMember(memberData);
                toast.success('Miembro creado y membresía asignada', {
                    duration: 3000,
                    position: 'bottom-right',
                    style: { background: '#4b5563', color: '#fff', padding: '16px', borderRadius: '8px' },
                });
                reset();
                setMultiplier(1);
                setDiscountPercent(0);
                navigate('/dashboard/miembros');
            } else {
                // === ASIGNAR A MIEMBRO EXISTENTE ===
                const miembroId = parseInt(data.miembro);
                if (isNaN(miembroId)) {
                    toast.error('Por favor, selecciona un miembro');
                    return;
                }

                const requestData: CreateAsignarMemberShipsDto = {
                    miembro: miembroId,
                    membresia: membresiaId,
                    multiplier: multiplier,
                    dateInitial: dateInitialStr,
                    dateFinal: dateFinal,
                    discount_percent: discountPercent,
                };

                if (params.id) {
                    await updateAsignarMemberShips(parseInt(params.id), requestData);
                    toast.success('Asignación de Membresía Actualizada', {
                        duration: 3000,
                        position: 'bottom-right',
                        style: { background: '#4b5563', color: '#fff', padding: '16px', borderRadius: '8px' },
                    });
                } else {
                    await createAsignarMemberShips(requestData);
                    toast.success('Asignación de Membresía Creada', {
                        duration: 3000,
                        position: 'bottom-right',
                        style: { background: '#4b5563', color: '#fff', padding: '16px', borderRadius: '8px' },
                    });
                    reset();
                    setMultiplier(1);
                    setDiscountPercent(0);
                }
                navigate('/dashboard/asignar-membresia-list');
            }
        } catch (error) {
            if (error instanceof Error) {
                console.error('Error detallado:', error);
                toast.error(`Error: ${error.message}`);
            } else {
                console.error('Error desconocido:', error);
                toast.error('Error desconocido al procesar la solicitud');
            }
        }
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const responseMemberShips: Membresia[] = await getMemberList();
                const responseMembers: Miembro[] = await getMembers();

                setMembresias(responseMemberShips);
                setMiembros(responseMembers);

                if (params.id) {
                    const responseAsignacion = await getAsignarMemberShips(parseInt(params.id));
                    if (responseAsignacion.dateInitial && responseAsignacion.dateFinal) {
                        responseAsignacion.dateInitial = formatDate(responseAsignacion.dateInitial);
                        responseAsignacion.dateFinal = formatDate(responseAsignacion.dateFinal);
                    }
                    const mult = Number(responseAsignacion.multiplier) || 1;
                    const disc = Number(responseAsignacion.discount_percent) || 0;
                    setMultiplier(mult);
                    setDiscountPercent(disc);

                    reset({
                        miembro: responseAsignacion.miembro.toString(),
                        membresia: responseAsignacion.membresia.toString(),
                        multiplier: responseAsignacion.multiplier?.toString() ?? '1',
                        dateInitial: responseAsignacion.dateInitial,
                    });
                }
            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Error al cargar los datos';
                toast.error(errorMessage);
            }
        };

        fetchData();
    }, [params.id, reset]);

    const formatDate = (date: string): string => {
        if (!date) return '';
        try {
            const [day, month, year] = date.split('-');
            return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        } catch (error) {
            console.error('Error al formatear la fecha:', error);
            return '';
        }
    };

    const handleMemberShipsChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const membresiaId = parseInt(event.target.value);
        const found = membresias.find((m) => m.id === membresiaId);
        setSelectedMembresia(found ?? null);
        setMultiplier(1);
        setDiscountPercent(0);
    };

    // Generate multiplier options from 1..max_multiplier (dynamic per membership)
    const multiplierOptions = selectedMembresia
        ? Array.from({ length: selectedMembresia.max_multiplier }, (_, i) => i + 1)
        : [];
    const showMultiplier = selectedMembresia && selectedMembresia.max_multiplier > 1;

    return (
        <main className="max-w-7xl mx-auto p-6 lg:p-10">
            <BreadCrumbsSection
                isEditing={isEditing}
                title="Asignar Membresías"
                description="Asocie membresías a los atletas registrados en el sistema"
                entityName="esta asignación"
            />
            <section className="gap-8 grid grid-cols-1 lg:grid-cols-12">
                <div className="space-y-8 md:col-span-6 lg:col-span-8 xl:col-span-11">
                    <section className="bg-surface-container-lowest overflow-hidden p-8 relative rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
                        <div className="absolute p-4 right-0 top-0">
                            <span className="font-black select-none text-[60px] text-slate-50">
                                Identificación
                            </span>
                        </div>
                        <h4 className="font-bold flex gap-2 items-center mb-10 relative text-xl">
                            {modo === 'nuevo' ? 'Información Personal' : 'Asignar Membresía'}
                        </h4>
                        <form onSubmit={onSubmit} className="relative space-y-10 z-10">
                            {/* Toggle: existente vs nuevo miembro */}
                            {!params.id && (
                                <div className="flex gap-2 mb-2">
                                    <button
                                        type="button"
                                        onClick={() => setModo('existente')}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-semibold transition-all ${
                                            modo === 'existente'
                                                ? 'bg-primary text-white shadow-md'
                                                : 'bg-surface-container-high text-on-surface/70 hover:bg-surface-container-high/80'
                                        }`}
                                    >
                                        <MdPeople className="text-lg" />
                                        Miembro existente
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setModo('nuevo')}
                                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-semibold transition-all ${
                                            modo === 'nuevo'
                                                ? 'bg-primary text-white shadow-md'
                                                : 'bg-surface-container-high text-on-surface/70 hover:bg-surface-container-high/80'
                                        }`}
                                    >
                                        <RiUserAddLine className="text-lg" />
                                        Nuevo miembro
                                    </button>
                                </div>
                            )}

                            {modo === 'existente' ? (
                                /* Seleccionar miembro existente */
                                <div className="relative pt-5">
                                    <Select
                                        {...register('miembro', {
                                            required: {
                                                value: true,
                                                message: 'Nombre requerido'
                                            },
                                        })}
                                    >
                                        <option value="">Seleccione un Miembro</option>
                                        {miembros.map((miembro) => (
                                            <option key={miembro.id} value={miembro.id?.toString()}>
                                                {miembro.name} {miembro.lastname}
                                            </option>
                                        ))}
                                    </Select>
                                    <Label>
                                        Miembro
                                    </Label>
                                    {errors.miembro && <span className='text-red-500 text-sm'>{errors.miembro.message}</span>}
                                </div>
                            ) : (
                                /* Datos del nuevo miembro — estilo anterior */
                                <section className="gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2">
                                    <div className="relative pt-5">
                                        <Input
                                            type="text"
                                            placeholder=""
                                            {...register('nuevoName', {
                                                required: { value: true, message: 'Nombre requerido' },
                                                minLength: { value: 4, message: 'El nombre debe tener como mínimo 4 letras' },
                                                maxLength: { value: 20, message: 'El nombre debe tener como máximo 20 letras' },
                                                pattern: { value: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, message: 'Nombre inválido' },
                                            })}
                                        />
                                        <Label>Nombres *</Label>
                                        {errors.nuevoName && <span className='text-red-500 text-sm'>{errors.nuevoName.message}</span>}
                                    </div>
                                    <div className="relative pt-5">
                                        <Input
                                            type="text"
                                            placeholder=""
                                            {...register('nuevoLastname', {
                                                required: { value: true, message: 'Apellido requerido' },
                                                minLength: { value: 5, message: 'El apellido debe tener como mínimo 5 letras' },
                                                maxLength: { value: 20, message: 'El apellido debe tener como máximo 20 letras' },
                                                pattern: { value: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, message: 'Apellido inválido' },
                                            })}
                                        />
                                        <Label>Apellidos *</Label>
                                        {errors.nuevoLastname && <span className='text-red-500 text-sm'>{errors.nuevoLastname.message}</span>}
                                    </div>
                                    <div className="relative pt-5">
                                        <Input
                                            type="tel"
                                            placeholder=""
                                            {...register('nuevoPhone', {
                                                required: { value: true, message: 'Celular requerido' },
                                                minLength: { value: 10, message: 'El celular debe tener como mínimo 10 números' },
                                                maxLength: { value: 10, message: 'El celular debe tener como máximo 10 números' },
                                                pattern: { value: /^[0-9]+$/, message: 'Número celular inválido' },
                                            })}
                                        />
                                        <Label>Celular *</Label>
                                        {errors.nuevoPhone && <span className='text-red-500 text-sm'>{errors.nuevoPhone.message}</span>}
                                    </div>
                                    <div className="relative pt-5">
                                        <Input
                                            type="text"
                                            placeholder=""
                                            {...register('nuevoAddress', {
                                                maxLength: { value: 50, message: 'La dirección debe tener como máximo 50 caracteres' },
                                            })}
                                        />
                                        <Label>Dirección</Label>
                                        {errors.nuevoAddress && <span className='text-red-500 text-sm'>{errors.nuevoAddress.message}</span>}
                                    </div>
                                </section>
                            )}

                            {/* Membresía — siempre visible */}
                            <section className="gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2">
                                <div className="relative pt-5">
                                    <Select
                                        {...register('membresia', {
                                            required: {
                                                value: true,
                                                message: 'Membresía requerida'
                                            },
                                        })}
                                        onChange={(e) => {
                                            register('membresia').onChange(e);
                                            handleMemberShipsChange(e);
                                        }}
                                    >
                                        <option value="">Seleccione una Membresía</option>
                                        {membresias.filter(m => m.is_active !== false).map((membresia) => (
                                            <option key={membresia.id} value={membresia.id?.toString()}>
                                                {membresia.name} - ${membresia.price}
                                            </option>
                                        ))}
                                    </Select>
                                    <Label>Membresía</Label>
                                    {errors.membresia && <span className='text-red-500 text-sm'>{errors.membresia.message}</span>}
                                </div>
                                <div className="relative pt-5">
                                    <Input
                                        type="date"
                                        placeholder=""
                                        {...register('dateInitial', {
                                            required: {
                                                value: true,
                                                message: 'Fecha requerida'
                                            },
                                        })}
                                    />
                                    <Label>Fecha Inicial</Label>
                                    {errors.dateInitial && <span className='text-red-500 text-sm'>{errors.dateInitial.message}</span>}
                                </div>
                            </section>

                            {/* Periodos y Descuento — solo si hay membresía seleccionada */}
                            {showMultiplier && (
                                <section className="gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2">
                                    <div className="relative pt-5">
                                        <Select
                                            value={multiplier}
                                            onChange={handleMultiplierChange}
                                        >
                                            {multiplierOptions.map((val) => (
                                                <option key={val} value={val}>
                                                    {val} {val === 1 ? 'mes' : 'meses'}
                                                </option>
                                            ))}
                                        </Select>
                                        <Label>Periodos</Label>
                                    </div>
                                    <div className="relative pt-5">
                                        <Input
                                            type="number"
                                            value={discountPercent}
                                            onChange={(e) => setDiscountPercent(Number(e.target.value) || 0)}
                                            min={0}
                                            max={100}
                                            step={0.5}
                                        />
                                        <Label>Descuento (%)</Label>
                                    </div>
                                </section>
                            )}

                            {/* Resumen del pago — estilo anterior */}
                            {selectedMembresia && Number(selectedMembresia.price) > 0 && (
                                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                                    <p className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-2">Resumen del pago</p>
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span>Valor unitario:</span>
                                            <span>{formatCurrency(Number(selectedMembresia.price))}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Periodos:</span>
                                            <span>{multiplier}x</span>
                                        </div>
                                        {discountPercent > 0 && (
                                            <div className="flex justify-between text-green-600">
                                                <span>Descuento ({discountPercent}%):</span>
                                                <span>-{formatCurrency(Number(selectedMembresia.price) * multiplier * discountPercent / 100)}</span>
                                            </div>
                                        )}
                                        <div className="flex justify-between font-bold text-base pt-2 border-t border-gray-200 mt-2">
                                            <span>Total a pagar:</span>
                                            <span>{formatCurrency(estimatedPrice)}</span>
                                        </div>
                                        {totalDays > 0 && (
                                            <div className="flex justify-between text-gray-500 text-xs pt-1">
                                                <span>Días totales:</span>
                                                <span>{totalDays} días</span>
                                            </div>
                                        )}
                                        {estimatedDateFinal && (
                                            <div className="flex justify-between text-gray-500 text-xs pt-1">
                                                <span>Fecha final aprox.:</span>
                                                <span>{estimatedDateFinal}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* btn Register */}
                            <div className="w-full flex items-center justify-center">
                                <Button type="submit">
                                    {params.id ? 'Actualizar' : 'Registrar'} <RiLoginBoxLine className='text-surface-container-lowest' />
                                </Button>
                            </div>
                        </form>
                    </section>
                </div>
            </section>
        </main>
    );
};
export default MemberShipsForm;