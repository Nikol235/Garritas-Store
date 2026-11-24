package pe.edu.upeu.garritas.pago.controller;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import pe.edu.upeu.garritas.pago.service.MercadoPagoService;
import pe.edu.upeu.garritas.pago.dto.PagoResponse;
import pe.edu.upeu.garritas.pago.service.PagoService;

@RestController
@RequestMapping("/api/v1/pagos")
@RequiredArgsConstructor
public class PagoController {
  private final PagoService service;
  private final MercadoPagoService mercadoPago;

  @GetMapping
  public List<PagoResponse> listar() {
    return service.listar();
  }

  @GetMapping("/{id}")
  public PagoResponse obtener(@PathVariable Long id) {
    return service.obtener(id);
  }

  @GetMapping("/venta/{id}")
  public PagoResponse porVenta(@PathVariable Long id) {
    return service.porVenta(id);
  }

  /**
   * Verifica el pago indicado por el retorno o busca por la referencia del pedido.
   */
  @PostMapping("/confirmar")
  public PagoResponse confirmar(
      @RequestParam("ventaId") Long ventaId,
      @RequestParam(value = "paymentId", required = false) Long paymentId) {
    return service.confirmar(ventaId, paymentId);
  }

  /**
   * Webhook de Mercado Pago (solo desplegado: requiere una URL pública HTTPS).
   * Valida x-signature y luego vuelve a consultar el pago en la API.
   */
  @PostMapping("/webhook")
  public ResponseEntity<Void> webhook(
      @RequestParam(value = "type", required = false) String type,
      @RequestParam(value = "topic", required = false) String topic,
      @RequestParam(value = "data.id", required = false) String dataId,
      @RequestHeader(value = "x-signature", required = false) String signature,
      @RequestHeader(value = "x-request-id", required = false) String requestId) {
    // Las notificaciones IPN antiguas (topic=...) y otros tipos no se procesan.
    if (!"payment".equals(type) || topic != null) return ResponseEntity.ok().build();
    if (!mercadoPago.webhookConfigured()) return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).build();
    if (!mercadoPago.firmaValida(signature, requestId, dataId))
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    long paymentId;
    try {
      paymentId = Long.parseLong(dataId);
    } catch (NumberFormatException e) {
      return ResponseEntity.ok().build();
    }
    service.notificar(paymentId);
    return ResponseEntity.ok().build();
  }
}
