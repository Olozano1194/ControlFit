import {Routes, Route, Navigate } from 'react-router-dom';
//Context
import { useAuth } from './context/useAuth';
//Layouts
import LayoutAdmin from './layouts/LayoutAdmin';
import LayoutPlatform from './layouts/LayoutPlatform';
//Pages auth
import Login from './pages/auth/LoginPage';
import Register from './pages/auth/RegisterPage';
import SolicitarDemo from './pages/auth/SolicitarDemoPage';
import ForgetPassword from './pages/auth/ForgetPassword';
//Pages admin
import Home from './pages/admin/HomePage';
import ListUser from './pages/admin/usuarios/ListUser';
import Profile from './pages/admin/usuarios/ProfileAdmin';
// Miembros mensuales
import MemberForm from './pages/admin/registroPorMes/MemberForm';
import ListMiembro from './pages/admin/registroPorMes/ListMiembro';
// Miembros por dia
import ListMiembroDay from './pages/admin/registroPorDia/ListMiembroDay';
import MemberFormDay from './pages/admin/registroPorDia/MemberFormDay';
// Membresías
import ListMemberShips from './pages/admin/memberShips/ListMemberShips';
import MemberShipsForm from './pages/admin/memberShips/MemberShipsForm';
//Asignación membresías
import ListAsignarMemberShips from './pages/admin/asignadaMemberShips/ListAsignarMemberShips';
//Notificaciones
import NotificationsPage from './pages/admin/notifications/NotificationsPage';
// Calendario
import CalendarPage from './pages/admin/calendario/CalendarioPage';
// Solicitudes Demo (plataforma)
import DemoRequestsPage from './pages/admin/demo/DemoRequestsPage';
import PlatformDashboardPage from './pages/admin/platform/PlatformDashboardPage';
import GimnasiosPage from './pages/admin/platform/GimnasiosPage';
import GimnasioDetailPage from './pages/admin/platform/GimnasioDetailPage';
//Rutas protegidas
import ProtectRoute from './routes/protectedRoute/ProtectRoute';
import SuperAdminRoute from './routes/protectedRoute/SuperAdminRoute';

import Error404 from './pages/Error404';

// Redirige la raíz según sesión: con sesión válida a /dashboard, sin sesión a /login.
// Espera el loading para no mandar al login a un usuario con sesión restaurable.
const HomeRedirect = () => {
    const { isAuthenticated, loading } = useAuth();
    if (loading) return null;
    return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />;
};

function App() {
  return (
    <Routes>        
      <Route path="/" element={<HomeRedirect />} />
      <Route path="login" element={<Login />} />
      <Route path="solicitar-demo" element={<SolicitarDemo />} />
      <Route path="forget-password" element={<ForgetPassword />} />

      {/* Rutas de la plataforma — solo superadmin */}
      <Route element={<SuperAdminRoute />}>
        <Route path="platform" element={<LayoutPlatform />}>
          <Route index element={<PlatformDashboardPage />} />
          <Route path="solicitudes-demo" element={<DemoRequestsPage />} />
          <Route path="gimnasios" element={<GimnasiosPage />} />
          <Route path="gimnasios/:id" element={<GimnasioDetailPage />} />
        </Route>
      </Route>

      {/* Rutas protegidas del gimnasio */}
      <Route element={<ProtectRoute />} >
        <Route path="dashboard" element={<LayoutAdmin />} >
          <Route index element={<Home />} />
          {/* Usuarios */}
          <Route path="register" element={<Register />} />
          <Route path="listUser" element={<ListUser />} />
          <Route path="profile" element={<Profile />} />
          {/* Miembros mensuales */}
          <Route path="registrar-miembro" element={<MemberForm />} />
          <Route path="miembros" element={<ListMiembro />} />
          <Route path="miembro/:id" element={<MemberForm />} />
          {/* Miembros por dia */}
          <Route path="miembros-day" element={<ListMiembroDay />} />
          <Route path="registrar-miembro-day" element={<MemberFormDay />} />
          <Route path="miembro-day/:id" element={<MemberFormDay />} />
          {/* Membresías */}
          <Route path="registrar-membresia" element={<MemberShipsForm />} />
          <Route path="memberships-list" element={<ListMemberShips />} />
          <Route path="membresia/:id" element={<MemberShipsForm />} />
          {/* Asignación Membresía */}
          <Route path="asignar-membresia-list" element={<ListAsignarMemberShips />} />
          {/* Notificaciones */}
          <Route path="notifications" element={<NotificationsPage />} />
          {/* Calendario */}
          <Route path="calendar" element={<CalendarPage />} />
        </Route> 
      </Route>       
      <Route path="*" element={<Error404 />} />
    </Routes> 
  )
}
export default App