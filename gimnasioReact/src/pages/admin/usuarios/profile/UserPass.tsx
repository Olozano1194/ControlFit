//Api
import { getUserProfile } from "../../../../api/users/users.api";
//hooks
import { useState, useEffect } from "react";
//ui
import { Input, Label, Button } from '../../../../components/ui/index';
// Mensajes
import { toast } from "react-hot-toast";

function UserPass() {
    const [user, setUser] = useState({ email: '' });

    useEffect(() => {
        const axiosUserData = async () => {
            try {
                const data = await getUserProfile();
                setUser({
                    email: data.user.email,
                });
            } catch (error) {
                console.error(error);
            }
        };
        axiosUserData();
    }, []);

    const handleChangePassword = () => {
        toast.success('Función de cambiar contraseña próximamente disponible', {
            duration: 4000,
            position: 'bottom-right',
        });
    };

    return (
        <section className="max-w-7xl mx-auto p-6 relative lg:p-10">
            <section className="gap-8 grid grid-cols-1 lg:grid-cols-12">
                <div className="space-y-8 md:col-span-6 lg:col-span-8 xl:col-span-11">
                    <section className="bg-surface-container-lowest overflow-hidden p-8 relative rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
                        <h4 className="font-bold flex gap-2 items-center mb-10 relative text-xl">
                        <span className="h-6 bg-pulse-gradient rounded-full w-2"></span>
                        Cuenta & Seguridad
                    </h4>
                    <form className="relative space-y-10 z-10">
                        <section className='gap-y-10 gap-x-8 grid grid-cols-1 md:grid-cols-2'>
                            {/* Email */}
                            <div className="relative pt-5">
                                <Input
                                    type="text"
                                    placeholder=""
                                    name='email'
                                    value={user.email}
                                    disabled
                                />
                                <Label>
                                    Correo Electrónico
                                </Label>
                                <small className="w-full flex justify-center mt-1 text-gray-500">
                                    El correo es asignado por el Administrador.
                                </small>
                            </div>
                            {/* Password */}
                            <div className="relative pt-5">
                                <Input
                                    type="password"
                                    placeholder=""
                                    name='password'
                                    disabled
                                    value='••••••••'
                                />
                                <Label>
                                    Contraseña
                                </Label>
                            </div>
                        </section>
                        {/* Botón para cambiar contraseña */}
                        <div className="w-full flex items-center justify-center">
                            <Button
                                type="button"
                                onClick={handleChangePassword}
                                variant="secondary"
                            >
                                Cambiar Contraseña
                            </Button>
                        </div>
                    </form>

                    </section>                    
                </div>
            </section>
        </section>
    );
}
export default UserPass;