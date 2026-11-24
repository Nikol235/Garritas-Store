import { Component, inject } from "@angular/core";
import { Auth } from "../core/auth";
import { CuentaComponent } from "../features/cuenta/cuenta.component";

@Component({
  selector: "app-cuenta-page",
  imports: [CuentaComponent],
  template: `
    <button (click)="auth.manageAccount()">Cambiar contraseña en Keycloak</button>
    <app-cuenta />
  `,
})
export class CuentaPage {
  readonly auth = inject(Auth);
}
