/**
 * Errors from the Nebula gateway as the console shows them.
 *
 * The console maps the HTTP status to a Spanish message; the gateway's English `detail` is kept on
 * the error object but never shown. The Next proxies answer 503 `gateway_unreachable` when the
 * gateway does not answer at all.
 */

export const GATEWAY_UNREACHABLE_DETAIL = "gateway_unreachable";

const REJECTED_DATA = "El gateway rechazó los datos.";

/** Fields named by a FastAPI 422 list: the last named `loc` element of each entry, once each. */
function invalidFields(detail: unknown): string[] {
  if (!Array.isArray(detail)) {
    return [];
  }
  const fields: string[] = [];
  for (const entry of detail) {
    const loc: unknown = typeof entry === "object" && entry !== null ? (entry as { loc?: unknown }).loc : null;
    const named = Array.isArray(loc) ? loc.filter((part): part is string => typeof part === "string") : [];
    const field = named[named.length - 1];
    if (field && !fields.includes(field)) {
      fields.push(field);
    }
  }
  return fields;
}

function adminErrorMessage(status: number, detail: unknown, retryAfterSeconds: number | null) {
  if (status === 503 && detail === GATEWAY_UNREACHABLE_DETAIL) {
    return "No se pudo conectar con el gateway.";
  }
  switch (status) {
    case 401:
      return "La clave de admin no es válida.";
    case 403:
      return "Acción no permitida.";
    case 404:
      return "No se encontró el recurso.";
    case 409:
      return "Ya existe un recurso con ese identificador.";
    case 422: {
      const fields = invalidFields(detail);
      return fields.length > 0 ? `Revisar los campos: ${fields.join(", ")}.` : REJECTED_DATA;
    }
    case 400:
      return REJECTED_DATA;
    case 429:
      return retryAfterSeconds === null
        ? "Demasiados pedidos. Reintentar en unos segundos."
        : `Demasiados pedidos. Reintentar en ${retryAfterSeconds} s.`;
    default:
      return `El gateway devolvió un error (${status}).`;
  }
}

/** `Retry-After` in whole seconds; an HTTP date or anything else is not worth showing. */
function parseRetryAfter(value: string | null): number | null {
  if (value === null || !/^\d+$/.test(value.trim())) {
    return null;
  }
  const seconds = Number(value.trim());
  return seconds > 0 ? seconds : null;
}

export class AdminApiError extends Error {
  readonly status: number;
  readonly detail: unknown;
  readonly retryAfterSeconds: number | null;

  constructor(status: number, detail: unknown, retryAfterSeconds: number | null = null) {
    super(adminErrorMessage(status, detail, retryAfterSeconds));
    this.name = "AdminApiError";
    this.status = status;
    this.detail = detail;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

/** What a Next proxy answers when the gateway does not. */
export function gatewayUnreachableResponse(): Response {
  return Response.json({ detail: GATEWAY_UNREACHABLE_DETAIL }, { status: 503 });
}

/** Builds the error for a non-2xx response; the body may be anything (HTML from a Next 500, say). */
export async function adminErrorFromResponse(response: Response): Promise<AdminApiError> {
  const body: unknown = await response.json().catch(() => null);
  const detail = typeof body === "object" && body !== null ? ((body as { detail?: unknown }).detail ?? null) : null;
  return new AdminApiError(response.status, detail, parseRetryAfter(response.headers.get("Retry-After")));
}

/** `fetch` for the gateway proxies: a request that cannot be sent is the unreachable error. */
export async function gatewayFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init);
  } catch {
    throw new AdminApiError(503, GATEWAY_UNREACHABLE_DETAIL);
  }
}
