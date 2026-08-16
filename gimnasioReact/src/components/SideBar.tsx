import { useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { sidebarMenus, pathMatches } from "./sideBar/components/SideBarMenus";
import { useAuth } from "../context/useAuth";
// icons
import { RiMenu3Line, RiCloseLine, RiLogoutCircleLine } from "react-icons/ri";
// Components
import SideBarAdmin from "./sideBar/SideBarAdmin";
import SideBarUser from "./sideBar/SideBarUser";
import FormHeader from "./form/formTitle/FormHeader";
//img
import Logo from "../../public/favicon-32x32.png";


export interface SubMenuState {
    menu1: boolean;
    menu2: boolean;
    menu3: boolean;
    menu4: boolean;
    menu5: boolean;
}

const SideBar = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [toggleMenu, setToggleMenu] = useState(false);
    const [showSubMenu, setShowSubMenu] = useState<SubMenuState>({
        menu1: false,
        menu2: false,
        menu3: false,
        menu4: false,
        menu5: false,
    });
    const { user, logout } = useAuth();

    //este useEfect es para obtener el rol del usuario
    const userRoles = user?.roles ?? [];
    const firstRole = userRoles[0] ?? "";

    //Funcion para mostrar y ocultar los submenus
    const handleToggleSubMenu = (submenu: keyof SubMenuState) => {
        setShowSubMenu((prev) => ({
            ...prev,
            [submenu]: !prev[submenu],
        }));
    };

    // Auto-abrir submenú si la ruta actual coincide con algún item
    useEffect(() => {
        for (const menu of sidebarMenus) {
            const hasActiveItem = menu.items.some(item =>
                pathMatches(location.pathname, item.to)
            );
            if (hasActiveItem && !showSubMenu[menu.key as keyof SubMenuState]) {
                setShowSubMenu((prev) => ({ ...prev, [menu.key]: true }));
            }
        }
    }, [location.pathname, showSubMenu]);

    // Esta función nos sirve para cerrar la sesión
    const handleLogOut = () => {
        logout();
        navigate("/");
    };

    //función para capitalizar
    const formatRole = (role: string): string =>
        role.charAt(0).toUpperCase() + role.slice(1);

    // Función para cerrar el menú al hacer clic en un enlace
    useEffect(() => {
        setToggleMenu(false);
    }, [location.pathname]);

    return (
        <>
            <div
                className={`bg-slate-50  border-r border-slate-100 duration-200 ease-in-out fixed flex flex-col justify-between h-full px-3 py-6 overflow-y-scroll top-0 transition-all w-64 z-50 md:w-[40%] lg:w-[35%] xl:w-auto xl:h-screen xl:static ${toggleMenu ? "left-0" : "-left-full"}`}
            >
                {/* Menu */}
                <div>
                    {/* logo + Name gym */}
                    <section className="flex flex-col gap-3 items-center">
                        <FormHeader logo={Logo} title="ControlFit" highlight="Colombia" />
                        <h1 className="text-center text-2xl font-black text-dark mb-10">
                            {firstRole && formatRole(firstRole)}
                            <span className="text-primary">.</span>
                        </h1>
                    </section>
                    <nav>
                        {userRoles.includes("admin") ? (
                            <SideBarAdmin
                                handleToggleSubMenu={handleToggleSubMenu}
                                showSubmenu={showSubMenu}
                                currentPath={location.pathname}
                                
                            />
                        ) : (
                            <SideBarUser
                                handleToggleSubMenu={handleToggleSubMenu}
                                showSubmenu={showSubMenu}
                                currentPath={location.pathname}
                                
                            />
                        )}
                    </nav>
                </div>
                {/* Cerrar Sesión */}
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
export default SideBar;