import { Bell, Menu, Search, X } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useSession } from "../features/auth/session";
import { appRoutes } from "../routes/routeConfig";
import { BrandMark } from "./BrandMark";

export function AppShell() {
  const [isNavOpen, setIsNavOpen] = useState(false);
  const { user, workspace } = useSession();
  const location = useLocation();
  const activeRoute = appRoutes.find((route) => route.path === location.pathname);
  const mainRoutes = appRoutes.filter((route) => route.section === "main");
  const governanceRoutes = appRoutes.filter((route) => route.section === "governance");

  return (
    <div className="app-shell">
      <aside className={`sidebar ${isNavOpen ? "is-open" : ""}`} aria-label="Workspace navigation">
        <div className="sidebar-header">
          <BrandMark />
          <button
            className="icon-button sidebar-close"
            type="button"
            aria-label="Close navigation"
            onClick={() => setIsNavOpen(false)}
          >
            <X size={18} />
          </button>
        </div>

        <div className="workspace-chip">
          <span className="workspace-avatar">NW</span>
          <span>
            <strong>{workspace?.name ?? "Choose workspace"}</strong>
            <small>{workspace?.domain ?? "Tenant workspace"}</small>
          </span>
        </div>

        <nav className="sidebar-nav">
          <NavSection label="Main" routes={mainRoutes} onNavigate={() => setIsNavOpen(false)} />
          <NavSection label="Governance" routes={governanceRoutes} onNavigate={() => setIsNavOpen(false)} />
        </nav>

        <div className="sidebar-user">
          <span className="user-avatar">{user?.initials ?? "GL"}</span>
          <span>
            <strong>{user?.name ?? "GridLens user"}</strong>
            <small>{workspace?.role ?? "No workspace selected"}</small>
          </span>
        </div>
      </aside>

      {isNavOpen ? <button className="nav-scrim" aria-label="Close navigation" onClick={() => setIsNavOpen(false)} /> : null}

      <div className="shell-main">
        <header className="topbar">
          <button
            className="icon-button menu-button"
            type="button"
            aria-label="Open navigation"
            onClick={() => setIsNavOpen(true)}
          >
            <Menu size={20} />
          </button>
          <h1>{activeRoute?.label ?? "Workspace"}</h1>
          <label className="search-field">
            <Search size={16} aria-hidden="true" />
            <span className="sr-only">Search</span>
            <input type="search" placeholder="Search datasets, evaluations..." />
          </label>
          <button className="icon-button" type="button" aria-label="Notifications">
            <Bell size={18} />
            <span className="notification-dot" aria-hidden="true" />
          </button>
        </header>
        <main className="workspace-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function NavSection({
  label,
  routes,
  onNavigate
}: {
  label: string;
  routes: typeof appRoutes;
  onNavigate: () => void;
}) {
  return (
    <section aria-labelledby={`nav-${label.toLowerCase()}`}>
      <h2 id={`nav-${label.toLowerCase()}`}>{label}</h2>
      {routes.map((route) => {
        const Icon = route.icon;
        return (
          <NavLink key={route.path} to={route.path} onClick={onNavigate}>
            <Icon size={18} strokeWidth={1.8} />
            <span>{route.label}</span>
          </NavLink>
        );
      })}
    </section>
  );
}
