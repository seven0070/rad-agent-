/** Artifact explorer. Registered artifacts only — no arbitrary filesystem access,
 *  no shell. View = redacted text preview served by the backend. */
import { useCallback, useEffect, useState } from "react";
import { ApiError, Artifact, ArtifactContent, WhyArtifact } from "../api";
import { useRad } from "../ctx";
import { fmtBytes, fmtTime, redactText, shortHash } from "../util";

export default function Artifacts() {
  const { client, selected } = useRad();
  const [rows, setRows] = useState<Artifact[]>([]);
  const [sel, setSel] = useState<string | null>(null);
  const [content, setContent] = useState<ArtifactContent | null>(null);
  const [why, setWhy] = useState<WhyArtifact | null>(null);
  const [err, setErr] = useState("");
  const id = selected?.id;

  useEffect(() => {
    if (!id) {
      setRows([]);
      setSel(null);
      setContent(null);
      setWhy(null);
      return;
    }
    let stop = false;
    const tick = async () => {
      try {
        const r = await client.artifacts(id);
        if (stop) return;
        setRows(r.artifacts);
        setErr("");
      } catch (e) {
        if (!stop) setErr(e instanceof ApiError ? e.message : String(e));
      }
    };
    void tick();
    const t = setInterval(tick, 6000);
    return () => {
      stop = true;
      clearInterval(t);
    };
  }, [client, id]);

  const open = useCallback(
    async (a: Artifact) => {
      if (!id) return;
      setSel(a.id);
      setContent(null);
      setWhy(null);
      setErr("");
      try {
        const [c, w] = await Promise.all([
          client.artifactContent(id, a.id).catch((e: unknown) => (e instanceof ApiError ? null : null)),
          client.why(id, a.location).catch(() => null),
        ]);
        if (c) setContent(c);
        else {
          // preview unsupported (binary / too large / moved) — still show provenance
          setContent(null);
        }
        if (w && "artifact" in w) setWhy(w as WhyArtifact);
      } catch (e) {
        setErr(e instanceof ApiError ? e.message : String(e));
      }
    },
    [client, id],
  );

  if (!id) {
    return (
      <div>
        <h1>Artifacts</h1>
        <p className="lead">Select an objective to inspect its artifacts and provenance.</p>
      </div>
    );
  }

  const selRow = rows.find((r) => r.id === sel);

  return (
    <div>
      <h1>Artifacts</h1>
      <p className="lead">
        Files and references recorded by the Observer for {id}. Preview is redacted text;
        there is no arbitrary file access or shell from the desktop.
      </p>
      {err && <p className="err">{err}</p>}
      <div className="row art-row">
        <div className="card art-list">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>path</th>
                  <th>task</th>
                  <th>ver</th>
                  <th>sha256</th>
                  <th>size</th>
                  <th>created</th>
                  <th>verif.</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((a) => (
                  <tr
                    key={a.id}
                    onClick={() => void open(a)}
                    className={`selectable${sel === a.id ? " is-selected" : ""}`}
                  >
                    <td title={a.location}>{a.location.split("/").slice(-2).join("/")}</td>
                    <td className="hint">{a.task_id}</td>
                    <td className="hint">v{a.version}</td>
                    <td className="hint">{shortHash(a.sha256)}</td>
                    <td className="hint">{fmtBytes(a.size)}</td>
                    <td className="hint">{fmtTime(a.at)}</td>
                    <td>
                      {a.verification && Object.keys(a.verification).length > 0 ? (
                        <span
                          className={`badge ${
                            a.verification.ok === false ? "b-bad" : a.verification.ok === true ? "b-ok" : "b-warn"
                          }`}
                        >
                          {String(a.verification.status || (a.verification.ok ? "ok" : "recorded"))}
                        </span>
                      ) : (
                        <span className="hint">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={7} className="hint">
                      no artifacts recorded yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {selRow && (
          <div className="card art-detail">
            <div className="row justify-between">
              <b className="break-all">{selRow.location}</b>
              <span className="hint">
                {selRow.creator} · v{selRow.version} · {fmtBytes(selRow.size)}
              </span>
            </div>
            <div className="hint mt-4">
              sha256 {shortHash(selRow.sha256, 20)} · {fmtTime(selRow.at)}
            </div>

            {why && (
              <div className="mt-10">
                <label>Provenance (why this artifact exists)</label>
                <div className="chain">
                  <div className="chain-step">
                    <b>Objective</b>
                    <div className="hint">{id}</div>
                  </div>
                  <div className="chain-step">
                    <b>Task</b>
                    <div className="hint">
                      {why.task.text || why.task.id} {why.task.attempt ? `(attempt ${why.task.attempt})` : ""}
                    </div>
                  </div>
                  <div className="chain-step">
                    <b>Action</b>
                    <div className="hint">
                      {why.action ? `${why.action.tool} (${why.action.status})` : "not recorded"}
                    </div>
                  </div>
                  <div className="chain-step">
                    <b>Artifact</b>
                    <div className="hint">
                      {why.versions.length} version(s) · {why.artifact.location}
                    </div>
                  </div>
                  <div className="chain-step">
                    <b>Verification</b>
                    <div className="hint">
                      {Object.keys(why.verification || {}).length
                        ? redactText(JSON.stringify(why.verification)).slice(0, 160)
                        : "recorded, no verification attached"}
                    </div>
                  </div>
                </div>
                {why.evidence.length > 0 && (
                  <div className="mt-8">
                    <label>Evidence (before this action, same task)</label>
                    {why.evidence.slice(0, 6).map((e, i) => {
                      const ee = e as { source?: string; tool?: string; trusted?: boolean; excerpt?: string };
                      return (
                        <div key={i} className="hint mb-4">
                          {ee.trusted === false ? "⚠ untrusted " : ""}
                          {ee.source || ee.tool || "evidence"}:{" "}
                          {redactText(String(ee.excerpt || "")).slice(0, 180)}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            <div className="mt-10">
              <label>Content preview (redacted)</label>
              {content ? (
                <pre className="art-pre">
                  {redactText(content.preview)}
                  {content.truncated ? "\n… (truncated to first 400 lines)" : ""}
                </pre>
              ) : (
                <div className="hint">
                  no text preview (binary file, too large, or not on disk)
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
