import { useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { SidebarItem } from "./sideBar/components/SideBarItem";
import FormHeader from "./form/formTitle/FormHeader";
import { useAuth } from "../context/useAuth";
// icons
import { RiMenu3Line, RiCloseLine, RiLogoutCircleLine, RiHome8Line, RiBuilding4Line } from "react-icons/ri";
import { MdOutlineSupportAgent } from "react-icons/md";
//img
import Logo from "../../public/favicon-32x32.png";

const SideBarPlatform = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [toggleMenu, setToggleMenu] = useState(false);
    const { logout } = useAuth();

    useEffect(() => {
        setToggleMenu(false);
    }, [location.pathname]);

    const handleLogOut = () => {
        logout();
        navigate("/");
    };

    return (
        <>
            <div
                className={`bg-slate-50 border-r border-slate-100 duration-200 ease-in-out fixed flex flex-col justify-between h-full px-3 py-6 overflow-y-scroll top-0 transition-all w-64 z-50 md:w-[40%] lg:w-[35%] xl:w-auto xl:h-screen xl:static ${toggleMenu ? "left-0" : "-left-full"}`}
            >
                <div>
                    <section className="flex flex-col gap-3 items-center">
                        <FormHeader logo={Logo} title="ControlFit" highlight="Plataforma" />
                        <h1 className="text-center text-2xl font-black text-dark mb-10">
                            SuperAdmin<span className="text-primary">.</span>
                        </h1>
                    </section>
                    <nav>
                        <ul className="flex flex-col gap-2">
                            <SidebarItem
                                to="/platform"
                                icon={<RiHome8Line />}
                                label="Resumen"
                                isActive={location.pathname === '/platform'}
                            />
                            <SidebarItem
                                to="/platform/gimnasios"
                                icon={<RiBuilding4Line />}
                                label="Gimnasios"
                                isActive={location.pathname.startsWith('/platform/gimnasios')}
                            />
                            <SidebarItem
                                to="/platform/solicitudes-demo"
                                icon={<MdOutlineSupportAgent />}
                                label="Solicitudes Demo"
                                isActive={location.pathname.startsWith('/platform/solicitudes-demo')}
                            />
                        </ul>
                    </nav>
                </div>
                <nav>
                    <ul className="border-t border-nav/30 flex flex-col gap-4">
                        <li>
                            <button
                                onClick={handleLogOut}
                                className="w-full flex items-center gap-3 py-2 px-4 rounded-lg hover:bg-slate-100 text-nav font-semibold transition-colors"
                            >
                                <RiLogoutCircleLine className="text-primary" />
                                Cerrar Sesión
                            </button>
                        </li>
                    </ul>
                </nav>
            </div>
            <button
                onClick={() => setToggleMenu(!toggleMenu)}
                className="cursor-pointer xl:hidden fixed bottom-4 right-4 bg-pulse-gradient text-white transition-transform p-3 rounded-full shadow-2xl z-50 hover:scale-110"
            >
                {toggleMenu ? <RiCloseLine /> : <RiMenu3Line />}
            </button>
        </>
    );
};
export default SideBarPlatform;