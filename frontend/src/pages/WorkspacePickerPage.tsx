import { ArrowRight, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { BrandMark } from "../components/BrandMark";
import { useSession } from "../features/auth/session";

export function WorkspacePickerPage() {
  const navigate = useNavigate();
  const { user, workspaces, selectWorkspace, signOut } = useSession();

  return (
    <main className="workspace-picker">
      <header>
        <BrandMark />
        <div className="picker-account">
          <span>{user?.email}</span>
          <button type="button" className="text-button" onClick={signOut}>
            <LogOut size={15} />
            Sign out
          </button>
        </div>
      </header>
      <section aria-labelledby="workspace-title">
        <p className="eyebrow">Tenant boundary</p>
        <h1 id="workspace-title">Choose a workspace</h1>
        <p>Pick a workspace to continue. Your role can differ in each one.</p>
        <div className="workspace-list">
          {workspaces.map((workspace) => (
            <button
              className="workspace-option"
              type="button"
              key={workspace.id}
              onClick={() => {
                selectWorkspace(workspace.id);
                navigate("/dashboard", { replace: true });
              }}
            >
              <span className="workspace-avatar">{workspace.name.slice(0, 2).toUpperCase()}</span>
              <span>
                <strong>{workspace.name}</strong>
                <small>
                  {workspace.role} · {workspace.domain}
                </small>
              </span>
              <span className={`status-pill status-${workspace.status}`}>{workspace.status}</span>
              <ArrowRight size={17} />
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
