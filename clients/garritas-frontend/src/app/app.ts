import { Component, inject } from "@angular/core";
import {
  NavigationEnd,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from "@angular/router";
import { filter, take } from "rxjs";
import { Auth } from "./core/auth";
import { RETURN_URL_KEY } from "./core/guards";
import { Shop } from "./core/shop";
import { CartStore } from "./features/cart/cart-store";

@Component({
  selector: "app-root",
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: "./app.html",
})
export class App {
  readonly auth = inject(Auth);
  readonly cart = inject(CartStore);
  readonly shop = inject(Shop);
  private readonly router = inject(Router);

  constructor() {
    if (this.auth.admin()) this.cart.clear();
    this.shop.refreshCatalogo();
    this.shop.refreshSedes();

    // Tras la navegación inicial: retorno de Mercado Pago o ruta pendiente del login
    this.router.events
      .pipe(
        filter((e) => e instanceof NavigationEnd),
        take(1),
      )
      .subscribe(() => this.afterInitialNavigation());
  }

  private afterInitialNavigation() {
    const returnUrl = sessionStorage.getItem(RETURN_URL_KEY);
    sessionStorage.removeItem(RETURN_URL_KEY);
    if (sessionStorage.getItem("garritas-checkout-return")) {
      this.shop.handleMercadoPagoRedirect();
    } else if (returnUrl?.startsWith("/") && this.auth.loggedIn()) {
      this.router.navigateByUrl(returnUrl, { replaceUrl: true });
    }
  }
}
