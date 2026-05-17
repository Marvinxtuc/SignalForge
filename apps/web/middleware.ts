import { NextResponse, type NextRequest } from "next/server";
import {
  hasValidOwnerSession,
  isOwnerAuthRequired,
  ownerAuthConfigError
} from "./lib/ownerAuth";

const PROTECTED_PAGE_PREFIXES = [
  "/signals",
  "/dashboard",
  "/reports",
  "/settings",
  "/logs",
  "/opportunities",
  "/onboarding",
  "/production"
];

export function middleware(request: NextRequest) {
  if (!isOwnerAuthRequired()) {
    return NextResponse.next();
  }

  const { pathname, search } = request.nextUrl;
  const isApiRequest = pathname === "/api" || pathname.startsWith("/api/");
  const isProtectedPage = PROTECTED_PAGE_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );

  if (pathname === "/login") {
    if (hasValidOwnerSession(request)) {
      return NextResponse.redirect(new URL("/signals", request.url));
    }

    return NextResponse.next();
  }

  if (!isApiRequest && !isProtectedPage) {
    return NextResponse.next();
  }

  const configError = ownerAuthConfigError();
  if (configError) {
    return authFailure(request, "owner_auth_misconfigured", configError, 503);
  }

  if (hasValidOwnerSession(request)) {
    return NextResponse.next();
  }

  if (isApiRequest) {
    return authFailure(request, "owner_auth_required", "Owner session is required.", 401);
  }

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", `${pathname}${search}`);
  return NextResponse.redirect(loginUrl);
}

function authFailure(request: NextRequest, code: string, message: string, status: number) {
  if (request.nextUrl.pathname.startsWith("/api/") || request.nextUrl.pathname === "/api") {
    return Response.json(
      {
        error: {
          code,
          message,
          details: {}
        }
      },
      {
        status,
        headers: {
          "Cache-Control": "no-store"
        }
      }
    );
  }

  return new NextResponse(message, {
    status,
    headers: {
      "Cache-Control": "no-store",
      "Content-Type": "text/plain; charset=utf-8"
    }
  });
}

export const config = {
  matcher: [
    "/api/:path*",
    "/dashboard/:path*",
    "/logs/:path*",
    "/login",
    "/onboarding/:path*",
    "/opportunities/:path*",
    "/production/:path*",
    "/reports/:path*",
    "/settings/:path*",
    "/signals/:path*"
  ]
};
