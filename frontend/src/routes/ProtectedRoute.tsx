import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useSession } from "../features/auth/session";

export function ProtectedRoute() {
  const location = useLocation();
  const { user, workspace } = useSession();

  if (!user) {
    return <Navigate to="/signin" replace state={{ from: location.pathname }} />;
  }

  if (!workspace && location.pathname !== "/workspaces") {
    return <Navigate to="/workspaces" replace />;
  }

  return <Outlet />;
}
