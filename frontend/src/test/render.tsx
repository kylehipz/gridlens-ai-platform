import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement } from "react";
import { RouterProvider } from "react-router-dom";
import { SessionProvider } from "../features/auth/session";
import { createAppRouter } from "../routes/router";

export function renderRoute(path = "/", options?: RenderOptions) {
  window.history.pushState({}, "", path);
  return render(
    <SessionProvider>
      <RouterProvider router={createAppRouter()} />
    </SessionProvider>,
    options
  );
}

export function renderWithSession(ui: ReactElement, options?: RenderOptions) {
  return render(<SessionProvider>{ui}</SessionProvider>, options);
}
