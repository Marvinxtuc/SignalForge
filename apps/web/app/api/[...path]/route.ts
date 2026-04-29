import { SERVER_API_BASE_URL } from "../../../lib/constants";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteContext = {
  params: Promise<{ path?: string[] }> | { path?: string[] };
};

const BLOCKED_REQUEST_HEADERS = new Set([
  "authorization",
  "connection",
  "cookie",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "sf-token",
  "sf_token",
  "x-sf-token",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade"
]);

const BLOCKED_RESPONSE_HEADERS = new Set(["connection", "content-encoding", "set-cookie"]);

export async function GET(request: Request, context: RouteContext) {
  return proxyBackendRequest(request, context);
}

export async function POST(request: Request, context: RouteContext) {
  return proxyBackendRequest(request, context);
}

export async function PUT(request: Request, context: RouteContext) {
  return proxyBackendRequest(request, context);
}

export async function PATCH(request: Request, context: RouteContext) {
  return proxyBackendRequest(request, context);
}

export async function DELETE(request: Request, context: RouteContext) {
  return proxyBackendRequest(request, context);
}

export async function OPTIONS(request: Request, context: RouteContext) {
  return proxyBackendRequest(request, context);
}

export async function HEAD(request: Request, context: RouteContext) {
  return proxyBackendRequest(request, context);
}

async function proxyBackendRequest(request: Request, context: RouteContext): Promise<Response> {
  try {
    const targetUrl = await buildTargetUrl(request, context);
    const body = await getRequestBody(request);

    const upstreamResponse = await fetch(targetUrl, {
      body,
      cache: "no-store",
      headers: getForwardHeaders(request.headers),
      method: request.method,
      redirect: "manual"
    });

    return new Response(upstreamResponse.body, {
      headers: getResponseHeaders(upstreamResponse.headers),
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText
    });
  } catch {
    return Response.json(
      {
        error: {
          code: "backend_proxy_unavailable",
          message: "SignalForge backend is unavailable through the web proxy.",
          details: {}
        }
      },
      {
        status: 502,
        headers: {
          "Cache-Control": "no-store"
        }
      }
    );
  }
}

async function buildTargetUrl(request: Request, context: RouteContext): Promise<URL> {
  const incomingUrl = new URL(request.url);
  const params = await Promise.resolve(context.params);
  const path = (params.path ?? []).join("/");
  const upstreamPath = path === "health" ? "/health" : `/api/${path}`;
  const targetUrl = new URL(upstreamPath, `${SERVER_API_BASE_URL}/`);

  incomingUrl.searchParams.forEach((value, key) => {
    if (key !== "sf_token") {
      targetUrl.searchParams.append(key, value);
    }
  });

  return targetUrl;
}

async function getRequestBody(request: Request): Promise<ArrayBuffer | undefined> {
  if (request.method === "GET" || request.method === "HEAD") {
    return undefined;
  }

  const body = await request.arrayBuffer();
  return body.byteLength > 0 ? body : undefined;
}

function getForwardHeaders(headers: Headers): Headers {
  const forwardHeaders = new Headers();

  headers.forEach((value, key) => {
    if (!BLOCKED_REQUEST_HEADERS.has(key.toLowerCase())) {
      forwardHeaders.set(key, value);
    }
  });

  return forwardHeaders;
}

function getResponseHeaders(headers: Headers): Headers {
  const responseHeaders = new Headers();

  headers.forEach((value, key) => {
    if (!BLOCKED_RESPONSE_HEADERS.has(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });

  return responseHeaders;
}
