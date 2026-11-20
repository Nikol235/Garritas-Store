import { ImageEditor } from "../../shared/image-editor";
import { ResourceImage } from "../../shared/resource-image";
import { concatMap, map, of } from "rxjs";
import { Component, viewChild, inject, signal, output } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { Auth } from "../../core/auth";
import { DomainApi, Feedback, Sede } from "../../core/domain-api";
import { CartStore } from "../cart/cart-store";
@Component({
  selector: "app-sedes",
  imports: [FormsModule, ImageEditor, ResourceImage],
  templateUrl: "./sedes.component.html",
})
export class SedesComponent extends Feedback {
  readonly imageEditor = viewChild(ImageEditor);
  readonly auth = inject(Auth);
  readonly cart = inject(CartStore);
  private readonly api = inject(DomainApi);
  readonly sedes = signal<Sede[]>([]);
  readonly order = output<void>();
  readonly servicios = output<number>();
  id: number | undefined;
  model = { nombre: "", ciudad: "", direccion: "", telefono: "", activo: true };
  constructor() {
    super();
    this.load();
  }
  load() {
    this.api.get<Sede[]>("/sedes").subscribe({
      next: (s) => {
        this.sedes.set(s);
        this.cart.setSedes(s);
      },
      error: (e) => this.report(e),
    });
  }
  edit(s: Sede) {
    this.imageEditor()?.reset();
    this.id = s.id;
    this.model = {
      nombre: s.nombre,
      ciudad: s.ciudad,
      direccion: s.direccion,
      telefono: s.telefono,
      activo: s.activo,
    };
  }
  reset() {
    this.imageEditor()?.reset();
    this.id = undefined;
    this.model = {
      nombre: "",
      ciudad: "",
      direccion: "",
      telefono: "",
      activo: true,
    };
  }
  save() {
    this.send(
      (this.id
        ? this.api.put<Sede>("/sedes/" + this.id, this.model)
        : this.api.post<Sede>("/sedes", this.model)
      ).pipe(
        concatMap((saved) => {
          this.id = saved.id; // Si falla la imagen, el reintento no duplica el registro.
          return (this.imageEditor()?.persist(saved.id) ?? of(void 0)).pipe(
            map(() => saved),
          );
        }),
      ),
      () => {
        this.reset();
        this.load();
      },
    );
  }
  deactivate(s: Sede) {
    if (confirm("¿Desactivar la sede " + s.nombre + "?"))
      this.send(this.api.delete("/sedes/" + s.id), () => this.load());
  }
  choose(s: Sede) {
    this.cart.selectSede(s.id);
    this.order.emit();
  }
}
