import { Component, inject } from "@angular/core";
import { Router } from "@angular/router";
import { Shop } from "../core/shop";
import { VentasComponent } from "../features/ventas/ventas.component";

@Component({
  selector: "app-compras-page",
  imports: [VentasComponent],
  template: `
    <app-ventas
      (settled)="shop.refreshCatalogo()"
      (comprar)="router.navigate(['/catalogo'])"
    />
  `,
})
export class ComprasPage {
  readonly shop = inject(Shop);
  readonly router = inject(Router);
}
