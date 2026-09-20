const FooterSection = () => {
    return (
        <footer className="bg-slate-50/50 flex items-center justify-between mt-auto p-8">
            <p className="font-medium text-[11px] text-slate-400 tracking-widest uppercase">@ 2026 ControlFit Colombia - Plataforma de Gestión de elite</p>
            <div className="flex gap-6">
                <a href="#" className="font-bold text-[11px] text-nav tracking-widest transition-colors uppercase hover:text-primary">Privacidad</a>
                <a href="#" className="font-bold text-[11px] text-nav tracking-widest transition-colors uppercase hover:text-primary">Soporte</a>
            </div>
        </footer>
    );
};
export default FooterSection;