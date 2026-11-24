import {
  Component,
  DestroyRef,
  computed,
  effect,
  inject,
  output,
  signal,
} from "@angular/core";
import { CurrencyPipe, DatePipe } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { takeUntilDestroyed } from "@angular/core/rxjs-interop";
import { EMPTY, catchError, exhaustMap, finalize, timer } from "rxjs";
import { Api, Pago, Producto, Venta, pending } from "../../core/api";
import { Auth } from "../../core/auth";
import { DomainApi, Feedback, Sede } from "../../core/domain-api";

export const ESTADOS_VENTA: Record<
  string,
  { nombre: string; descripcion: string }
> = {
  PENDIENTE_STOCK: {
    nombre: "Pendiente de stock",
    descripcion:
      "Estamos intentando reservar los productos. La compra todavía no está confirmada.",
  },
  PENDIENTE_PAGO: {
    nombre: "Pendiente de pago",
    descripcion:
      "El inventario está reservado y esperamos el resultado del pago.",
  },
  PAGADA: {
    nombre: "Pagada",
    descripcion:
      "El pago fue confirmado. Si elegiste delivery, el despacho se genera automáticamente.",
  },
  COMPENSANDO: {
    nombre: "Compensando",
    descripcion:
      "El pago fue rechazado y estamos devolviendo el inventario reservado. Todavía no termina la cancelación.",
  },
  CANCELADA: {
    nombre: "Cancelada",
    descripcion:
      "La compra no se completó. Puede deberse a falta de stock o al rechazo del pago; si hubo reserva, su liberación ya fue confirmada.",
  },
};

@Component({
  selector: "app-ventas",
  imports: [FormsModule, CurrencyPipe, DatePipe],
  templateUrl: "./ventas.component.html",
})
export class VentasComponent extends Feedback {
  readonly auth = inject(Auth);
  private readonly api = inject(Api);
  private readonly domain = inject(DomainApi);
  private readonly destroy = inject(DestroyRef);
  readonly settled = output<void>();
  readonly comprar = output<void>();
  readonly ventas = signal<Venta[]>([]);
  readonly productos = signal<Producto[]>([]);
  readonly sedes = signal<Sede[]>([]);
  readonly selected = signal<number | null>(null);
  readonly detalle = computed(() =>
    this.ventas().find((v) => v.id === this.selected()),
  );
  readonly pagos = signal<Record<number, Pago>>({});
  readonly loading = signal(false);
  readonly pdfBusy = signal(false);
  readonly verificandoPago = signal(false);
  readonly search = signal("");
  readonly estado = signal("");
  readonly desde = signal("");
  readonly hasta = signal("");
  readonly estados = Object.entries(ESTADOS_VENTA);
  readonly filtered = computed(() => {
    const query = this.search().trim().toLowerCase();
    return this.ventas().filter((v) => {
      const fecha = this.localDate(v.fecha);
      return (
        (!query ||
          String(v.id).includes(query) ||
          (this.auth.admin() && v.idCliente.toLowerCase().includes(query))) &&
        (!this.estado() || v.estado === this.estado()) &&
        (!this.desde() || fecha >= this.desde()) &&
        (!this.hasta() || fecha <= this.hasta())
      );
    });
  });
  readonly pagadas = computed(() =>
    this.ventas().filter((v) => v.estado === "PAGADA"),
  );
  readonly totalPagado = computed(() =>
    this.pagadas().reduce((sum, v) => sum + v.total, 0),
  );

  constructor() {
    super();
    this.domain
      .get<Sede[]>("/sedes")
      .subscribe({ next: (s) => this.sedes.set(s), error: () => {} });
    this.api
      .productos()
      .subscribe({ next: (p) => this.productos.set(p), error: () => {} });
    timer(0, 3000)
      .pipe(
        exhaustMap((n) => {
          if (n > 0 && !this.ventas().some((v) => pending(v.estado)))
            return EMPTY;
          return this.api.ventas().pipe(
            catchError((e) => {
              this.report(e);
              return EMPTY;
            }),
          );
        }),
        takeUntilDestroyed(this.destroy),
      )
      .subscribe((ventas) => this.apply(ventas));

    // Autocargar pago al seleccionar un pedido
    effect(() => {
      const id = this.selected();
      if (id == null) return;
      const v = this.ventas().find(x => x.id === id);
      if (v && pending(v.estado) && !this.pagos()[id]) this.pago(id);
    });
  }
  refresh() {
    if (this.loading()) return;
    this.error.set("");
    this.loading.set(true);
    this.api
      .ventas()
      .pipe(
        finalize(() => this.loading.set(false)),
        takeUntilDestroyed(this.destroy),
      )
      .subscribe({
        next: (v) => this.apply(v),
        error: (e) => this.report(e),
      });
  }
  private apply(next: Venta[]) {
    const finished = this.ventas().some(
      (v) =>
        pending(v.estado) &&
        next.some((n) => n.id === v.id && !pending(n.estado)),
    );
    this.ventas.set(next);
    if (finished) this.settled.emit();
  }
  info(estado: string) {
    return (
      ESTADOS_VENTA[estado] ?? {
        nombre: estado,
        descripcion: "Consulta el estado actualizado de esta compra.",
      }
    );
  }
  sede(id: number | null) {
    return (
      this.sedes().find((s) => s.id === id)?.nombre ?? `Sede #${id ?? "—"}`
    );
  }
  producto(id: number) {
    return (
      this.productos().find((p) => p.id === id)?.nombre ?? `Producto #${id}`
    );
  }
  localDate(value: string) {
    const d = new Date(value);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  clear() {
    this.search.set("");
    this.estado.set("");
    this.desde.set("");
    this.hasta.set("");
  }
  pago(id: number) {
    this.api
      .pago(id)
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: (p) => this.pagos.update((all) => ({ ...all, [id]: p })),
        error: (e) => this.report(e),
      });
  }
  verificarPago(id: number) {
    if (this.verificandoPago()) return;
    this.verificandoPago.set(true);
    this.error.set("");
    this.message.set("");
    this.api.confirmarPago(id)
      .pipe(finalize(() => this.verificandoPago.set(false)), takeUntilDestroyed(this.destroy))
      .subscribe({
        next: (pago) => {
          this.pagos.update((all) => ({ ...all, [id]: pago }));
          if (pago.estado === "PENDIENTE")
            this.message.set("Mercado Pago todavía no confirma el pago. Puedes volver a verificarlo.");
          else this.refresh();
        },
        error: (e) => this.report(e),
      });
  }

  comprobante(venta: Venta) {
    if (venta.estado !== "PAGADA" || this.pdfBusy()) return;
    this.pdfBusy.set(true);
    this.error.set("");
    this.api
      .comprobante(venta.id)
      .pipe(
        finalize(() => this.pdfBusy.set(false)),
        takeUntilDestroyed(this.destroy),
      )
      .subscribe({
        next: (blob) => {
          const url = URL.createObjectURL(blob);
          const anchor = document.createElement("a");
          anchor.href = url;
          anchor.download = `Garritas-compra-${venta.id}.pdf`;
          document.body.appendChild(anchor);
          anchor.click();
          anchor.remove();
          setTimeout(() => URL.revokeObjectURL(url), 60000);
          this.message.set(
            "PDF descargado. Ábrelo y elige Imprimir para obtener una copia en papel.",
          );
        },
        error: () =>
          this.error.set(
            "No se pudo descargar el comprobante. Actualiza la compra y verifica tu sesión.",
          ),
      });
  }
}
