import {Routes, Route, Navigate } from 'react-router-dom';
//Layouts
import LayoutAdmin from './layouts/LayoutAdmin';
//Pages auth
import Login from './pages/auth/LoginPage';
import Register from './pages/auth/RegisterPage';
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
//Ruta protegida
import ProtectRoute from './routes/protectedRoute/ProtectRoute';

import Error404 from './pages/Error404';

function App() {
  return (
    <Routes>        
      <Route path="/" element={<Navigate to='/login' />} />
      <Route path="login" element={<Login />} />
      <Route path="forget-password" element={<ForgetPassword />} />
      {/* Rutas protegidas */}
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
          <Route path="asignar-membresia-list" element={<ListAsignarMemberShips /> } />
          {/* Notificaciones */}
          <Route path="notifications" element={<NotificationsPage />} />
        </Route> 
      </Route>       
      <Route path="*" element={<Error404 />} />
    </Routes> 
  )
}

export default App
