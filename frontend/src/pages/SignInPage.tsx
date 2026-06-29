import { ArrowRight, Building2, ShieldCheck } from "lucide-react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { BrandMark } from "../components/BrandMark";
import { useSession } from "../features/auth/session";

export function SignInPage() {
  const navigate = useNavigate();
  const { signIn } = useSession();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    signIn();
    navigate("/workspaces", { replace: true });
  }

  return (
    <main className="signin-screen">
      <section className="signin-story" aria-label="GridLens product summary">
        <BrandMark />
        <div>
          <h1>Turn messy utility data into evidence you can defend.</h1>
          <p>Ingest, validate, evaluate, and explain energy-program results safely, per tenant.</p>
        </div>
        <div className="story-points">
          <article>
            <ShieldCheck size={20} />
            <span>
              <strong>Tenant-isolated by design</strong>
              <small>Data, prompts, and reports stay inside the selected workspace.</small>
            </span>
          </article>
          <article>
            <Building2 size={20} />
            <span>
              <strong>Every metric traces to its source</strong>
              <small>Datasets, versions, assumptions, and limitations remain visible.</small>
            </span>
          </article>
        </div>
      </section>

      <section className="signin-form-panel" aria-labelledby="signin-title">
        <p className="eyebrow">Invitation gated access</p>
        <h2 id="signin-title">Sign in</h2>
        <p>Use the development sign-in to exercise protected route and workspace behavior.</p>
        <form onSubmit={handleSubmit}>
          <label>
            Work email
            <input type="email" defaultValue="mara.quinn@northwind.example" />
          </label>
          <button className="primary-button" type="submit">
            Continue
            <ArrowRight size={16} />
          </button>
        </form>
      </section>
    </main>
  );
}
