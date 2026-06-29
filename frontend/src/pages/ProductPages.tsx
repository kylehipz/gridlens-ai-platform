import { AlertTriangle, Bot, Database, FileText, Gauge, ShieldCheck, TestTube2, TrendingUp } from "lucide-react";
import type { ElementType } from "react";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../components/States";

type PageModel = {
  title: string;
  kicker: string;
  summary: string;
  primaryMetric: string;
  primaryLabel: string;
  secondaryMetric: string;
  secondaryLabel: string;
  status: "passed" | "warning" | "failed" | "running" | "queued";
  icon: ElementType;
};

const pageModels: Record<string, PageModel> = {
  dashboard: {
    title: "Program intelligence",
    kicker: "Executive workspace",
    summary: "Monitor savings, data quality, active evaluations, and evidence readiness from one tenant-scoped view.",
    primaryMetric: "8.4%",
    primaryLabel: "Weather-normalized savings",
    secondaryMetric: "94%",
    secondaryLabel: "Evidence coverage",
    status: "passed",
    icon: TrendingUp
  },
  assistant: {
    title: "Evidence-grounded assistant",
    kicker: "Tenant-scoped answers",
    summary: "Ask questions over approved methodology, quality reports, and evaluation summaries with citation guardrails.",
    primaryMetric: "12",
    primaryLabel: "Indexed evidence sets",
    secondaryMetric: "3",
    secondaryLabel: "Open caveats",
    status: "running",
    icon: Bot
  },
  datasets: {
    title: "Data operations",
    kicker: "Validation pipeline",
    summary: "Track uploaded files, schema checks, data quality findings, and normalized operational datasets.",
    primaryMetric: "27",
    primaryLabel: "Tenant datasets",
    secondaryMetric: "5",
    secondaryLabel: "Need review",
    status: "warning",
    icon: Database
  },
  evaluations: {
    title: "Program evaluations",
    kicker: "Transparent model runs",
    summary: "Review configuration, baseline assumptions, run state, and reproducible savings estimates.",
    primaryMetric: "18",
    primaryLabel: "Evaluation runs",
    secondaryMetric: "2",
    secondaryLabel: "Awaiting approval",
    status: "queued",
    icon: TestTube2
  },
  anomalies: {
    title: "Anomaly review",
    kicker: "Quality and savings outliers",
    summary: "Prioritize unusual consumption, participation gaps, and result changes that need analyst review.",
    primaryMetric: "11",
    primaryLabel: "Open anomalies",
    secondaryMetric: "4",
    secondaryLabel: "High severity",
    status: "failed",
    icon: AlertTriangle
  },
  reports: {
    title: "Evidence reports",
    kicker: "Export center",
    summary: "Package approved results with source links, assumptions, limitations, and audit-friendly summaries.",
    primaryMetric: "6",
    primaryLabel: "Draft packages",
    secondaryMetric: "2",
    secondaryLabel: "Ready to export",
    status: "passed",
    icon: FileText
  },
  audit: {
    title: "Audit trail",
    kicker: "Sensitive actions",
    summary: "Inspect tenant actions across uploads, evaluations, assistant prompts, report exports, and access changes.",
    primaryMetric: "1,284",
    primaryLabel: "Recorded events",
    secondaryMetric: "0",
    secondaryLabel: "Policy exceptions",
    status: "passed",
    icon: ShieldCheck
  },
  usage: {
    title: "Usage and cost",
    kicker: "Operational visibility",
    summary: "Track tenant activity, AI usage, storage growth, and workflow volume for responsible operation.",
    primaryMetric: "73%",
    primaryLabel: "Monthly activity",
    secondaryMetric: "$412",
    secondaryLabel: "Projected AI cost",
    status: "running",
    icon: Gauge
  },
  settings: {
    title: "Workspace settings",
    kicker: "Tenant administration",
    summary: "Configure workspace identity, module access, report defaults, and governance preferences.",
    primaryMetric: "9",
    primaryLabel: "Active members",
    secondaryMetric: "4",
    secondaryLabel: "Enabled modules",
    status: "queued",
    icon: ShieldCheck
  }
};

export function DashboardPage() {
  return <ProductPage model={pageModels.dashboard} />;
}

export function AssistantPage() {
  return <ProductPage model={pageModels.assistant} />;
}

export function DatasetsPage() {
  return <ProductPage model={pageModels.datasets} />;
}

export function EvaluationsPage() {
  return <ProductPage model={pageModels.evaluations} />;
}

export function AnomaliesPage() {
  return <ProductPage model={pageModels.anomalies} />;
}

export function ReportsPage() {
  return <ProductPage model={pageModels.reports} />;
}

export function AuditPage() {
  return <ProductPage model={pageModels.audit} />;
}

export function UsagePage() {
  return <ProductPage model={pageModels.usage} />;
}

export function SettingsPage() {
  return <ProductPage model={pageModels.settings} />;
}

function ProductPage({ model }: { model: PageModel }) {
  const Icon = model.icon;
  return (
    <section className="product-page" aria-labelledby={`${model.title}-title`}>
      <div className="page-heading">
        <div>
          <p className="eyebrow">{model.kicker}</p>
          <h2 id={`${model.title}-title`}>{model.title}</h2>
          <p>{model.summary}</p>
        </div>
        <StatusBadge tone={model.status}>{model.status}</StatusBadge>
      </div>

      <div className="metric-grid">
        <article>
          <Icon size={22} />
          <strong>{model.primaryMetric}</strong>
          <span>{model.primaryLabel}</span>
        </article>
        <article>
          <TrendingUp size={22} />
          <strong>{model.secondaryMetric}</strong>
          <span>{model.secondaryLabel}</span>
        </article>
      </div>

      <div className="state-grid">
        <LoadingState label="Refreshing tenant-scoped summary" />
        <ErrorState title="API boundary not connected" message="Feature data will bind to service endpoints as related API tasks land." />
        <EmptyState title="No permanent fake data" message="This scaffold uses static screen states only to establish layout and behavior." />
      </div>
    </section>
  );
}
