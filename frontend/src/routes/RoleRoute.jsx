import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Loading from "../components/Loading";

function RoleRoute({ allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Loading message="Checking access..." />
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export default RoleRoute;