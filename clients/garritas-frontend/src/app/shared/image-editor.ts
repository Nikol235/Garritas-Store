import { Component, OnDestroy, inject, input, signal } from "@angular/core";
import { Observable, of, tap } from "rxjs";
import { Media, ImageResource } from "./media";
import { ResourceImage } from "./resource-image";
@Component({
  selector: "app-image-editor",
  imports: [ResourceImage],
  template: `<section class="image-editor">
    <h3>Imagen principal (opcional)</h3>
    @if (preview()) {
      <img
        class="image-preview"
        [src]="preview()"
        alt="Vista previa de la imagen seleccionada"
      />
    } @else if (id() && !removed()) {
      <app-resource-image
        [resource]="resource()"
        [id]="id()!"
        label="Imagen actual"
      />
    }
    <label
      >Seleccionar imagen de tu computadora<input
        type="file"
        accept="image/jpeg,image/png"
        [disabled]="disabled()"
        (change)="choose($event)"
    /></label>
    <p class="muted">
      JPG o PNG, hasta 5 MB. La imagen se aplica al guardar el registro.
    </p>
    @if (file() || (id() && !removed())) {
      <button type="button" [disabled]="disabled()" (click)="remove()">
        Quitar imagen al guardar
      </button>
    }
    @if (removed()) {
      <p class="muted">Se guardará sin imagen.</p>
    }
    @if (error()) {
      <p class="error" role="alert">{{ error() }}</p>
    }
  </section>`,
})
export class ImageEditor implements OnDestroy {
  readonly resource = input.required<ImageResource>();
  readonly id = input<number>();
  readonly disabled = input(false);
  readonly file = signal<File | null>(null);
  readonly preview = signal("");
  readonly removed = signal(false);
  readonly error = signal("");
  private readonly media = inject(Media);
  choose(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.error.set("");
    if (
      !["image/jpeg", "image/png"].includes(file.type) ||
      file.size > 5 * 1024 * 1024 ||
      !file.size
    ) {
      this.error.set("Selecciona JPG o PNG de hasta 5 MB.");
      input.value = "";
      return;
    }
    this.revoke();
    this.file.set(file);
    this.removed.set(false);
    this.preview.set(URL.createObjectURL(file));
    input.value = "";
  }
  remove() {
    this.reset();
    this.removed.set(true);
  }
  reset() {
    this.revoke();
    this.file.set(null);
    this.removed.set(false);
    this.error.set("");
  }
  private revoke() {
    if (this.preview()) URL.revokeObjectURL(this.preview());
    this.preview.set("");
  }
  persist(id: number): Observable<void> {
    const file = this.file();
    const request = file
      ? this.media.upload(this.resource(), id, file)
      : this.removed()
        ? this.media.delete(this.resource(), id)
        : of(void 0);
    return request.pipe(tap(() => this.reset()));
  }
  ngOnDestroy() {
    this.revoke();
  }
}
