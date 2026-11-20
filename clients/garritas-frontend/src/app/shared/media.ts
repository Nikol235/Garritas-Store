import { Injectable, inject, signal } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { tap } from "rxjs";
import { Config } from "../core/config";
export type ImageResource = "productos" | "especialistas" | "sedes";
@Injectable({ providedIn: "root" })
export class Media {
  private readonly http = inject(HttpClient);
  private readonly config = inject(Config);
  readonly versions = signal<Record<string, number>>({});
  url(resource: ImageResource, id: number) {
    return `${this.config.value.apiUrl}/${resource}/${id}/imagen?v=${this.versions()[resource + "/" + id] ?? 0}`;
  }
  private changed(resource: ImageResource, id: number) {
    this.versions.update((v) => ({
      ...v,
      [resource + "/" + id]: (v[resource + "/" + id] ?? 0) + 1,
    }));
  }
  upload(resource: ImageResource, id: number, file: File) {
    const body = new FormData();
    body.append("archivo", file);
    return this.http
      .put<void>(`${this.config.value.apiUrl}/${resource}/${id}/imagen`, body)
      .pipe(tap(() => this.changed(resource, id)));
  }
  delete(resource: ImageResource, id: number) {
    return this.http
      .delete<void>(`${this.config.value.apiUrl}/${resource}/${id}/imagen`)
      .pipe(tap(() => this.changed(resource, id)));
  }
}
