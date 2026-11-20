package pe.edu.upeu.garritas.venta.service;

import java.awt.Color;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigDecimal;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import pe.edu.upeu.garritas.venta.entity.EstadoVenta;

@Service
@RequiredArgsConstructor
public class ComprobanteService {
  private static final Color ACCENT = new Color(119, 38, 76);
  private static final Color INK = new Color(39, 32, 37);
  private static final Color TINT = new Color(250, 238, 244);
  private static final PDType1Font REGULAR = new PDType1Font(Standard14Fonts.FontName.HELVETICA);
  private static final PDType1Font BOLD = new PDType1Font(Standard14Fonts.FontName.HELVETICA_BOLD);
  private static final DateTimeFormatter FECHA = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm")
      .withZone(ZoneId.of("America/Lima"));
  private static final int ROWS_PER_PAGE = 20;

  private final VentaService ventas;

  public byte[] generar(long id) {
    var venta = ventas.obtener(id);
    if (venta.getEstado() != EstadoVenta.PAGADA)
      throw new ResponseStatusException(HttpStatus.CONFLICT,
          "El comprobante está disponible cuando la compra está pagada");

    try (var doc = new PDDocument(); var out = new ByteArrayOutputStream()) {
      var detalles = List.copyOf(venta.getDetalles());
      int paginas = Math.max(1, (detalles.size() + ROWS_PER_PAGE - 1) / ROWS_PER_PAGE);
      for (int numero = 0; numero < paginas; numero++) {
        var page = new PDPage(PDRectangle.A4);
        doc.addPage(page);
        try (var stream = new PDPageContentStream(doc, page)) {
          box(stream, 40, 734, 515, 68, ACCENT);
          text(stream, BOLD, 11, 54, 780, Color.WHITE, "GARRITAS STORE");
          text(stream, BOLD, 21, 54, 752, Color.WHITE, "Constancia de compra #" + id);
          text(stream, REGULAR, 10, 40, 710, INK, "Fecha: " + FECHA.format(venta.getFecha()) + " (Perú)");
          text(stream, BOLD, 10, 416, 710, ACCENT, "PAGADA  |  Sede #" + venta.getSedeId());
          text(stream, REGULAR, 10, 40, 691, INK, "Cliente (identificador): " + venta.getIdCliente());
          box(stream, 40, 648, 515, 25, TINT);
          text(stream, BOLD, 10, 50, 657, INK, "Producto");
          right(stream, BOLD, 10, 328, 657, "Cantidad");
          right(stream, BOLD, 10, 439, 657, "Precio unitario");
          right(stream, BOLD, 10, 545, 657, "Subtotal");

          int y = 631;
          int inicio = numero * ROWS_PER_PAGE;
          for (var detalle : detalles.subList(inicio, Math.min(inicio + ROWS_PER_PAGE, detalles.size()))) {
            box(stream, 40, y - 6, 515, 1, TINT);
            text(stream, REGULAR, 10, 50, y, INK, "Producto #" + detalle.getIdProducto());
            right(stream, REGULAR, 10, 328, y, Integer.toString(detalle.getCantidad()));
            right(stream, REGULAR, 10, 439, y, soles(detalle.getPrecioUnitario()));
            right(stream, REGULAR, 10, 545, y, soles(detalle.getSubtotal()));
            y -= 19;
          }

          if (numero == paginas - 1) {
            text(stream, REGULAR, 10, 40, y - 14, INK, "Entrega: " + venta.getTipoEntrega());
            if (venta.getDireccionEntrega() != null) {
              paragraph(stream, "Dirección: " + venta.getDireccionEntrega(), 40, y - 33, 320);
            }
            box(stream, 378, y - 74, 177, 78, TINT);
            text(stream, REGULAR, 10, 390, y - 14, INK, "Subtotal");
            right(stream, REGULAR, 10, 545, y - 14, soles(venta.getSubtotal()));
            text(stream, REGULAR, 10, 390, y - 33, INK, "Envío");
            right(stream, REGULAR, 10, 545, y - 33, soles(venta.getCostoEnvio()));
            text(stream, BOLD, 11, 390, y - 59, ACCENT, "TOTAL:");
            right(stream, BOLD, 11, 545, y - 59, soles(venta.getTotal()));
          }

          box(stream, 40, 57, 515, 1, TINT);
          text(stream, REGULAR, 9, 40, 40, INK,
              "Modo demo: pago simulado. Sin validez tributaria. No es boleta ni factura SUNAT.");
          right(stream, REGULAR, 9, 555, 40, (numero + 1) + " / " + paginas);
        }
      }
      doc.save(out);
      return out.toByteArray();
    } catch (IOException e) {
      throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "No se pudo generar el PDF", e);
    }
  }

  private static String soles(BigDecimal importe) {
    return "S/ " + importe.toPlainString();
  }

  private static void box(PDPageContentStream stream, int x, int y, int width, int height, Color color)
      throws IOException {
    stream.setNonStrokingColor(color);
    stream.addRect(x, y, width, height);
    stream.fill();
  }

  private static void text(PDPageContentStream stream, PDType1Font font, int size, float x, int y,
      Color color, String value) throws IOException {
    stream.beginText();
    stream.setNonStrokingColor(color);
    stream.setFont(font, size);
    stream.newLineAtOffset(x, y);
    stream.showText(value);
    stream.endText();
  }

  private static void right(PDPageContentStream stream, PDType1Font font, int size, int x, int y,
      String value) throws IOException {
    text(stream, font, size, x - font.getStringWidth(value) * size / 1000, y, INK, value);
  }

  private static void paragraph(PDPageContentStream stream, String value, int x, int y, int width)
      throws IOException {
    String remaining = value.replaceAll("[^\\x20-\\x7E\\xA0-\\xFF]", "?");
    while (!remaining.isEmpty()) {
      int end = remaining.length();
      while (REGULAR.getStringWidth(remaining.substring(0, end)) * 10 / 1000 > width)
        end--;
      if (end < remaining.length() && remaining.lastIndexOf(' ', end) > 0)
        end = remaining.lastIndexOf(' ', end);
      text(stream, REGULAR, 10, x, y, INK, remaining.substring(0, end));
      remaining = remaining.substring(end).stripLeading();
      y -= 14;
    }
  }
}
