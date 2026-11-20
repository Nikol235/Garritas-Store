import { TestBed } from "@angular/core/testing";
import { signal } from "@angular/core";
import { of } from "rxjs";
import { describe, it, expect, vi, afterEach } from "vitest";
import { VentasComponent } from "./ventas.component";
import { Api, Venta } from "../../core/api";
import { Auth } from "../../core/auth";
import { DomainApi } from "../../core/domain-api";
describe("Ventas: roles, filtros e importes acordados", () => {
  afterEach(() => TestBed.resetTestingModule());
  function setup(admin = false) {
    const pdf = vi.fn();
    TestBed.configureTestingModule({
      imports: [VentasComponent],
      providers: [
        { provide: Auth, useValue: { admin: signal(admin) } },
        {
          provide: Api,
          useValue: {
            productos: () => of([]),
            ventas: () => of([]),
            comprobante: pdf,
          },
        },
        { provide: DomainApi, useValue: { get: () => of([]) } },
      ],
    });
    const fixture = TestBed.createComponent(VentasComponent);
    const c = fixture.componentInstance;
    c.ventas.set([
      {
        id: 1,
        idCliente: "cliente-a",
        fecha: "2026-11-12T12:00:00Z",
        estado: "PAGADA",
        subtotal: 20,
        costoEnvio: 5,
        total: 25,
        tipoEntrega: "ENVIO",
        detalles: [],
      },
      {
        id: 2,
        idCliente: "cliente-b",
        fecha: "2026-11-14T12:00:00Z",
        estado: "COMPENSANDO",
        subtotal: 40,
        costoEnvio: 0,
        total: 40,
        tipoEntrega: "RECOJO",
        detalles: [],
      },
    ] as unknown as Venta[]);
    return { fixture, c, pdf };
  }
  it("muestra Ventas y cliente para ADMIN", () => {
    const { fixture } = setup(true);
    fixture.detectChanges();
    const el = fixture.nativeElement;
    expect(el.querySelector("h1").textContent).toBe("Ventas");
    expect(el.textContent).toContain("cliente-a");
  });
  it("presenta Mis compras sin columna de identificadores ni resumen administrativo", () => {
    const { fixture } = setup();
    fixture.detectChanges();
    const el = fixture.nativeElement;
    expect(el.querySelector("h1").textContent).toBe("Mis compras");
    expect(el.querySelector(".client-reference")).toBeNull();
    expect(el.querySelector(".sales-summary")).toBeNull();
  });
  it("combina estado, fecha e identificador; suma solo pagos confirmados", () => {
    const { c } = setup(true);
    expect(c.totalPagado()).toBe(25);
    c.estado.set("COMPENSANDO");
    c.desde.set("2026-11-13");
    c.search.set("cliente-b");
    expect(c.filtered().map((v) => v.id)).toEqual([2]);
    c.hasta.set("2026-11-13");
    expect(c.filtered()).toEqual([]);
    c.clear();
    expect(c.filtered()).toHaveLength(2);
  });
  it("no solicita PDF para una compra sin pago confirmado", () => {
    const { c, pdf } = setup();
    c.comprobante(c.ventas()[1]);
    expect(pdf).not.toHaveBeenCalled();
    expect(c.info("COMPENSANDO").descripcion).toContain("devolviendo");
  });
});
