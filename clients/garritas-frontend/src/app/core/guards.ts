import { inject } from "@angular/core";
import { CanActivateFn, Router } from "@angular/router";
import { Auth } from "./auth";

/** Ruta a la que volver después de iniciar sesión (Keycloak siempre redirige a "/"). */
export const RETURN_URL_KEY = "garritas-return-url";

/** Requiere sesión iniciada; si no hay, guarda la ruta pedida y envía a Keycloak. */
export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(Auth);
  if (auth.loggedIn()) return true;
  sessionStorage.setItem(RETURN_URL_KEY, state.url);
  auth.login();
  return false;
};

/** Solo administradores (rol ADMIN de Keycloak). */
export const adminGuard: CanActivateFn = () => {
  const auth = inject(Auth);
  if (auth.admin()) return true;
  return inject(Router).createUrlTree(["/catalogo"]);
};

/** Solo clientes: los administradores no compran (carrito, nueva orden). */
export const clienteGuard: CanActivateFn = () => {
  const auth = inject(Auth);
  if (!auth.admin()) return true;
  return inject(Router).createUrlTree(["/catalogo"]);
};
