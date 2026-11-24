import { Component, inject } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { Api, Categoria } from "../core/api";
import { Shop } from "../core/shop";

@Component({
  selector: "app-categorias-page",
  imports: [FormsModule],
  template: `
    <h1>Administrar categorías</h1>
    <form (ngSubmit)="save()">
      <label
        >Nombre<input name="nombre" [(ngModel)]="nombre" required maxlength="100" /></label
      ><label
        >Descripción<input name="descripcion" [(ngModel)]="descripcion" maxlength="255" /></label
      ><button class="primary" [disabled]="!nombre.trim()">
        {{ categoriaId ? "Actualizar" : "Crear" }}
      </button>
    </form>
    <section class="grid">
      @for (c of shop.categorias(); track c.id) {
        <article>
          <h2>{{ c.nombre }}</h2>
          <p>{{ c.descripcion }}</p>
          <button (click)="edit(c)">Editar</button
          ><button (click)="remove(c)">Eliminar</button>
        </article>
      }
    </section>
  `,
})
export class CategoriasPage {
  readonly shop = inject(Shop);
  private readonly api = inject(Api);
  nombre = "";
  descripcion = "";
  categoriaId: number | undefined;

  edit(c: Categoria) {
    this.categoriaId = c.id;
    this.nombre = c.nombre;
    this.descripcion = c.descripcion ?? "";
  }

  save() {
    this.api
      .guardarCategoria(
        { nombre: this.nombre, descripcion: this.descripcion },
        this.categoriaId,
      )
      .subscribe({
        next: () => {
          this.nombre = "";
          this.descripcion = "";
          this.categoriaId = undefined;
          this.shop.refreshCatalogo();
        },
        error: (e) => this.shop.fail(e),
      });
  }

  remove(c: Categoria) {
    if (confirm("¿Eliminar categoría " + c.nombre + "?"))
      this.api.borrarCategoria(c.id).subscribe({
        next: () => this.shop.refreshCatalogo(),
        error: (e) => this.shop.fail(e),
      });
  }
}
