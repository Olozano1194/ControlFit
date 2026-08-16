import { useForm } from 'react-hook-form';
import { useParams, useNavigate } from "react-router-dom";
//Estados
import { useEffect } from "react";
//Icons
import { RiLoginBoxLine } from "react-icons/ri";
// sections
import BreadCrumbsSection from "../../../components/form/section/BreadCrumbsSection";
//Mensajes
import { toast } from "react-hot-toast";
//ui
import { Input, Label, Button } from '../../../components/ui/index';
//API
import { createMemberDay, getMember, updateMember } from '../../../api/action/userGymDay.api';
//Models
import { MemberDay } from '../../../model/memberDay.model';


const RegisterMiembroDay = () => {
    const params = useParams<{ id?: string }>();
    const navigate = useNavigate();
    const { register, handleSubmit, formState: { errors }, reset } = useForm<MemberDay>();
    const isEditing = !!params.id;

    const onSubmit = handleSubmit(async (data: MemberDay) => {

        try {
            const requestData = {
                name: data.name,
                lastname: data.lastname,
                phone: data.phone,
                dateInitial: data.dateInitial,
                price: data.price,
            };

            if (params.id) {
                await updateMember(parseInt(params.id), requestData);
                //console.log('Actualizando miembro:', params.id);
                toast.success('Miembro Actualizado', {
                    duration: 3000,
                    position: 'bottom-right',
                    style: {
                        background: '#4b5563',   // Fondo negro
                        color: '#fff',           // Texto blanco
                        padding: '16px',
                        borderRadius: '8px',
                    },

                });
            } else {
                await createMemberDay(requestData);//console.log('Respuesta del servidor:',rest.data);            
                reset();
                toast.success('Miembro Creado', {
                    duration: 3000,
                    position: 'bottom-right',
                    style: {
                        background: '#4b5563',   // Fondo negro
                        color: '#fff',           // Texto blanco
                        padding: '16px',
                        borderRadius: '8px',
                    },

                });
            }
            navigate('/dashboard/miembros-day');


        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Error al registrar el miembro diario';
            toast.error(errorMessage, {
                duration: 3000,
                position: 'bottom-right',
            });
        }

    });

    useEffect(() => {
        const axiosUserData = async () => {
            try {
                if (params.id) {
                    const response = await getMember(parseInt(params.id));

                    //formateamos la fecha antes de pasarla al formulario
                    if (response.dateInitial) {
                        response.dateInitial = formatDate(response.dateInitial);
                    }

                    reset(response);
                }
            } catch (error) {
                console.error('Error al obtener el miembro', error);
            }
        }
        axiosUserData();
    }, [params.id, reset]);

    const formatDate = (date: string): string => {
        if (!date) return ''; // Retorna un valor vacío si la fecha es undefined o null
        try {
            const [day, month, year] = date.split('-');
            return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        } catch (error) {
            console.error('Error al formatear la fecha:', error);
            return '';
        }
    };

    return (
        <main className="max-w-7xl mx-auto p-6 lg:p-10">
            <BreadCrumbsSection
                isEditing={isEditing}
                title="Registro de Atletas Diarios"
                description="Ingrese los datos del nuevo atleta con acceso por día"
                entityName="este atleta diario"
            />
            <section className="gap-8 grid grid-cols-1 lg:grid-cols-12">
                <div className="space-y-8 md:col-span-6 lg:col-span-8 xl:col-span-11">
                    <section className="bg-surface-container-lowest overflow-hidden p-8 relative rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
                        <div className="absolute p-4 right-0 top-0">
                            <span className="font-black select-none text-[60px] text-slate-50">
                                Identificación
                            </span>
                        </div>
                        <h4 className="font-bold flex gap-2 items-center mb-10 relative text-xl">Información Personal</h4>
                        <form onSubmit={onSubmit} className="relative space-y-10 z-10">
                            <section className='gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2'>
                                {/* Name */}
                                <div className="relative pt-5">
                                    <Input
                                        type="text"
                                        placeholder=""
                                        {...register('name', {
                                            required: {
                                                value: true,
                                                message: 'Nombre requerido'
                                            },
                                            minLength: {
                                                value: 4,
                                                message: 'El nombre debe tener como minimo 4 letras'
                                            },
                                            maxLength: {
                                                value: 20,
                                                message: 'El nombre debe tener como maximo 20 letras'
                                            },
                                            pattern: {
                                                value: /^[a-zA-Z]+$/,
                                                message: 'Nombre invalido'
                                            },
                                        })}
                                    />
                                    <Label>
                                        Nombres
                                    </Label>
                                    {
                                        errors.name && <span className='text-red-500 text-sm'>{errors.name.message}</span>
                                    }
                                </div>
                                {/* LastName */}
                                <div className="relative pt-5">
                                    <Input
                                        type="text"
                                        placeholder=""
                                        {...register('lastname', {
                                            required: {
                                                value: true,
                                                message: 'Apellido requerido'
                                            },
                                            minLength: {
                                                value: 5,
                                                message: 'El apellido debe tener como minimo 5 letras'
                                            },
                                            maxLength: {
                                                value: 20,
                                                message: 'El apellido debe tener como maximo 20 letras'
                                            },
                                            pattern: {
                                                value: /^[a-zA-Z]+$/,
                                                message: 'Apellido invalido'
                                            },
                                        })}
                                    />
                                    <Label>
                                        Apellidos
                                    </Label>
                                    {
                                        errors.lastname && <span className='text-red-500 text-sm'>{errors.lastname.message}</span>
                                    }
                                </div>
                                {/* Phone */}
                                <div className="relative pt-5">
                                    <Input
                                        type="tel"
                                        placeholder=""
                                        {...register('phone', {
                                            required: {
                                                value: true,
                                                message: 'Celular requerido'
                                            },
                                            minLength: {
                                                value: 10,
                                                message: 'El Celular debe tener como minimo 10 números'
                                            },
                                            maxLength: {
                                                value: 10,
                                                message: 'El Celular debe tener como maximo 10 número'
                                            },
                                            pattern: {
                                                value: /^[0-9]+$/,
                                                message: 'Numero celular invalido'
                                            },
                                        })}
                                    />
                                    <Label>
                                        Celular
                                    </Label>
                                    {
                                        errors.phone && <span className='text-red-500 text-sm'>{errors.phone.message}</span>
                                    }
                                </div>
                                {/* Date Initial */}
                                <div className="relative pt-5">
                                    <Input
                                        type="date"
                                        placeholder=""
                                        {...register('dateInitial', {
                                            required: {
                                                value: true,
                                                message: 'Fecha requerido'
                                            },
                                        })}
                                    />
                                    <Label>
                                        Fecha Inicial
                                    </Label>
                                    {
                                        errors.dateInitial && <span className='text-red-500 text-sm'>{errors.dateInitial.message}</span>
                                    }
                                </div>
                                {/* Price */}
                                <div className="relative pt-5">
                                    <Input
                                        type="text"
                                        placeholder=""
                                        {...register('price', {
                                            required: {
                                                value: true,
                                                message: 'Precio requerido'
                                            },
                                            pattern: {
                                                value: /^[0-9]+$/,
                                                message: 'Precio invalido'
                                            },
                                        })}
                                    />
                                    <Label>
                                        Precio
                                    </Label>
                                    {
                                        errors.price && <span className='text-red-500 text-sm'>{errors.price.message}</span>
                                    }
                                </div>                                
                            </section>
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
}
export default RegisterMiembroDay;