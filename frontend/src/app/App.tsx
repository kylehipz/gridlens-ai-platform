import { RouterProvider } from "react-router-dom";
import { createAppRouter } from "../routes/router";

export function App() {
  return <RouterProvider router={createAppRouter()} />;
}
