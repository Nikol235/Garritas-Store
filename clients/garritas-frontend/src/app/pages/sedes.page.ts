import { Component, inject } from "@angular/core";
import { Router } from "@angular/router";
import { SedesComponent } from "../features/sedes/sedes.component";

@Component({
  selector: "app-sedes-page",
  imports: [SedesComponent],
  template: `
    <app-sedes
      (servicios)="openServicios($event)"
      (order)="router.navigate(['/nueva-orden'])"
    />
  `,
})
export class SedesPage {
  readonly router = inject(Router);

  openServicios(id: number) {
    sessionStorage.setItem("garritas-servicios-sede", String(id));
    this.router.navigate(["/prestaciones"]);
  }
}
