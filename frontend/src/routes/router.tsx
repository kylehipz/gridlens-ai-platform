import { createBrowserRouter, Navigate } from "react-router-dom";

function SignInPage() {
  return (
    <main className="auth-page">
      <section className="auth-panel" aria-labelledby="signin-title">
        <div className="brand-mark" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
        <p className="eyebrow">GridLens</p>
        <h1 id="signin-title">Sign in</h1>
        <p>Use your organization account to open a tenant workspace.</p>
      </section>
    </main>
  );
}

export function createAppRouter() {
  return createBrowserRouter([
    {
      path: "/signin",
      element: <SignInPage />
    },
    {
      path: "*",
      element: <Navigate to="/signin" replace />
    }
  ]);
}
