//hooks
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
//Context
import { useAuth } from "../../../../context/useAuth";
//Api
import { getUserProfile, updateUser } from "../../../../api/users/users.api";
//icons
import { RiEdit2Line } from "react-icons/ri";
//models
import { User } from "../../../../model/user.model";
// sections
import BreadCrumbsSection from "../../../../components/form/section/BreadCrumbsSection";
//Mensajes
import { toast } from "react-hot-toast";
//ui
import { Input, Label, Button, Select } from '../../../../components/ui/index';


interface FormData {
    name: string;
    lastname: string;
    roles: string;
    avatar: string | File | undefined;
    id: string;
};

const Profile = () => {
    const { updateUserData } = useAuth();
    const params = useParams<{ id?: string }>();
    const isEditing = !!params.id;
    const [, setUser] = useState<User>();
    const [editingUser, seteditingUser] = useState(false);
    const [formData, setFormData] = useState<FormData>({
        name: '',
        lastname: '',
        roles: '',
        avatar: undefined,
        id: ''
    });

    //hook para vizualizar los datos de la bd
    useEffect(() => {
        const fetchData = async () => {
            try {
                const userData = await getUserProfile();
                //console.log('Respuesta del servidor:', userData);

                const avatarUrl = userData.user.avatar instanceof File ? URL.createObjectURL(userData.user.avatar) : userData.user.avatar ?? '';

                const roles = Array.isArray(userData.user.roles) ? userData.user.roles[0] ?? '' : userData.user.roles ?? '';

                if (userData && userData.user) {
                    setUser(userData.user);
                    //console.log('Datos de usuario:', userData.user);
                    setFormData({
                        name: userData.user.name,
                        lastname: userData.user.lastname,
                        roles: roles,
                        avatar: avatarUrl,
                        id: userData.user.id.toString(),
                    });
                    //setLoading(false);

                } else {
                    console.log('Datos de usuario faltantes:', userData);
                }

            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Error al mostrar el perfil del usuario';
                toast.error(errorMessage, {
                    duration: 3000,
                    position: 'bottom-right',
                });
            }
        };
        fetchData();
    }, []);

    //Función donde manejamos los cambios en el formulario
    const handleChanges = (data: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>): void => {
        const { name, value } = data.target;
        setFormData((prevData) => ({
            ...prevData,
            [name]: value
        }));
    };

    //Función para las imagenes
    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files ? event.target.files[0] : null;
        if (file) {
            setFormData(prev => ({
                ...prev,
                avatar: file  // Guardamos el archivo directamente
            }));
        }
    };

    //Función para guardar los cambios en el formulario
    const handleSave = async () => {
        try {
            // const roles = Array.isArray(formData.roles) ? formData.roles : formData.roles;
            // Enviamos solo los campos necesarios
            const dataToUpdate = {
                name: formData.name,
                lastname: formData.lastname,
                // roles: roles,
                avatar: formData.avatar instanceof File ? formData.avatar : undefined,
            };

            //console.log('Datos a actualizar', dataToUpdate);
            const updatedProfile = await updateUser(parseInt(formData.id), dataToUpdate);
            toast.success('Usuario Actualizado');

            if (updatedProfile) {
                setUser(updatedProfile);
                seteditingUser(false); // Desactivar modo edición
                // Actualizar el formData con los nuevos datos
                setFormData(prev => ({
                    ...prev,
                    name: updatedProfile.name,
                    lastname: updatedProfile.lastname,
                    // roles: updatedProfile.roles,
                    avatar: updatedProfile.avatar,
                }));

                // Actualizar el contexto de autenticación (Header se actualiza en tiempo real)
                const avatarUrl = updatedProfile.avatar instanceof File
                    ? URL.createObjectURL(updatedProfile.avatar)
                    : updatedProfile.avatar ?? '';

                updateUserData({
                    name: updatedProfile.name,
                    lastname: updatedProfile.lastname,
                    avatar: avatarUrl,
                });
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Error al actualizar el Usuario';
            toast.error(errorMessage);
        }
    };

    const avatarSrc = formData.avatar
        ? (formData.avatar instanceof File
            ? URL.createObjectURL(formData.avatar)
            : formData.avatar.startsWith('http')
                ? formData.avatar
                : `${import.meta.env.MODE === 'development' ? import.meta.env.VITE_API_URL_DEV : import.meta.env.VITE_API_URL_PROD}${formData.avatar}`)
        : 'https://img.freepik.com/foto-gratis/negocios-finanzas-empleo-concepto-mujeres-emprendedoras-exitosas-joven-empresaria-segura-anteojos-mostrando-gesto-pulga-arriba-sostenga-computadora-portatil-garantice-mejor-calidad-servicio_1258-59118.jpg';

    return (
        <section className="max-w-7xl mx-auto p-6 lg:p-10">
            <BreadCrumbsSection
                isEditing={isEditing}
                title="Perfil del Usuario"
                description="Aquí puedes ver y editar la información de tu perfil. Asegúrate de mantener tus datos actualizados para una mejor experiencia en nuestra plataforma."
                entityName="este atleta mensual"
            />
            <section className="gap-8 grid grid-cols-1 lg:grid-cols-12">
                <div className="space-y-8 md:col-span-6 lg:col-span-8 xl:col-span-11">
                    <section className="bg-surface-container-lowest overflow-hidden p-8 relative rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
                        <div className="absolute p-4 right-0 top-0">
                            <span className="font-black select-none text-[35px] text-slate-50 md:text-[60px]">
                                Identificación
                            </span>
                        </div>
                        <h4 className="font-bold flex gap-2 items-center mb-10 relative text-xl">Información Personal</h4>
                        <form className="relative space-y-10 z-10">
                            <section className='gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2'>
                                {/* Avatar */}
                                <div className="flex items-center relative w-full md:col-span-2">
                                    <div className="w-1/4">
                                        <p>Avatar</p>
                                    </div>
                                    <div className="flex-1">
                                        <div className="relative mb-2">
                                            <img src={avatarSrc}
                                                alt="Avatar"
                                                className="w-28 h-28 object-cover rounded-lg"
                                            />
                                            {editingUser && (
                                                <>
                                                    <label htmlFor="avatar" className="absolute bg-surface-container-lowest p-2 rounded-full hover:cursor-pointer -top-2 left-24"><RiEdit2Line className='text-text-primary' /></label>
                                                    <input type="file" name="avatar" id="avatar" className="hidden"
                                                        // {...register("avatar")} 
                                                        accept='image/*'
                                                        onChange={handleFileChange}
                                                    />
                                                </>
                                            )}
                                        </div>
                                        <p className="text-gray-500 text-sm mb-5">Allowed file types: png, jpg, jpeg.</p>
                                    </div>
                                </div>
                                {/* Name */}
                                <div className="relative pt-5">
                                    <Input
                                        type="text"
                                        placeholder=""
                                        id="name"
                                        name='name'
                                        value={formData.name}
                                        onChange={handleChanges}
                                        disabled={!editingUser}
                                    />
                                    <Label>
                                        Nombres
                                    </Label>
                                </div>
                                {/* LastName */}
                                <div className="relative pt-5">
                                    <Input
                                        type="text"
                                        placeholder=""
                                        id="lastname"
                                        name='lastname'
                                        value={formData.lastname}
                                        onChange={handleChanges}
                                        disabled={!editingUser}
                                    />
                                    <Label>
                                        Apellidos
                                    </Label>
                                </div>
                                {/* Roles */}
                                <div className="relative pt-5">
                                    <Select
                                        name="roles"
                                        value={formData.roles}
                                        // onChange={handleChanges}
                                        disabled
                                    >
                                        <option value="">Escoge un rol</option>
                                        <option value="admin">Administrador</option>
                                        <option value="recepcion">Recepcionista</option>
                                    </Select>
                                    <Label>
                                        Roles
                                    </Label>
                                    <small className="w-full flex justify-center mt-1 text-gray-500">El rol es asignado por el Administrador.</small>
                                </div>
                            </section>
                            {/* btn Register */}
                            <div className="w-full flex items-center justify-center">
                                {editingUser ? (
                                    <Button
                                        type="button"
                                        onClick={handleSave}
                                        variant="primary"
                                    >
                                        Guardar Cambios
                                    </Button>
                                ) : (
                                    <Button
                                        type="button"
                                        onClick={() => seteditingUser(true)}
                                        variant="secondary"
                                    >
                                        Editar Perfil
                                    </Button>
                                )}
                            </div>
                        </form>
                    </section>
                </div>
            </section>
        </section>
    );
};
export default Profile;