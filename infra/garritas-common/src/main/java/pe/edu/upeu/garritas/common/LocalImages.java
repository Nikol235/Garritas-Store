package pe.edu.upeu.garritas.common;

import java.awt.image.BufferedImage;
import java.io.*;
import java.util.*;
import javax.imageio.ImageIO;
import javax.imageio.stream.ImageInputStream;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

/**
 * Almacena imágenes directamente en PostgreSQL (bytea).
 * Compatible con entornos efímeros como Railway donde el disco no persiste.
 */
@Service
public class LocalImages {
  public static final long MAX_BYTES = 5L * 1024 * 1024;
  private final JdbcTemplate jdbc;
  private final String table;

  public LocalImages(JdbcTemplate jdbc, @Value("${spring.application.name}") String application) {
    this.jdbc = jdbc;
    this.table = switch (application) {
      case "garritas-catalogo-ms" -> "productos";
      case "garritas-institucion-ms" -> "sedes";
      case "garritas-bienestar-ms" -> "profesionales";
      default -> throw new IllegalArgumentException("Servicio sin almacenamiento de imágenes");
    };
  }

  public record Image(byte[] bytes, String contentType) {}

  @Transactional(readOnly = true)
  public Image read(long id) {
    var rows = jdbc.queryForList(
        "SELECT datos, content_type FROM recurso_imagen WHERE id_recurso=? AND datos IS NOT NULL", id);
    if (rows.isEmpty())
      throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Sin imagen");
    var row = rows.getFirst();
    byte[] datos = (byte[]) row.get("datos");
    String ct = (String) row.get("content_type");
    if (datos == null || ct == null)
      throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Sin imagen");
    return new Image(datos, ct);
  }

  @Transactional
  public void upload(long id, MultipartFile file) {
    if (!CurrentUser.admin())
      throw new org.springframework.security.access.AccessDeniedException("Solo ADMIN modifica imágenes");
    if (file.isEmpty() || file.getSize() > MAX_BYTES)
      throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "La imagen debe ocupar entre 1 byte y 5 MB");

    String contentType;
    byte[] imageBytes;

    try (InputStream source = file.getInputStream();
        ImageInputStream input = ImageIO.createImageInputStream(source)) {
      if (input == null) throw invalidImage();
      var readers = ImageIO.getImageReaders(input);
      if (!readers.hasNext()) throw invalidImage();
      var reader = readers.next();
      try {
        String format = reader.getFormatName().toLowerCase(Locale.ROOT);
        if (!Set.of("jpeg", "jpg", "png").contains(format)) throw invalidImage();
        reader.setInput(input, true, true);
        int width = reader.getWidth(0), height = reader.getHeight(0);
        if (width < 1 || height < 1 || width > 4096 || height > 4096 || (long) width * height > 16000000)
          throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Máximo 4096 × 4096 y 16 millones de píxeles");
        BufferedImage decoded = reader.read(0);
        if (decoded == null) throw invalidImage();

        contentType = format.equals("png") ? "image/png" : "image/jpeg";
        // Re-codificar la imagen para garantizar contenido limpio
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        if (!ImageIO.write(decoded, format.equals("png") ? "png" : "jpeg", out)) throw invalidImage();
        imageBytes = out.toByteArray();
        if (imageBytes.length > MAX_BYTES)
          throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
              "La imagen procesada supera 5 MB; reduce su tamaño");
      } finally { reader.dispose(); }
    } catch (IOException | IllegalArgumentException ex) { throw invalidImage(); }

    lockResource(id);
    jdbc.update("""
        INSERT INTO recurso_imagen(id_recurso, datos, content_type)
        VALUES (?, ?, ?)
        ON CONFLICT(id_recurso)
        DO UPDATE SET datos = EXCLUDED.datos, content_type = EXCLUDED.content_type
        """, id, imageBytes, contentType);
  }

  @Transactional
  public void delete(long id) {
    if (!CurrentUser.admin())
      throw new org.springframework.security.access.AccessDeniedException("Solo ADMIN modifica imágenes");
    lockResource(id);
    jdbc.update("DELETE FROM recurso_imagen WHERE id_recurso=?", id);
  }

  private void lockResource(long id) {
    if (jdbc.queryForList("SELECT id FROM " + table + " WHERE id=? FOR UPDATE", Long.class, id).isEmpty())
      throw new ResponseStatusException(HttpStatus.NOT_FOUND, "El registro no existe");
  }

  private static ResponseStatusException invalidImage() {
    return new ResponseStatusException(HttpStatus.BAD_REQUEST, "Selecciona una imagen JPG o PNG válida");
  }
}
