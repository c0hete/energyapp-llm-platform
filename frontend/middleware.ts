import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Versión actual del build
  const currentVersion = process.env.NEXT_PUBLIC_BUILD_ID || "default";

  // Versión almacenada en cookies del cliente
  const clientVersion = request.cookies.get("build_version")?.value;

  // Si el cliente tiene una versión diferente → invalida sesión y envía a login
  if (clientVersion && clientVersion !== currentVersion) {
    const loginResponse = NextResponse.redirect(new URL("/login", request.url));

    // Limpia la sesión vieja
    loginResponse.cookies.set({
      name: "session_token",
      value: "",
      path: "/",
      maxAge: 0,
    });

    // Almacena la nueva versión del build
    loginResponse.cookies.set({
      name: "build_version",
      value: currentVersion,
      path: "/",
      maxAge: 31536000, // 1 año
    });

    return loginResponse;
  }

  // En la primera carga o después de limpiar → guarda la versión del build
  response.cookies.set({
    name: "build_version",
    value: currentVersion,
    path: "/",
    maxAge: 31536000, // 1 año
  });

  // No-cache headers para prevenir HTML cacheado
  response.headers.set("Cache-Control", "no-store, no-cache, must-revalidate");
  response.headers.set("Pragma", "no-cache");
  response.headers.set("Expires", "0");

  // Permitir eval para React/Next.js (desarrollo y producción)
  response.headers.set(
    "Content-Security-Policy",
    "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://energyapp.alvaradomazzei.cl;"
  );

  return response;
}

// Aplicar middleware a todas las rutas excepto assets estáticos
export const config = {
  matcher: [
    /*
     * Excluir:
     * - api (manejar aparte)
     * - _next/static (archivos estáticos)
     * - _next/image (optimización de imágenes)
     * - favicon.ico (favicon)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
