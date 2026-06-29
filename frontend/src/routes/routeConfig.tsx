import {
  AlertTriangle,
  Bot,
  Database,
  FileText,
  Gauge,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  TestTube2
} from "lucide-react";
import type { ComponentType, ReactElement } from "react";
import {
  AnomaliesPage,
  AssistantPage,
  AuditPage,
  DashboardPage,
  DatasetsPage,
  EvaluationsPage,
  ReportsPage,
  SettingsPage,
  UsagePage
} from "../pages/ProductPages";

export type AppRoute = {
  path: string;
  label: string;
  section: "main" | "governance";
  icon: ComponentType<{ size?: number; strokeWidth?: number }>;
  element: ReactElement;
};

export const appRoutes: AppRoute[] = [
  {
    path: "/dashboard",
    label: "Dashboard",
    section: "main",
    icon: LayoutDashboard,
    element: <DashboardPage />
  },
  {
    path: "/assistant",
    label: "Assistant",
    section: "main",
    icon: Bot,
    element: <AssistantPage />
  },
  {
    path: "/datasets",
    label: "Datasets",
    section: "main",
    icon: Database,
    element: <DatasetsPage />
  },
  {
    path: "/evaluations",
    label: "Evaluations",
    section: "main",
    icon: TestTube2,
    element: <EvaluationsPage />
  },
  {
    path: "/anomalies",
    label: "Anomalies",
    section: "main",
    icon: AlertTriangle,
    element: <AnomaliesPage />
  },
  {
    path: "/reports",
    label: "Reports",
    section: "governance",
    icon: FileText,
    element: <ReportsPage />
  },
  {
    path: "/audit",
    label: "Audit",
    section: "governance",
    icon: ShieldCheck,
    element: <AuditPage />
  },
  {
    path: "/usage",
    label: "Usage",
    section: "governance",
    icon: Gauge,
    element: <UsagePage />
  },
  {
    path: "/settings",
    label: "Settings",
    section: "governance",
    icon: Settings,
    element: <SettingsPage />
  }
];

export const defaultAppPath = "/dashboard";
