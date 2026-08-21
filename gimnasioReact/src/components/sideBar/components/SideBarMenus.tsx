import { HiMiniUserGroup } from "react-icons/hi2";
import { FaCreditCard } from "react-icons/fa";

export type UserRole = 'admin' | 'recepcion' | 'superadmin';

export interface SidebarMenu {
  key: string;
  title: string;
  icon: React.ReactNode;
  items: Array<{
    label: string;
    to: string;
  }>;
  roles: UserRole[];
}

export const sidebarMenus: SidebarMenu[] = [
  {
    key: "menu1",
    title: "Miembro",
    icon: <HiMiniUserGroup />,
    items: [
      { label: "Registrar miembro", to: "registrar-miembro" },
      { label: "Ver miembros", to: "miembros" },
    ],
    roles: ['admin', 'recepcion']
  },
  {
    key: "menu2",
    title: "Miembro Diario",
    icon: <HiMiniUserGroup />,
    items: [
      { label: "Registrar miembro", to: "registrar-miembro-day" },
      { label: "Ver miembros", to: "miembros-day" },
    ],
    roles: ['admin', 'recepcion']
  },
  {
    key: "menu3",
    title: "Usuario",
    icon: <HiMiniUserGroup />,
    items: [
      { label: "Registrar Usuario", to: "register" },
      { label: "Ver Usuarios", to: "listUser" },
    ],
    roles: ['admin']
  },
  {
    key: "menu4",
    title: "Membresía",
    icon: <FaCreditCard />,
    items: [
      { label: "Registrar Membresía", to: "registrar-membresia" },
      { label: "Ver Membresías", to: "memberships-list" },
    ],
    roles: ['admin']
  },
  {
    key: "menu5", 
    title: "Asignar Membresía",
    icon: <FaCreditCard />,
    items: [
      { label: "Ver Asignaciones", to: "asignar-membresia-list" },
    ],
    roles: ['admin', 'recepcion']
  },
];

/**
 * Verifica si una ruta actual coincide con un item del sidebar.
 * Compara por segmentos de path para evitar falsos positivos
 * (ej: "miembros" no debe coincidir con "miembros-day").
 */
export const pathMatches = (currentPath: string, itemTo: string): boolean => {
    const path = currentPath.endsWith('/') ? currentPath.slice(0, -1) : currentPath;
    return path === `/dashboard/${itemTo}` || path.startsWith(`/dashboard/${itemTo}/`);
};

// Función para obtener menús filtrados por rol
export const getSidebarMenusByRole = (userRoles: UserRole[] | undefined): SidebarMenu[] => {
    if (!userRoles || userRoles.length === 0) return [];

    return sidebarMenus.filter(menu => {
        // Verificar si el usuario tiene al menos uno de los roles requeridos
        return menu.roles.some(requiredRole => 
            userRoles.includes(requiredRole)
        );
    });
};