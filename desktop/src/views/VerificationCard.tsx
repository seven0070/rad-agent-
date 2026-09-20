import { TaskRow, Verification } from "../api";

/**
 * Renders a backend verification object as-is. Desktop never computes a pass:
 * the "VERIFIED" judgement comes only from the control plane.
 */
export const NO_VERIFIED_COPY = "No machine-check pass ⇒ No VERIFIED";

function chipClass(v: string | undefined | null) {
  return `chip ${(v || "pending").toLowerCase()}`;
}

const HIDDEN_KEYS = new Set(["checks", "tasks"]);

export function VerificationCard({
  verification,
  tasks,
}: {
  verification?: Verification | null;
  tasks?: TaskRow[];
}) {
  const checks = Array.isArray(verification?.checks)
    ? (verification.checks as Array<Record<string, unknown>>)
    : [];
  const kv = verification ? Object.entries(verification).filter(([k]) => !HIDDEN_KEYS.has(k)) : [];

  return (
    <div className="card">
      <h3>Verification</h3>
      {!verification || kv.length === 0 ? (
        <p className="meta">{NO_VERIFIED_COPY}</p>
      ) : (
        <>
          <div className="row" style={{ marginBottom: 8 }}>
            <span className={chipClass(verification.status)}>{verification.status || "pending"}</span>
          </div>
          <div className="kv">
            {kv.map(([k, v]) => (
              <div key={k} className="kv-row">
                <span className="k">{k}</span>
                <span className="v mono">
                  {typeof v === "object" && v !== null ? JSON.stringify(v) : String(v)}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
      {checks.length > 0 && (
        <div className="checks" style={{ marginTop: 10 }}>
          {checks.map((c, i) => {
            const st = typeof c.status === "string" ? c.status : "unknown";
            const pass = st === "ok" || st === "passed" || st === "true" || st === "verified";
            const msg = String(c.summary ?? c.message ?? c.name ?? c.check ?? "");
            return (
              <div key={i} className={`check ${pass ? "ok" : "bad"}`}>
                <span className={chipClass(st)}>{st}</span>
                <span>{msg}</span>
              </div>
            );
          })}
        </div>
      )}
      {tasks && tasks.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <table>
            <thead>
              <tr>
                <th>status</th>
                <th>verified</th>
                <th>task</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td>{t.status}</td>
                  <td>{t.verification?.status || "—"}</td>
                  <td>{t.title || t.text || t.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}