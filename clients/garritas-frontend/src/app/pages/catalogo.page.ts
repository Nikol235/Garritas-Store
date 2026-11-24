import { Component, inject } from "@angular/core";
import { RouterLink } from "@angular/router";
import { Auth } from "../core/auth";
import { Shop } from "../core/shop";
import { ProductCatalog } from "../features/catalogo/product-catalog";

@Component({
  selector: "app-catalogo-page",
  imports: [RouterLink, ProductCatalog],
  template: `
    <section class="hero">
      <span>TODO PARA TU MEJOR AMIGO</span>
      <h1>Cuídalos con amor.<br />Nosotros ponemos lo demás.</h1>
      <p>Alimentos, higiene, juguetes y accesorios para cada etapa de su vida.</p>
      @if (!auth.admin()) {
        <button class="primary" routerLink="/nueva-orden">Crear nueva orden</button>
      }
      <div class="hero-features">
        <span>🐾 Hecho para su bienestar</span
        ><span>♡ Atención en nuestras sedes</span
        ><span>✦ Productos para cada etapa</span>
      </div>
    </section>
    <div class="heading">
      <h2>Encuentra su próximo favorito</h2>
      <button (click)="shop.refreshCatalogo()">Actualizar catálogo</button>
    </div>
    @if (shop.loading()) {
      <p role="status">Cargando productos…</p>
    }
    <app-product-catalog
      [productos]="shop.productos()"
      [purchasable]="!auth.admin()"
      [categorias]="shop.categorias()"
      [busy]="shop.busy()"
      (add)="shop.add($event)"
    />
  `,
})
export class CatalogoPage {
  readonly auth = inject(Auth);
  readonly shop = inject(Shop);
}
