import { Component, inject } from "@angular/core";
import { Router } from "@angular/router";
import { CitasComponent } from "../features/citas/citas.component";

@Component({
  selector: "app-citas-page",
  imports: [CitasComponent],
  template: `<app-citas (cuenta)="router.navigate(['/cuenta'])" />`,
})
export class CitasPage {
  readonly router = inject(Router);
}
