import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../../context/useAuth";
//Icons
import { MdEmail, MdOutlineVisibility, MdOutlineVisibilityOff, MdArrowForward } from "react-icons/md";
import { RiLockPasswordLine } from "react-icons/ri";
import { FaShield, FaDatabase } from "react-icons/fa6";
// Components
import FormHeader from "../../components/form/formTitle/FormHeader";
//Mensajes
import { toast } from "react-hot-toast";
//Models
import { LoginUserDto } from "../../model/dto/user.dto";
//img
import Logo from "../../../public/favicon-32x32.png";
import imgGym from "../../../public/img_Gym_prev_ui.png";


const Login = () => {
  const navigate = useNavigate();
  const { login, loading, error } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginUserDto>();
  const [showkPass, setShowPass] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);


  const onSubmit = handleSubmit(async (data: LoginUserDto) => {
    if (isSubmitting) return; // Evitar doble envío
    setIsSubmitting(true);
    try {
      await login({
        email: data.email,
        password: data.password,
      });

      toast.success('Login exitoso');
      navigate("/dashboard");
    } catch {
      toast.error("Error al iniciar sesión");
    } finally {
      setIsSubmitting(false);
    }
  });

  // Visibilidad del pass
  const handlePass = () => {
    setShowPass(!showkPass);
  };

  return (
    <main className="w-full h-screen flex flex-col justify-center items-center relative z-10 lg:justify-between lg:flex-row lg:pr-48">
      <div className="hidden w-full h-full relative lg:flex lg:w-1/2 lg:justify-center lg:items-center">
        <img src={imgGym} alt="img del gym" className="w-full h-[75%]" />
      </div>
      <form
        onSubmit={onSubmit}
        className="w-[90%] bg-surface-container-lowest border border-outline-variant/10 p-8 rounded-xl shadow-[0_1px_30px_-5px_rgba(11,28,48,0.08)] space-y-8 md:p-12 md:w-[52%] md:gap-8 lg:w-[45%] xl:max-w-[30%]"
      >
        <section className="w-full flex justify-center">
          <FormHeader
            logo={Logo}
            title="ControlFit"
            highlight="Colombia"
          />
        </section>
        {/* Email */}
        <section className="space-y-1">
          <label htmlFor="" className="block font-bold ml-1 text-[10px] text-secondary tracking-widest uppercase">Correo Electrónico</label>
          <div className="border-b border-[rgba(195, 198, 215, 0.4)] duration-300 flex items-center relative transition-all focus-within:border-text-primary">
            <span className="absolute left-0 text-xl text-outline"><MdEmail /></span>
            <input
              type="text"
              id="email"
              className="body-md bg-transparent border-none pl-8 py-3 text-on-surface w-full focus:ring-0 focus:outline-none placeholder:text-outline/50"
              placeholder="Escribe el correo electrónico"
              {...register("email", {
                required: {
                  value: true,
                  message: "Correo electrónico requerido",
                },
              })}
            />           
          </div>
          {
            errors.email && <span className='text-red-500 text-sm'>{errors.email.message}</span>
          }
        </section>
        {/* Password */}
        <section className="space-y-1">
          <label htmlFor="" className="block font-bold ml-1 text-[10px] text-secondary tracking-widest uppercase">Contraseña</label>
          <div className="border-b border-[rgba(195, 198, 215, 0.4)] duration-300 flex items-center relative transition-all focus-within:border-text-primary">
            <span className="absolute left-0 text-xl text-outline"><RiLockPasswordLine /></span>
            <input
              type={showkPass ? "text" : "password"}
              id="password"
              className="body-md bg-transparent border-none pl-8 py-3 text-on-surface w-full focus:ring-0 focus:outline-none placeholder:text-outline/50"
              placeholder="Escribe la Contraseña"
              {...register("password", {
                required: {
                  value: true,
                  message: "Contraseña requerida",
                },
              })}
            />
            <button type="button" onClick={handlePass}>
              {showkPass ? <MdOutlineVisibility /> : <MdOutlineVisibilityOff />}
            </button>           
          </div>
          {
            errors.password && <span className='text-red-500 text-sm'>{errors.password.message}</span>
          }          
          <div className="flex justify-end pt-2">
            <Link to='#' className="font-semibold text-xs text-primary transition-colors hover:text-primary/70">¿olvidaste tu contraseña?</Link>
          </div>
          {error && <span className="text-red-600 text-sm text-center -mt-3 mb-100 md:-mt-6">{error}</span>}
        </section>
        {/* btn login */}
        <button
          disabled={isSubmitting || loading}
          className="w-full bg-primary bg-pulse-gradient cursor-pointer flex font-bold gap-2 items-center justify-center py-4 rounded-lg shadow-lg text-white transition-all hover:shadow-primary/20 hover:scale-[1.01] active:scale-[0.98] disabled:opacity-60 disabled:scale-100 disabled:cursor-not-allowed"
          type="submit"
        >
          {isSubmitting || loading ? 'Ingresando...' : 'Ingresar al Panel'}
          <MdArrowForward className={`text-2xl ${isSubmitting || loading ? 'animate-pulse' : ''}`} />
        </button>
        {/* footer */}
        <section className="border-t border-outline-variant mt-12 pt-8">
          <div className="flex flex-col gap-4 items-center">
            <p className="text-sm text-secondary">¿Nuevo en ControlFit Colombia?</p>
            <button 
              type="button" 
              onClick={() => navigate('/solicitar-demo')}
              className="bg-surface-container-high cursor-pointer font-semibold px-6 py-2 rounded-full text-on-surface text-sm transition-colors hover:bg-surface-container-high/80"
            >
              Solicitar una Demo
            </button>
          </div>
        </section>
      </form>
      {/* Version */}
      <section className="w-full bottom-8 hidden items-center justify-center gap-x-10 left-8 mt-7 md:flex lg:fixed">
        <div className="flex gap-2 items-center text-secondary/60">
          <span className="text-sm"><FaShield /></span>
          <span className="font-medium text-[10px] tracking-wider uppercase">Secure Acess</span>
        </div>
        <div className="flex gap-2 items-center text-secondary/60">
          <span className="text-sm"><FaDatabase /></span>
          <span className="font-medium text-[10px] tracking-wider uppercase">v1.4.0</span>
        </div>
      </section>
    </main>
  );
};
export default Login;