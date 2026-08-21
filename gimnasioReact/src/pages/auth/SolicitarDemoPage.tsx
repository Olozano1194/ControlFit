import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { useState } from "react";
//Icons
import { MdEmail, MdPerson, MdFitnessCenter, MdPhone, MdArrowBack, MdCheckCircle } from "react-icons/md";
// Components
import FormHeader from "../../components/form/formTitle/FormHeader";
//Mensajes
import { toast } from "react-hot-toast";
import { axiosPublic } from "../../api/axios/axios.public";
//img
import Logo from "../../../public/favicon-32x32.png";
import imgGym from "../../../public/img_Gym_prev_ui.png";

type DemoRequestDto = {
  nombre: string;
  email: string;
  telefono: string;
  nombre_gimnasio: string;
};

const SolicitarDemoPage = () => {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors } } = useForm<DemoRequestDto>();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const onSubmit = handleSubmit(async (data: DemoRequestDto) => {
    if (isSubmitting) return; 
    setIsSubmitting(true);
    try {
      await axiosPublic.post('/solicitudes-demo/', data);
      setSuccess(true);
      toast.success('Solicitud enviada correctamente');
    } catch {
      toast.error('Ocurrió un error al enviar la solicitud');
    } finally {
      setIsSubmitting(false);
    }
  });

  if (success) {
    return (
      <main className="w-full h-screen flex flex-col justify-center items-center relative z-10 lg:justify-between lg:flex-row lg:pr-48">
        <div className="hidden w-full h-full relative lg:flex lg:w-1/2 lg:justify-center lg:items-center">
          <img src={imgGym} alt="img del gym" className="w-full h-[75%]" />
        </div>
        <div className="w-[90%] bg-surface-container-lowest border border-outline-variant/10 p-8 rounded-xl shadow-lg space-y-8 md:p-12 md:w-[52%] md:gap-8 lg:w-[45%] xl:max-w-[30%] text-center">
           <MdCheckCircle className="text-6xl text-primary mx-auto" />
           <h2 className="text-2xl font-bold text-on-surface">¡Solicitud Enviada!</h2>
           <p className="text-secondary">Nos pondremos en contacto contigo muy pronto para armar tu demo de ControlFit.</p>
           <button onClick={() => navigate('/login')} className="mt-4 bg-primary text-white px-6 py-2 rounded-full font-semibold transition-transform hover:scale-105">Volver al Inicio</button>
        </div>
      </main>
    );
  }

  return (
    <main className="w-full h-screen flex flex-col justify-center items-center relative z-10 lg:justify-between lg:flex-row lg:pr-48">
      <div className="hidden w-full h-full relative lg:flex lg:w-1/2 lg:justify-center lg:items-center">
        <img src={imgGym} alt="img del gym" className="w-full h-[75%]" />
      </div>
      <form
        onSubmit={onSubmit}
        className="w-[90%] max-h-screen overflow-y-auto bg-surface-container-lowest border border-outline-variant/10 p-8 rounded-xl shadow-[0_1px_30px_-5px_rgba(11,28,48,0.08)] space-y-6 md:p-12 md:w-[52%] lg:w-[45%] xl:max-w-[30%]"
      >
        <section className="w-full flex flex-col items-center gap-2 pb-4">
          <FormHeader
            logo={Logo}
            title="Solicitar"
            highlight="Demo"
          />
          <p className="text-sm text-secondary text-center px-4">Dejanos tus datos y te contactaremos para mostrarte cómo ControlFit puede potenciar tu gimnasio.</p>
        </section>

        {/* Nombre */}
        <section className="space-y-1">
          <label className="block font-bold ml-1 text-[10px] text-secondary tracking-widest uppercase">Nombre Completo</label>
          <div className="border-b border-[rgba(195,198,215,0.4)] duration-300 flex items-center relative transition-all focus-within:border-text-primary">
            <span className="absolute left-0 text-xl text-outline"><MdPerson /></span>
            <input
              type="text"
              className="body-md bg-transparent border-none pl-8 py-2 text-on-surface w-full focus:ring-0 focus:outline-none placeholder:text-outline/50"
              placeholder="Ej: Juan Pérez"
              {...register("nombre", { required: "El nombre es requerido" })}
            />           
          </div>
          {errors.nombre && <span className='text-red-500 text-xs'>{errors.nombre.message}</span>}
        </section>

        {/* Email */}
        <section className="space-y-1">
          <label className="block font-bold ml-1 text-[10px] text-secondary tracking-widest uppercase">Correo Electrónico</label>
          <div className="border-b border-[rgba(195,198,215,0.4)] duration-300 flex items-center relative transition-all focus-within:border-text-primary">
            <span className="absolute left-0 text-xl text-outline"><MdEmail /></span>
            <input
              type="email"
              className="body-md bg-transparent border-none pl-8 py-2 text-on-surface w-full focus:ring-0 focus:outline-none placeholder:text-outline/50"
              placeholder="correo@ejemplo.com"
              {...register("email", { required: "El correo es requerido" })}
            />           
          </div>
          {errors.email && <span className='text-red-500 text-xs'>{errors.email.message}</span>}
        </section>

        {/* Teléfono */}
        <section className="space-y-1">
          <label className="block font-bold ml-1 text-[10px] text-secondary tracking-widest uppercase">WhatsApp / Teléfono</label>
          <div className="border-b border-[rgba(195,198,215,0.4)] duration-300 flex items-center relative transition-all focus-within:border-text-primary">
            <span className="absolute left-0 text-xl text-outline"><MdPhone /></span>
            <input
              type="text"
              className="body-md bg-transparent border-none pl-8 py-2 text-on-surface w-full focus:ring-0 focus:outline-none placeholder:text-outline/50"
              placeholder="+57 300 000 0000"
              {...register("telefono", { required: "El teléfono es requerido" })}
            />           
          </div>
          {errors.telefono && <span className='text-red-500 text-xs'>{errors.telefono.message}</span>}
        </section>

        {/* Gimnasio */}
        <section className="space-y-1">
          <label className="block font-bold ml-1 text-[10px] text-secondary tracking-widest uppercase">Nombre del Gimnasio</label>
          <div className="border-b border-[rgba(195,198,215,0.4)] duration-300 flex items-center relative transition-all focus-within:border-text-primary">
            <span className="absolute left-0 text-xl text-outline"><MdFitnessCenter /></span>
            <input
              type="text"
              className="body-md bg-transparent border-none pl-8 py-2 text-on-surface w-full focus:ring-0 focus:outline-none placeholder:text-outline/50"
              placeholder="Tu Gimnasio"
              {...register("nombre_gimnasio", { required: "El nombre del gimnasio es requerido" })}
            />           
          </div>
          {errors.nombre_gimnasio && <span className='text-red-500 text-xs'>{errors.nombre_gimnasio.message}</span>}
        </section>

        <button
          disabled={isSubmitting}
          className="w-full bg-primary bg-pulse-gradient cursor-pointer flex font-bold gap-2 items-center justify-center py-3 mt-4 rounded-lg shadow-lg text-white transition-all hover:shadow-primary/20 hover:scale-[1.01] active:scale-[0.98] disabled:opacity-60 disabled:scale-100 disabled:cursor-not-allowed"
          type="submit"
        >
          {isSubmitting ? 'Enviando...' : 'Enviar Solicitud'}
        </button>

        <div className="flex justify-center pt-6">
          <Link to="/login" className="flex items-center gap-2 font-semibold text-xs text-primary transition-colors hover:text-primary/70">
            <MdArrowBack className="text-lg" /> Volver al Inicio de Sesión
          </Link>
        </div>
      </form>
    </main>
  );
};

export default SolicitarDemoPage;
