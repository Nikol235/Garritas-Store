import { Component, inject } from "@angular/core";
import { Auth } from "../core/auth";
import { Shop } from "../core/shop";
import { CartPanel } from "../features/cart/cart-panel";
import { ProductCatalog } from "../features/catalogo/product-catalog";

@Component({
  selector: "app-nueva-orden-page",
  imports: [CartPanel, ProductCatalog],
  template: `
    <div class="heading">
      <div>
        <p class="eyebrow">PREPARA SU PRÓXIMA ENTREGA</p>
        <h1>Nueva orden</h1>
        <p>Elige lo que necesita tu mascota y revisa tu compra antes de confirmar.</p>
      </div>
      <button (click)="shop.refreshCatalogo()">Actualizar catálogo</button>
    </div>
    <div class="order-layout">
      <section aria-label="Productos para tu nueva orden">
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
      </section>
      <aside>
        <app-cart-panel
          [busy]="shop.busy()"
          [authenticated]="auth.loggedIn()"
          (checkout)="shop.checkout()"
          (login)="auth.login()"
        />
      </aside>
    </div>
  `,
})
export class NuevaOrdenPage {
  readonly auth = inject(Auth);
  readonly shop = inject(Shop);
}
