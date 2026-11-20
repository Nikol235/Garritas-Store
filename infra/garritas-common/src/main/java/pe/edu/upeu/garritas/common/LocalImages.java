package pe.edu.upeu.garritas.common;

import java.awt.image.BufferedImage;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import javax.imageio.ImageIO;
import javax.imageio.stream.ImageInputStream;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

/** Archivos locales y referencia SQL. Cada servicio conserva su propia carpeta y tabla. */
@Service
public class LocalImages {
  public static final long MAX_BYTES = 5L * 1024 * 1024;
  private final JdbcTemplate jdbc;
  private final Path directory;
  private final String table;

  public LocalImages(JdbcTemplate jdbc, @Value("${app.media.directory:./uploads}") String directory,
      @Value("${spring.application.name}") String application) {
    this.jdbc = jdbc;
    this.directory = Path.of(directory).toAbsolutePath().normalize();
    // Los nombres SQL proceden exclusivamente de esta lista, nunca de la petición.
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
    var names = jdbc.queryForList("SELECT archivo FROM recurso_imagen WHERE id_recurso=?", String.class, id);
    if (names.isEmpty()) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Sin imagen");
    Path path = resolve(names.getFirst());
    try {
      if (!Files.isRegularFile(path)) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Sin imagen");
      return new Image(Files.readAllBytes(path), path.toString().endsWith(".png") ? "image/png" : "image/jpeg");
    } catch (IOException ex) { throw storageFailure(); }
  }

  @Transactional
  public void upload(long id, MultipartFile file) {
    if (!CurrentUser.admin()) throw new org.springframework.security.access.AccessDeniedException("Solo ADMIN modifica imágenes");
    if (file.isEmpty() || file.getSize() > MAX_BYTES)
      throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "La imagen debe ocupar entre 1 byte y 5 MB");
    BufferedImage decoded;
    String format;
    // Validar contenido real y dimensiones antes de decodificar todos los píxeles.
    try (InputStream source = file.getInputStream();
        ImageInputStream input = ImageIO.createImageInputStream(source)) {
      if (input == null) throw invalidImage();
      var readers = ImageIO.getImageReaders(input);
      if (!readers.hasNext()) throw invalidImage();
      var reader = readers.next();
      try {
        format = reader.getFormatName().toLowerCase(Locale.ROOT);
        if (!Set.of("jpeg", "jpg", "png").contains(format)) throw invalidImage();
        reader.setInput(input, true, true);
        int width = reader.getWidth(0), height = reader.getHeight(0);
        if (width < 1 || height < 1 || width > 4096 || height > 4096 || (long) width * height > 16000000)
          throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Máximo 4096 × 4096 y 16 millones de píxeles");
        decoded = reader.read(0);
        if (decoded == null) throw invalidImage();
      } finally { reader.dispose(); }
    } catch (IOException | IllegalArgumentException ex) { throw invalidImage(); }
    lockResource(id);
    String old = jdbc.queryForList("SELECT archivo FROM recurso_imagen WHERE id_recurso=?", String.class, id).stream().findFirst().orElse(null);
    String name = UUID.randomUUID() + (format.equals("png") ? ".png" : ".jpg");
    Path target = resolve(name);
    // Crear nombre nuevo: un reemplazo nunca sobreescribe la foto todavía referenciada.
    try {
      Files.createDirectories(directory);
      if (!ImageIO.write(decoded, format.equals("png") ? "png" : "jpeg", target.toFile())) throw invalidImage();
      if (Files.size(target) > MAX_BYTES) {
        Files.deleteIfExists(target);
        throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "La imagen procesada supera 5 MB; reduce su tamaño");
      }
    } catch (IOException ex) { remove(name); throw storageFailure(); }
    TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
      @Override public void afterCompletion(int status) {
        if (status == STATUS_COMMITTED) { if (old != null) remove(old); }
        else remove(name);
      }
    });
    jdbc.update("INSERT INTO recurso_imagen(id_recurso,archivo) VALUES (?,?) ON CONFLICT(id_recurso) DO UPDATE SET archivo=EXCLUDED.archivo", id, name);
  }

  @Transactional
  public void delete(long id) {
    if (!CurrentUser.admin()) throw new org.springframework.security.access.AccessDeniedException("Solo ADMIN modifica imágenes");
    lockResource(id);
    var old = jdbc.queryForList("SELECT archivo FROM recurso_imagen WHERE id_recurso=?", String.class, id);
    jdbc.update("DELETE FROM recurso_imagen WHERE id_recurso=?", id);
    TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
      @Override public void afterCommit() { old.forEach(LocalImages.this::remove); }
    });
  }

  private void lockResource(long id) {
    if (jdbc.queryForList("SELECT id FROM " + table + " WHERE id=? FOR UPDATE", Long.class, id).isEmpty())
      throw new ResponseStatusException(HttpStatus.NOT_FOUND, "El registro no existe");
  }
  private Path resolve(String name) {
    if (!name.matches("[0-9a-f-]{36}\\.(png|jpg)")) throw storageFailure();
    Path path = directory.resolve(name).normalize();
    if (!path.startsWith(directory)) throw storageFailure();
    return path;
  }
  private void remove(String name) {
    try { Files.deleteIfExists(resolve(name)); }
    catch (Exception ex) { LoggerFactory.getLogger(LocalImages.class).warn("No se pudo limpiar archivo de imagen {}", name); }
  }
  private static ResponseStatusException invalidImage() {
    return new ResponseStatusException(HttpStatus.BAD_REQUEST, "Selecciona una imagen JPG o PNG válida");
  }
  private static ResponseStatusException storageFailure() {
    return new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "No se pudo acceder al almacenamiento de imágenes");
  }
}
