const toBasicAuth = (username, password) => {
  return `Basic ${btoa(`${username}:${password}`)}`;
};

async function apiRequest({
  baseUrl,
  apiVersion,
  path,
  method = "GET",
  token,
  basicAuth,
  body,
}) {
  const url = `${baseUrl.replace(/\/$/, "")}/api/v${apiVersion}${path}`;
  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (basicAuth) {
    headers.Authorization = basicAuth;
  }

  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let payload = null;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }

  if (!res.ok) {
    const message =
      payload?.msg || payload?.detail || `${res.status} ${res.statusText}`;
    const err = new Error(message);
    err.status = res.status;
    err.payload = payload;
    throw err;
  }

  return payload;
}

export function isAuthError(error) {
  return error?.status === 401 || error?.status === 403;
}

export async function loginBasic({
  baseUrl,
  apiVersion,
  username,
  password,
}) {
  return apiRequest({
    baseUrl,
    apiVersion,
    path: "/auth/login",
    method: "POST",
    basicAuth: toBasicAuth(username, password),
  });
}

export async function getSystemPing({ baseUrl, apiVersion }) {
  return apiRequest({ baseUrl, apiVersion, path: "/system/ping" });
}

export async function getSystemHealth({ baseUrl, apiVersion }) {
  return apiRequest({ baseUrl, apiVersion, path: "/system/health" });
}

export async function getDashboardMetrics({ baseUrl, apiVersion, token }) {
  return apiRequest({ baseUrl, apiVersion, path: "/dashboard/metrics", token });
}

export async function getRecentActivity({
  baseUrl,
  apiVersion,
  token,
  limit = 10,
}) {
  return apiRequest({
    baseUrl,
    apiVersion,
    path: `/dashboard/recent-activity?limit=${limit}`,
    token,
  });
}

export async function listTickets({
  baseUrl,
  apiVersion,
  token,
  page = 1,
  limit = 50,
  status,
}) {
  const qs = new URLSearchParams();
  qs.set("page", String(page));
  qs.set("limit", String(limit));
  if (status) {
    qs.set("status", status);
  }
  return apiRequest({
    baseUrl,
    apiVersion,
    path: `/tickets/?${qs.toString()}`,
    token,
  });
}

export async function getTicket({ baseUrl, apiVersion, ticketId, token }) {
  return apiRequest({
    baseUrl,
    apiVersion,
    path: `/tickets/${encodeURIComponent(ticketId)}`,
    token,
  });
}

export async function getTicketStatus({ baseUrl, apiVersion, ticketId, token }) {
  return apiRequest({
    baseUrl,
    apiVersion,
    path: `/tickets/${encodeURIComponent(ticketId)}/status`,
    token,
  });
}

export async function patchTicketStatus({
  baseUrl,
  apiVersion,
  ticketId,
  status,
  token,
}) {
  return apiRequest({
    baseUrl,
    apiVersion,
    path: `/tickets/${encodeURIComponent(ticketId)}/status`,
    method: "PATCH",
    token,
    body: { status },
  });
}

export async function getAuditLogs({ baseUrl, apiVersion, ticketId, token }) {
  return apiRequest({
    baseUrl,
    apiVersion,
    path: `/audit/${encodeURIComponent(ticketId)}`,
    token,
  });
}
