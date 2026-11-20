package pe.edu.upeu.garritas.venta.service;

import java.io.*;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import lombok.RequiredArgsConstructor;
import org.apache.pdfbox.pdmodel.*;
import org.apache.pdfbox.pdmodel.font.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import pe.edu.upeu.garritas.venta.entity.EstadoVenta;

@Service
@RequiredArgsConstructor
public class ComprobanteService {
  private final VentaService ventas;
  public byte[] generar(long id) {
    var v = ventas.obtener(id); // Aplica la misma propiedad/rol que la consulta de venta.
    if (v.getEstado() != EstadoVenta.PAGADA)
      throw new ResponseStatusException(HttpStatus.CONFLICT, "El comprobante está disponible cuando la compra está pagada");
    List<String> lines = new ArrayList<>();
    lines.add("GARRITAS STORE - CONSTANCIA DE COMPRA #" + id);
    lines.add("Laboratorio: pago simulado. Sin validez tributaria.");
    lines.add("Fecha: " + DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm").withZone(ZoneId.of("America/Lima")).format(v.getFecha()));
    lines.add("Cliente (identificador): " + v.getIdCliente());
    lines.add("Sede: #" + v.getSedeId() + " | Estado: PAGADA");
    lines.add(" "); lines.add("Producto / cantidad / precio acordado / subtotal (S/)");
    for (var d : v.getDetalles())
      lines.add("Producto #" + d.getIdProducto() + " | " + d.getCantidad() + " un. | S/ " + d.getPrecioUnitario() + " | S/ " + d.getSubtotal());
    lines.add(" "); lines.add("Subtotal: S/ " + v.getSubtotal());
    lines.add("Envio: S/ " + v.getCostoEnvio()); lines.add("TOTAL: S/ " + v.getTotal());
    lines.add("Entrega: " + v.getTipoEntrega());
    if (v.getDireccionEntrega() != null) lines.add("Direccion: " + v.getDireccionEntrega());
    lines.add(" ");lines.add("Los importes corresponden a la compra registrada.");
    lines.add("Esta constancia no es una boleta ni una factura SUNAT.");
    try (var doc = new PDDocument(); var out = new ByteArrayOutputStream()) {
      var font = new PDType1Font(Standard14Fonts.FontName.HELVETICA);
      PDPageContentStream stream = null; int y = 0;
      try {
        for (String text : lines) {
          // Identificadores y referencias no dependen de nombres mutables del catálogo.
          text = text.replaceAll("[^\\x20-\\x7E\\xA0-\\xFF]", "?");
          for (int start = 0; start < text.length(); start += 85) {
            if (stream == null || y < 55) {
              if (stream != null) stream.close();
              var page = new PDPage(); doc.addPage(page); stream = new PDPageContentStream(doc,page); y = 735;
            }
            stream.beginText();stream.setFont(font,11);stream.newLineAtOffset(45,y);
            stream.showText(text.substring(start, Math.min(start+85,text.length())));stream.endText(); y -= 19;
          }
        }
      } finally { if (stream != null) stream.close(); }
      doc.save(out);return out.toByteArray();
    } catch (IOException e) { throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"No se pudo generar el PDF"); }
  }
}
