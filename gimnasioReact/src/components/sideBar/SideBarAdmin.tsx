// Menu
import { SidebarItem } from "./components/SideBarItem";
import { SidebarSubMenu } from "./components/SideBarSubMenu";
import { getSidebarMenusByRole, sidebarMenus, pathMatches } from "./components/SideBarMenus";
import { useAuth } from "../../context/useAuth";
// Icon
import { MdOutlineSupportAgent } from "react-icons/md";
import { RiMessage3Fill, RiCalendarTodoLine, RiHome8Line } from "react-icons/ri";


export type SubMenuKey = 'menu1' | 'menu2' | 'menu3' | 'menu4' | 'menu5';

export interface SubMenuState {
  menu1: boolean;
  menu2: boolean;
  menu3: boolean;
  menu4: boolean;
  menu5: boolean;
}

interface SidebarAdminProps {
  showSubmenu: SubMenuState;
  handleToggleSubMenu: (submenu: SubMenuKey) => void;
  currentPath: string;
}

const SideBarAdmin = ({ showSubmenu, handleToggleSubMenu, currentPath }: SidebarAdminProps ) => {
    const { user } = useAuth();
    const filteredMenus = getSidebarMenusByRole(user?.roles);

    // Determinar qué rutas están activas
    const isHomeActive = currentPath === '/dashboard' || currentPath === '/dashboard/';

    const getActiveItem = (items: { label: string; to: string }[]) => {
      return items.find(item => pathMatches(currentPath, item.to))?.to;
    };

    const isParentActive = (menuKey: string) => {
      const menu = sidebarMenus.find(m => m.key === menuKey);
      if (!menu) return false;
      return menu.items.some(item => pathMatches(currentPath, item.to));
    };

    return (
        <nav className="flex flex-col gap-2">
            {/* Home */}
            <SidebarItem 
                to='/dashboard' 
                icon={<RiHome8Line />} 
                label='Inicio'
                isActive={isHomeActive}                
            />
            {/* Menus desplegables */}
            {filteredMenus.map(menu => (
                <SidebarSubMenu
                    key={menu.key}
                    title={menu.title}
                    icon={menu.icon}
                    isOpen={showSubmenu[menu.key as SubMenuKey ]}
                    onToggle={() => handleToggleSubMenu(menu.key as SubMenuKey)}
                    items={menu.items}
                    activeItem={getActiveItem(menu.items)}
                    isParentActive={isParentActive(menu.key)}
            />
            ))}

            <SidebarItem 
                to='#' 
                icon={<RiMessage3Fill />} 
                label='Mensajes' 
            />
            <SidebarItem 
                to='#' 
                icon={<MdOutlineSupportAgent />} 
                label='Soporte técnico' 
            />
            <SidebarItem 
                to='/dashboard/calendar' 
                icon={<RiCalendarTodoLine />} 
                label='Calendario' 
            />        
        </nav>
    );
};
export default SideBarAdmin;