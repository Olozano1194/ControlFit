import { useAuth } from "../../context/useAuth";
// Menu
import { SidebarItem } from "./components/SideBarItem";
import { SidebarSubMenu } from "./components/SideBarSubMenu";
import { getSidebarMenusByRole, sidebarMenus, pathMatches } from "./components/SideBarMenus";
// Icon
import { RiMessage3Fill, RiCalendarTodoLine, RiHome8Line } from "react-icons/ri";
import { MdOutlineSupportAgent } from "react-icons/md";

export type SubMenuKey = 'menu1' | 'menu2' | 'menu3' | 'menu4' | 'menu5';

export interface SubMenuState {
  menu1: boolean;
  menu2: boolean;
  menu3: boolean;
  menu4: boolean;
  menu5: boolean;
}

interface SidebarUserProps {
  showSubmenu: SubMenuState;
  handleToggleSubMenu: (submenu: keyof SubMenuState) => void;
  currentPath: string;
}

const SideBarUser: React.FC<SidebarUserProps> = ({ showSubmenu, handleToggleSubMenu, currentPath }) => {
    const { user } = useAuth();
    const filteredMenus = getSidebarMenusByRole(user?.roles);

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
        <ul className="flex flex-col gap-2">
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
        </ul>
    );        
};
export default SideBarUser;