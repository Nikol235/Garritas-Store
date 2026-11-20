package pe.edu.upeu.garritas.venta;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.web.server.ResponseStatusException;
import pe.edu.upeu.garritas.venta.dto.*;
import pe.edu.upeu.garritas.venta.entity.EstadoVenta;
import pe.edu.upeu.garritas.venta.service.*;
class ComprobanteTest {
  @Test void unpaidSaleCannotIssueReceipt() {
    var ventas=mock(VentaService.class);
    when(ventas.obtener(1L)).thenReturn(VentaResponse.builder().estado(EstadoVenta.PENDIENTE_PAGO).build());
    var error=assertThrows(ResponseStatusException.class,()->new ComprobanteService(ventas).generar(1));
    assertEquals(409,error.getStatusCode().value());
  }
  @Test void paidReceiptKeepsAgreedAmountsAndPaginates() throws Exception {
    var ventas=mock(VentaService.class);var details=new ArrayList<DetalleVentaResponse>();
    for(int i=0;i<60;i++) details.add(DetalleVentaResponse.builder().idProducto((long)i+1).cantidad(1).precioUnitario(BigDecimal.TEN).subtotal(BigDecimal.TEN).build());
    when(ventas.obtener(5L)).thenReturn(VentaResponse.builder().id(5L).estado(EstadoVenta.PAGADA).fecha(Instant.now()).idCliente("cliente-prueba").sedeId(1L).subtotal(new BigDecimal("600.00")).costoEnvio(new BigDecimal("10.00")).total(new BigDecimal("610.00")).tipoEntrega("ENVIO").direccionEntrega("Direccion de demostracion").detalles(details).build());
    try(var doc=Loader.loadPDF(new ComprobanteService(ventas).generar(5))) {
      assertTrue(doc.getNumberOfPages()>1);
      String text=new PDFTextStripper().getText(doc);
      assertTrue(text.contains("TOTAL: S/ 610.00"));assertTrue(text.contains("Producto #60"));
      assertTrue(text.contains("pago simulado"));assertTrue(text.contains("Sin validez tributaria"));
    }
  }
  @Test void ownershipFailureIsNotBypassed() {
    var ventas=mock(VentaService.class);
    when(ventas.obtener(7L)).thenThrow(new org.springframework.security.access.AccessDeniedException("Ajeno"));
    assertThrows(org.springframework.security.access.AccessDeniedException.class,()->new ComprobanteService(ventas).generar(7));
  }
}
