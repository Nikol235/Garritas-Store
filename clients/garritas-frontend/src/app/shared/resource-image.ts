import { Component, computed, inject, input, signal } from "@angular/core";
import { Media, ImageResource } from "./media";
@Component({
  selector: "app-resource-image",
  template: `@if (failed() !== url()) {
      <img
        [src]="url()"
        [alt]="label()"
        loading="lazy"
        (error)="failed.set(url())"
      />
    } @else {
      <span
        class="image-placeholder"
        role="img"
        [attr.aria-label]="label() + ', sin foto'"
        >{{
          resource() === "productos"
            ? "🐾"
            : resource() === "sedes"
              ? "🏡"
              : "🩺"
        }}</span
      >
    }`,
})
export class ResourceImage {
  readonly resource = input.required<ImageResource>();
  readonly id = input.required<number>();
  readonly label = input.required<string>();
  readonly failed = signal("");
  private readonly media = inject(Media);
  readonly url = computed(() => this.media.url(this.resource(), this.id()));
}
