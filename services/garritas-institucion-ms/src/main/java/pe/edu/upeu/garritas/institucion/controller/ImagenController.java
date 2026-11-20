package pe.edu.upeu.garritas.institucion.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Import;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import pe.edu.upeu.garritas.common.LocalImages;

@RestController
@RequestMapping("/api/v1/sedes/{id}/imagen")
@RequiredArgsConstructor
@Import(LocalImages.class)
public class ImagenController {
  private final LocalImages images;
  @GetMapping
  public ResponseEntity<byte[]> get(@PathVariable long id) {
    var image = images.read(id);
    return ResponseEntity.ok().contentType(MediaType.parseMediaType(image.contentType()))
        .cacheControl(CacheControl.noStore()).header("X-Content-Type-Options", "nosniff").body(image.bytes());
  }
  @PutMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void upload(@PathVariable long id, @RequestParam("archivo") MultipartFile archivo) {
    images.upload(id, archivo);
  }
  @DeleteMapping
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void delete(@PathVariable long id) { images.delete(id); }
}
