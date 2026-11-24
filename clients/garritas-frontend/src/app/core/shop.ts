import { Injectable, inject, signal } from "@angular/core";
import { HttpErrorResponse } from "@angular/common/http";
import { Router } from "@angular/router";
import { Auth } from "./auth";
import { Api, Categoria, Producto } from "./api";
import { Cobertura, DomainApi, Sede } from "./domain-api";
import { CartStore } from "../features/cart/cart-store";

/** Estado compartido de la tienda: catálogo, avisos globales y checkout. */
@Injectable({ providedIn: "root" })
export class Shop {
  private readonly auth = inject(Auth);
  private readonly cart = inject(CartStore);
  private readonly api = inject(Api);
  private readonly domain = inject(DomainApi);
  private readonly router = inject(Router);

  readonly productos = signal<Producto[]>([]);
  readonly categorias = signal<Categoria[]>([]);
  readonly error = signal("");
  readonly notice = signal("");
  readonly busy = signal(false);
  readonly loading = signal(true);

  refreshSedes() {
    this.domain.get<Sede[]>("/sedes").subscribe({
      next: (s) => this.cart.setSedes(s),
      error: (e) => this.fail(e),
    });
  }

  refreshCatalogo() {
    this.loading.set(true);
    this.api.productos().subscribe({
      next: (p) => {
        this.productos.set(p);
        this.cart.reconcile(p);
        this.loading.set(false);
      },
      error: (e) => {
        this.loading.set(false);
        this.fail(e);
      },
    });
    this.api.categorias().subscribe({
      next: (c) => this.categorias.set(c),
      error: (e) => this.fail(e),
    });
  }

  add(producto: Producto) {
    if (this.busy() || this.auth.admin()) return;
    this.error.set("");
    if (this.cart.add(producto))
      this.notice.set(producto.nombre + " añadido al carrito.");
    else
      this.error.set(
        "Ya tienes en el carrito todas las unidades disponibles de este producto.",
      );
  }

  checkout() {
    if (this.busy() || this.auth.admin()) return;
    this.error.set("");
    if (!this.auth.loggedIn()) {
      this.auth.login();
      return;
    }
    if (!this.cart.valid()) {
      this.error.set(
        "Revisa los productos y las cantidades de tu carrito antes de confirmar.",
      );
      return;
    }
    this.busy.set(true);
    this.api
      .crearVenta(this.cart.payload(), this.cart.checkoutKey())
      .subscribe({
        next: (venta) => {
          this.busy.set(false);
          this.cart.clear();
          this.notice.set(
            "Pedido #" +
              venta.id +
              " registrado. Estamos verificando el inventario y el pago.",
          );
          this.router.navigate(["/compras"]);
          this.refreshCatalogo();
          // Consultar pago después de un breve delay para que la saga procese
          this.pollForCheckout(venta.id);
        },
        error: (e) => {
          this.busy.set(false);
          this.fail(e);
          if (e.status === 409) {
            this.refreshCatalogo();
            this.refreshSedes();
            this.domain.get<Cobertura[]>("/coberturas").subscribe({
              next: (c) => this.cart.coberturas.set(c.filter((x) => x.activo)),
              error: () => this.cart.coberturas.set([]),
            });
          }
        },
      });
  }

  private pollForCheckout(ventaId: number, attempt = 0) {
    if (attempt > 10) return; // max 10 intentos (~20 segundos)
    setTimeout(() => {
      this.api.pago(ventaId).subscribe({
        next: (pago) => {
          if (pago.initPoint && pago.estado === "PENDIENTE") {
            this.notice.set(
              "Redirigiendo al checkout de Mercado Pago para completar el pago…",
            );
            window.open(pago.initPoint, "_blank", "noopener");
          } else if (pago.estado === "PENDIENTE" && !pago.initPoint && attempt < 10) {
            this.pollForCheckout(ventaId, attempt + 1);
          }
        },
        error: () => {
          if (attempt < 10) this.pollForCheckout(ventaId, attempt + 1);
        },
      });
    }, 2000);
  }

  /** Procesa el retorno de Mercado Pago (guardado por Auth.init desde /compras?...). */
  handleMercadoPagoRedirect() {
    const key = "garritas-checkout-return";
    const saved = sessionStorage.getItem(key);
    if (!saved) return;

    const params = new URLSearchParams(saved);
    const ventaId = Number(params.get("venta_id") ?? params.get("external_reference"));
    const paymentId = Number(params.get("payment_id"));
    const validId = (id: number) => Number.isSafeInteger(id) && id > 0;
    if (!validId(ventaId)) {
      sessionStorage.removeItem(key);
      return;
    }
    if (!this.auth.loggedIn()) {
      this.notice.set("Inicia sesión para consultar el resultado de tu pago.");
      return;
    }
    // Ir a /compras sin los parámetros de Mercado Pago en la URL
    this.router.navigate(["/compras"], { replaceUrl: true });
    if (!validId(paymentId)) {
      sessionStorage.removeItem(key);
      this.notice.set("Mercado Pago todavía no devolvió una confirmación. Revisa tu pedido.");
      return;
    }

    this.api.confirmarPago(ventaId, paymentId).subscribe({
      next: (pago) => {
        if (pago.estado !== "PENDIENTE") sessionStorage.removeItem(key);
        if (pago.estado === "APROBADO") this.notice.set("Mercado Pago confirmó tu pago.");
        else if (pago.estado === "RECHAZADO") this.error.set("Mercado Pago rechazó el pago.");
        else this.notice.set("El pago sigue pendiente. Recarga la página para consultar de nuevo.");
      },
      error: () => this.error.set("No se pudo comprobar el pago. Recarga la página para reintentar."),
    });
  }

  fail(e: HttpErrorResponse) {
    this.error.set(
      e.status === 401
        ? "La sesión expiró. Inicia sesión de nuevo."
        : e.status === 403
          ? "No tienes permiso para esta operación."
          : e.status === 0
            ? "No se pudo contactar al servidor. Tu carrito se conserva; puedes reintentar la compra sin duplicarla."
            : (e.error?.detail ??
              e.error?.message ??
              "No se pudo completar la operación. Inténtalo de nuevo."),
    );
  }
}
