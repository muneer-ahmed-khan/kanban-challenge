export async function api(path, method = 'GET', body) {
  const response = await fetch(`/api${path}`, {
    method,
    credentials: 'same-origin',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error('The server returned an unreadable response. Try again.');
  }
  if (!response.ok) {
    const error = new Error(data.error || 'The request failed. Try again.');
    error.status = response.status;
    throw error;
  }
  return data;
}

export function isOverdue(date) {
  if (!date) return false;
  const today = new Date();
  const localToday = [today.getFullYear(), String(today.getMonth() + 1).padStart(2, '0'), String(today.getDate()).padStart(2, '0')].join('-');
  return date < localToday;
}

export function formatDate(date) {
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${date}T00:00:00`));
}
