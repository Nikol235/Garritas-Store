import { Component, inject } from "@angular/core";
import { Router } from "@angular/router";
import { PlanesComponent } from "../features/planes/planes.component";

@Component({
  selector: "app-planes-page",
  imports: [PlanesComponent],
  template: `<app-planes (cuenta)="router.navigate(['/cuenta'])" />`,
})
export class PlanesPage {
  readonly router = inject(Router);
}
