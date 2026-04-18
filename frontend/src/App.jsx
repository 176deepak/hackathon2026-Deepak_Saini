import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getAuditLogs,
  getDashboardMetrics,
  getRecentActivity,
  getTicket,
  getTicketStatus,
  isAuthError,
  listTickets,
  loginBasic,
  patchTicketStatus,
} from "./api";

const STATUS_OPTIONS = [
  "pending",
  "processing",
  "resolved",
  "escalated",
  "waiting_for_customer",
  "failed",
];

const RECENT_PAGE_SIZE = 3;

function App() {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  const apiVersion = String(import.meta.env.VITE_API_VERSION || "1");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState(() => localStorage.getItem("dash_token") || "");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dashboardError, setDashboardError] = useState("");

  const [metrics, setMetrics] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [recentVisibleCount, setRecentVisibleCount] = useState(RECENT_PAGE_SIZE);

  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [selectedStatus, setSelectedStatus] = useState("");
  const [audit, setAudit] = useState(null);

  const authReady = useMemo(() => Boolean(token), [token]);
  const visibleRecent = useMemo(
    () => recentActivity.slice(0, recentVisibleCount),
    [recentActivity, recentVisibleCount],
  );
  const canLoadMoreRecent = recentVisibleCount < recentActivity.length;

  const runAuthLogin = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const res = await loginBasic({
        baseUrl,
        apiVersion,
        username,
        password,
      });
      const t = res?.data?.access_token || "";
      if (!t) {
        throw new Error("Login succeeded but token missing");
      }
      setToken(t);
      localStorage.setItem("dash_token", t);
    } catch (e) {
      setError(e.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }, [apiVersion, baseUrl, password, username]);

  const loadTickets = useCallback(async () => {
    const ticketRes = await listTickets({
      baseUrl,
      apiVersion,
      token,
      page: 1,
      limit: 100,
    });
    const rows = ticketRes?.data?.items || [];
    setTickets(rows);
    return rows;
  }, [apiVersion, baseUrl, token]);

  const selectTicket = useCallback(
    async (ticketId, ticketList = []) => {
      setDashboardError("");
      const tRes = await getTicket({ baseUrl, apiVersion, ticketId, token });
      const sRes = await getTicketStatus({ baseUrl, apiVersion, ticketId, token });

      let auditData = { ticket_id: ticketId, runs: [] };
      try {
        const aRes = await getAuditLogs({ baseUrl, apiVersion, ticketId, token });
        auditData = aRes?.data || auditData;
      } catch {
        auditData = { ticket_id: ticketId, runs: [] };
      }

      const listMeta = ticketList.find((t) => t.ticket_id === ticketId);
      const detail = tRes?.data || {};
      const statusPayload = sRes?.data || {};

      const combined = {
        ticket_id: detail.ticket_id || ticketId,
        customer_email: detail.customer_email || listMeta?.customer_email || "-",
        subject: detail.subject || listMeta?.subject || "-",
        body: detail.body || "-",
        status: statusPayload.status || listMeta?.status || "pending",
      };
      setSelectedTicket(combined);
      setSelectedStatus(combined.status);
      setAudit(auditData);
    },
    [apiVersion, baseUrl, token],
  );

  const loadDashboard = useCallback(async () => {
    setDashboardError("");
    setLoading(true);
    try {
      const rows = await loadTickets();
      setRecentVisibleCount(RECENT_PAGE_SIZE);

      if (token) {
        const [mRes, rRes] = await Promise.all([
          getDashboardMetrics({ baseUrl, apiVersion, token }),
          getRecentActivity({ baseUrl, apiVersion, token, limit: 50 }),
        ]);
        setMetrics(mRes?.data || null);
        setRecentActivity(rRes?.data?.items || []);
      }

      if (rows.length > 0) {
        await selectTicket(rows[0].ticket_id, rows);
      } else {
        setSelectedTicket(null);
        setAudit({ runs: [] });
      }
    } catch (e) {
      if (isAuthError(e)) {
        localStorage.removeItem("dash_token");
        setToken("");
        setDashboardError("");
        setError("Session expired. Please login again.");
        return;
      }
      setDashboardError(e.message || "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [apiVersion, baseUrl, loadTickets, selectTicket, token]);

  const saveStatus = useCallback(async () => {
    if (!selectedTicket?.ticket_id || !selectedStatus) {
      return;
    }
    setDashboardError("");
    setLoading(true);
    try {
      await patchTicketStatus({
        baseUrl,
        apiVersion,
        ticketId: selectedTicket.ticket_id,
        status: selectedStatus,
        token,
      });
      await loadDashboard();
    } catch (e) {
      setDashboardError(e.message || "Failed to update status");
    } finally {
      setLoading(false);
    }
  }, [apiVersion, baseUrl, loadDashboard, selectedStatus, selectedTicket, token]);

  const logout = useCallback(() => {
    localStorage.removeItem("dash_token");
    setToken("");
    setMetrics(null);
    setRecentActivity([]);
    setTickets([]);
    setSelectedTicket(null);
    setAudit(null);
    setDashboardError("");
    setError("");
  }, []);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      void loadDashboard();
    });
    return () => window.cancelAnimationFrame(frame);
  }, [loadDashboard]);

  if (!authReady) {
    return (
      <div className="login-page">
        <div className="login-card">
          <div className="brand login-brand">
            <div className="brand-mark">K</div>
            <div>
              <h1>KSolves</h1>
              <p>Support AI Dashboard Login</p>
            </div>
          </div>

          <h2>Authenticate to continue</h2>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>

          {error ? <div className="alert-error">{error}</div> : null}

          <button className="btn-primary" onClick={runAuthLogin} disabled={loading}>
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell dashboard-only">
      <main className="main full-width">
        <header className="topbar">
          <div>
            <h2>Autonomous Support Resolution Dashboard</h2>
          </div>
          <div className="actions">
            <button className="btn-secondary" onClick={loadDashboard} disabled={loading}>
              Refresh Dashboard
            </button>
            <button className="btn-ghost dark" onClick={logout}>
              Logout
            </button>
          </div>
        </header>

        {dashboardError ? <div className="alert-error">{dashboardError}</div> : null}

        <section className="grid-4">
          <article className="kpi"><span>Total</span><strong>{metrics?.total_tickets ?? "-"}</strong></article>
          <article className="kpi"><span>Resolved</span><strong>{metrics?.resolved ?? "-"}</strong></article>
          <article className="kpi"><span>Escalated</span><strong>{metrics?.escalated ?? "-"}</strong></article>
          <article className="kpi"><span>Failed</span><strong>{metrics?.failed ?? "-"}</strong></article>
        </section>

        <section className="panel two-col">
          <div>
            <h3>Tickets</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Email</th>
                    <th>Subject</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((t) => (
                    <tr
                      key={t.ticket_id}
                      onClick={() => selectTicket(t.ticket_id, tickets)}
                      className={selectedTicket?.ticket_id === t.ticket_id ? "selected" : ""}
                    >
                      <td>{t.ticket_id}</td>
                      <td>{t.customer_email}</td>
                      <td>{t.subject}</td>
                      <td>{t.status}</td>
                    </tr>
                  ))}
                  {tickets.length === 0 ? (
                    <tr>
                      <td colSpan={4}>No tickets found.</td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h3>Ticket Detail</h3>
            {selectedTicket ? (
              <div className="detail">
                <p><strong>ID:</strong> {selectedTicket.ticket_id}</p>
                <p><strong>Email:</strong> {selectedTicket.customer_email}</p>
                <p><strong>Subject:</strong> {selectedTicket.subject}</p>
                <p><strong>Body:</strong> {selectedTicket.body}</p>
                <div className="actions">
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                  <button className="btn-primary" onClick={saveStatus} disabled={loading}>
                    Update Status
                  </button>
                </div>
              </div>
            ) : (
              <p>Select a ticket to view details.</p>
            )}
          </div>
        </section>

        <section className="panel two-col">
          <div>
            <h3>Recent Activity (Protected API)</h3>
            <div className="recent-scroll">
              <ul className="activity-list">
                {visibleRecent.map((item) => (
                  <li
                    key={`${item.ticket_id}-${item.updated_at}`}
                    onClick={() => selectTicket(item.ticket_id, tickets)}
                    className="activity-item"
                  >
                    <strong>{item.ticket_id}</strong>
                    <span>{item.status}</span>
                    <small>{item.subject || "-"}</small>
                  </li>
                ))}
                {visibleRecent.length === 0 ? <li>No activity data.</li> : null}
              </ul>
            </div>
            {canLoadMoreRecent ? (
              <button
                className="btn-secondary load-more"
                onClick={() => setRecentVisibleCount((v) => v + RECENT_PAGE_SIZE)}
              >
                Load More
              </button>
            ) : null}
          </div>

          <div>
            <h3>Audit Timeline</h3>
            <div className="audit-wrap">
              {audit?.runs?.length ? (
                audit.runs.map((run) => (
                  <article key={run.run_id} className="audit-run">
                    <p><strong>Run:</strong> {run.run_id}</p>
                    <p><strong>Status:</strong> {run.status}</p>
                    <p><strong>Decision:</strong> {run.final_decision || "-"}</p>
                    <p><strong>Confidence:</strong> {run.confidence_score ?? "-"}</p>
                    <p><strong>Steps:</strong> {run.steps?.length || 0}</p>
                    <div className="audit-steps">
                      {(run.steps || []).map((step) => (
                        <div key={`${run.run_id}-${step.step_number}`} className="audit-step">
                          <p>
                            <strong>Step {step.step_number}:</strong>{" "}
                            {step.action || "-"} ({step.status || "-"})
                          </p>
                          <p><strong>Thought:</strong> {step.thought || "-"}</p>
                          <p><strong>At:</strong> {step.created_at || "-"}</p>
                          {(step.tool_calls || []).length ? (
                            <div className="audit-tools">
                              {(step.tool_calls || []).map((call, idx) => (
                                <div
                                  key={`${run.run_id}-${step.step_number}-${call.tool_name}-${idx}`}
                                  className="audit-tool"
                                >
                                  <p>
                                    <strong>Tool:</strong> {call.tool_name} ({call.status || "-"})
                                  </p>
                                  <p><strong>Error:</strong> {call.error || "-"}</p>
                                  <p><strong>At:</strong> {call.created_at || "-"}</p>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p><strong>Tool Calls:</strong> -</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </article>
                ))
              ) : (
                <p>No audit runs found for this ticket.</p>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
