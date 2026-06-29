import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { WorkspacePickerPage } from "../pages/WorkspacePickerPage";
import { SignInPage } from "../pages/SignInPage";
import { ProtectedRoute } from "./ProtectedRoute";
import { appRoutes, defaultAppPath } from "./routeConfig";

export function createAppRouter() {
  return createBrowserRouter([
    {
      path: "/signin",
      element: <SignInPage />
    },
    {
      element: <ProtectedRoute />,
      children: [
        {
          path: "/workspaces",
          element: <WorkspacePickerPage />
        },
        {
          element: <AppShell />,
          children: appRoutes.map((route) => ({
            path: route.path,
            element: route.element
          }))
        }
      ]
    },
    {
      path: "/",
      element: <Navigate to={defaultAppPath} replace />
    },
    {
      path: "*",
      element: <Navigate to={defaultAppPath} replace />
    }
  ]);
}
