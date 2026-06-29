export function BrandMark({ label = "GridLens" }: { label?: string }) {
  return (
    <div className="brand-lockup" aria-label={label}>
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </span>
      <span className="brand-name">{label}</span>
    </div>
  );
}
