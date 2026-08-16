import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from "react-router-dom";
//Icons
import { RiLoginBoxLine } from "react-icons/ri";
//Mensajes
import { toast } from 'react-hot-toast';
//ui
import { Input, Label, Button, Select } from '../../components/ui/index';
// sections
import BreadCrumbsSection from "../../components/form/section/BreadCrumbsSection";
//api
import { CreateUsers } from '../../api/users/users.api';
//Models
import { User } from '../../model/user.model';


const Register = () => {
    const { register, handleSubmit, formState: { errors }, watch, reset } = useForm<User>();
    const navigate = useNavigate();
    const params = useParams<{ id?: string }>();
    const isEditing = !!params.id;

    const onSubmit = handleSubmit(async (data: User) => {
        //console.log('Form data:', data);
        try {
            const requestData = {
                name: data.name,
                lastname: data.lastname,
                email: data.email,
                password: data.password,
                roles: data.roles,
            };

            await CreateUsers(requestData);
            //console.log('Respuesta del servidor:',rest.data);            
            reset();
            toast.success('Usuario Creado');
            navigate('/dashboard/listUser');

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Error al registrar el miembro';
            toast.error(errorMessage);
        }

    });

    return (
        <main className="max-w-7xl mx-auto p-6 lg:p-10">
            <BreadCrumbsSection 
                isEditing={isEditing}
                title="Registro de Usuarios"
                description="Ingrese los datos del nuevo usuario del sistema"
                entityName="este usuario"
            />
            <section className="gap-8 grid grid-cols-1 lg:grid-cols-12">
                <div className="space-y-8 md:col-span-6 lg:col-span-8 xl:col-span-11">
                    <section className="bg-surface-container-lowest overflow-hidden p-8 relative rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
                        <div className="absolute p-4 right-0 top-0">
                            <span className="font-black select-none text-[60px] text-slate-50">
                                Identificación
                            </span>
                        </div>
                        <h4 className="font-bold flex gap-2 items-center mb-10 relative text-xl">Credenciales de Usuario</h4>
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
                                {/* Roles */}
                                <div className="relative pt-5">
                                    <Select
                                        {...register('roles', {
                                            required: {
                                                value: true,
                                                message: 'Roles requerido'
                                            },
                                        })}
                                    >
                                        <option value="">Escoge un rol</option>
                                        <option value="admin">Administrador</option>
                                        <option value="recepcion">Recepcionista</option>
                                    </Select>
                                    <Label>
                                        Roles
                                    </Label>
                                    {
                                        errors.roles && <span className='text-red-500 text-sm'>{errors.roles.message}</span>
                                    }
                                </div>
                                {/* Email */}
                                <div className="relative pt-5">
                                    <Input
                                        type="text"
                                        placeholder=""
                                        {...register('email', {
                                            required: {
                                                value: true,
                                                message: 'Correo requerido'
                                            },
                                            pattern: {
                                                value: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
                                                message: 'Correo invalido'
                                            },
                                        })}
                                    />
                                    <Label>
                                        Email
                                    </Label>
                                    {
                                        errors.email && <span className='text-red-500 text-sm'>{errors.email.message}</span>
                                    }
                                </div>
                                {/* Password */}
                                <div className="relative pt-5">
                                    <Input
                                        type="password"
                                        placeholder=""
                                        {...register('password', {
                                            required: {
                                                value: true,
                                                message: 'Contraseña requerido'
                                            },
                                            minLength: {
                                                value: 5,
                                                message: 'La contraseña debe tener al menos 5 caracteres'
                                            },
                                            maxLength: {
                                                value: 20,
                                                message: 'La contraseña debe tener como maximo 20 caracteres'
                                            },
                                        })}
                                    />
                                    <Label>
                                        Contraseña
                                    </Label>
                                    {
                                        errors.password && <span className='text-red-500 text-sm'>{errors.password.message}</span>
                                    }
                                </div>
                                {/* RepeatPassword */}
                                <div className="relative pt-5">
                                    <Input
                                        type="password"
                                        placeholder=""
                                        {...register('repeatPass', {
                                            required: {
                                                value: true,
                                                message: 'Confirmar contraseña requerido'
                                            },
                                            validate: (value) => value === watch('password') || 'Las contraseñas no coinciden',
                                        })}
                                    />
                                    <Label>
                                        Repetir Contraseña
                                    </Label>
                                    {
                                        errors.repeatPass && <span className='text-red-500 text-sm'>{errors.repeatPass.message}</span>
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
export default Register;