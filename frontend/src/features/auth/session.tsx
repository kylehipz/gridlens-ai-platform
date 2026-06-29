import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

export type Workspace = {
  id: string;
  name: string;
  slug: string;
  role: string;
  domain: string;
  status: "active" | "review";
};

type UserSession = {
  name: string;
  email: string;
  initials: string;
};

type SessionContextValue = {
  user: UserSession | null;
  workspace: Workspace | null;
  workspaces: Workspace[];
  signIn: () => void;
  signOut: () => void;
  selectWorkspace: (workspaceId: string) => void;
};

const devUser: UserSession = {
  name: "Mara Quinn",
  email: "mara.quinn@northwind.example",
  initials: "MQ"
};

const devWorkspaces: Workspace[] = [
  {
    id: "northwind",
    name: "Northwind Utilities",
    slug: "northwind-utilities",
    role: "Analyst",
    domain: "Energy Programs",
    status: "active"
  },
  {
    id: "metro",
    name: "Metro Buildings Office",
    slug: "metro-buildings",
    role: "Reviewer",
    domain: "Municipal Buildings",
    status: "review"
  }
];

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(() =>
    window.localStorage.getItem("gridlens.devSession") === "signed-in" ? devUser : null
  );
  const [workspace, setWorkspace] = useState<Workspace | null>(() => {
    const workspaceId = window.localStorage.getItem("gridlens.devWorkspace");
    return devWorkspaces.find((item) => item.id === workspaceId) ?? null;
  });

  const value = useMemo<SessionContextValue>(
    () => ({
      user,
      workspace,
      workspaces: devWorkspaces,
      signIn() {
        window.localStorage.setItem("gridlens.devSession", "signed-in");
        setUser(devUser);
      },
      signOut() {
        window.localStorage.removeItem("gridlens.devSession");
        window.localStorage.removeItem("gridlens.devWorkspace");
        setUser(null);
        setWorkspace(null);
      },
      selectWorkspace(workspaceId) {
        const nextWorkspace = devWorkspaces.find((item) => item.id === workspaceId);
        if (!nextWorkspace) {
          return;
        }
        window.localStorage.setItem("gridlens.devWorkspace", nextWorkspace.id);
        setWorkspace(nextWorkspace);
      }
    }),
    [user, workspace]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used inside SessionProvider");
  }
  return context;
}
