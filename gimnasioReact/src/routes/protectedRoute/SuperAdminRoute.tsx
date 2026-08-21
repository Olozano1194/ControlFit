import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../../context/useAuth";

// Protege rutas exclusivas del dueño de la plataforma.
// Solo usuarios con rol 'superadmin' pueden acceder.
// Cualquier otro rol autenticado es redirigido al dashboard normal.
const SuperAdminRoute = () => {
    const { user, isAuthenticated, loading } = useAuth();

    if (loading) return null;

    if (!isAuthenticated) return <Navigate to="/login" replace />;

    const isSuperAdmin = user?.roles?.includes('superadmin');
    if (!isSuperAdmin) return <Navigate to="/dashboard" replace />;

    return <Outlet />;
};

export default SuperAdminRoute;
