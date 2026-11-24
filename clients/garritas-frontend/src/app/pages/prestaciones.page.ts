import { Component, inject } from "@angular/core";
import { Router } from "@angular/router";
import { Auth } from "../core/auth";
import { PrestacionesComponent } from "../features/prestaciones/prestaciones.component";

@Component({
  selector: "app-prestaciones-page",
  imports: [PrestacionesComponent],
  template: `<app-prestaciones (reservar)="openPrestacion($event)" />`,
})
export class PrestacionesPage {
  private readonly auth = inject(Auth);
  private readonly router = inject(Router);

  openPrestacion(event: { sedeId: number; prestacionId: number }) {
    if (this.auth.admin()) return;
    sessionStorage.setItem("garritas-cita-sede", String(event.sedeId));
    sessionStorage.setItem("garritas-cita-prestacion", String(event.prestacionId));
    // Sin sesión, authGuard envía a Keycloak y luego vuelve a /citas
    this.router.navigate(["/citas"]);
  }
}
