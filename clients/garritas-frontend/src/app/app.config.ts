import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from "@angular/core";
import { provideHttpClient, withInterceptors } from "@angular/common/http";
import {
  provideRouter,
  withComponentInputBinding,
  withInMemoryScrolling,
} from "@angular/router";
import { routes } from "./app.routes";
import { Auth } from "./core/auth";
import { authInterceptor } from "./core/interceptor";

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideHttpClient(withInterceptors([authInterceptor])),
    // Keycloak se inicializa antes de la primera navegación: los guards ya saben si hay sesión
    provideAppInitializer(() => inject(Auth).init()),
    provideRouter(
      routes,
      withComponentInputBinding(),
      withInMemoryScrolling({ scrollPositionRestoration: "top" }),
    ),
  ],
};
