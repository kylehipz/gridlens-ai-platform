import { RouterProvider } from "react-router-dom";
import { SessionProvider } from "../features/auth/session";
import { createAppRouter } from "../routes/router";

export function App() {
  return (
    <SessionProvider>
      <RouterProvider router={createAppRouter()} />
    </SessionProvider>
  );
}
