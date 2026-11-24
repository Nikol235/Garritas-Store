import { Component, inject } from "@angular/core";
import { RouterLink } from "@angular/router";
import { Auth } from "../core/auth";
import { Shop } from "../core/shop";
import { CartPanel } from "../features/cart/cart-panel";

@Component({
  selector: "app-carrito-page",
  imports: [RouterLink, CartPanel],
  template: `
    <div class="heading">
      <h1>Carrito de compras</h1>
      <button routerLink="/nueva-orden">Seguir comprando</button>
    </div>
    <div class="cart-page">
      <app-cart-panel
        [busy]="shop.busy()"
        [authenticated]="auth.loggedIn()"
        (checkout)="shop.checkout()"
        (login)="auth.login()"
      />
    </div>
  `,
})
export class CarritoPage {
  readonly auth = inject(Auth);
  readonly shop = inject(Shop);
}
