import { Component, inject } from "@angular/core";
import { Router } from "@angular/router";
import { EspecialistasComponent } from "../features/bienestar/especialistas.component";

@Component({
  selector: "app-especialistas-page",
  imports: [EspecialistasComponent],
  template: `<app-especialistas (reservar)="openCitas($event)" />`,
})
export class EspecialistasPage {
  private readonly router = inject(Router);

  openCitas(id: number) {
    sessionStorage.setItem("garritas-profesional", String(id));
    // Sin sesión, authGuard envía a Keycloak y luego vuelve a /citas
    this.router.navigate(["/citas"]);
  }
}
