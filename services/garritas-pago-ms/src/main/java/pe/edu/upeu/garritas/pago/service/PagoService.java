package pe.edu.upeu.garritas.pago.service;

import java.util.Comparator;
import java.util.List;
import pe.edu.upeu.garritas.pago.service.MercadoPagoService.PaymentResult;
import pe.edu.upeu.garritas.pago.service.MercadoPagoService.VerifiedPayment;
import java.util.Objects;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import pe.edu.upeu.garritas.common.*;
import pe.edu.upeu.garritas.pago.dto.PagoResponse;
import pe.edu.upeu.garritas.pago.entity.EstadoPago;
import pe.edu.upeu.garritas.pago.entity.Pago;
import pe.edu.upeu.garritas.pago.mapper.PagoMapper;
import pe.edu.upeu.garritas.pago.repository.PagoRepository;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PagoService {
  private final PagoRepository repository;
  private final PagoMapper mapper;
  private final MercadoPagoService mpService;
  private final Outbox outbox;

  public List<PagoResponse> listar() {
    return (CurrentUser.admin()
            ? repository.findAll()
            : repository.findByIdCliente(CurrentUser.subject()))
        .stream().map(mapper::toResponse).toList();
  }

  public PagoResponse obtener(Long id) {
    var p =
        repository
            .findById(id)
            .orElseThrow(
                () -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Pago no encontrado"));
    CurrentUser.requireOwner(p.getIdCliente());
    return mapper.toResponse(p);
  }

  public PagoResponse porVenta(Long id) {
    var p =
        repository.findByIdVenta(id).stream()
            .findFirst()
            .orElseThrow(
                () ->
                    new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "Pago todavía no disponible"));
    CurrentUser.requireOwner(p.getIdCliente());
    return mapper.toResponse(p);
  }

  /**
   * Confirma un pago verificando con la API de Mercado Pago.
   * Llamado cuando el usuario regresa del checkout de MP con un payment_id.
   */
  @Transactional
  public PagoResponse confirmar(Long ventaId, Long paymentId) {
    Pago pago = repository.lockByVenta(ventaId)
        .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Pago no encontrado para esta venta"));
    CurrentUser.requireOwner(pago.getIdCliente());

    if (pago.getEstado() != EstadoPago.PENDIENTE) return mapper.toResponse(pago);
    if (!mpService.enabled() || pago.getPreferenceId() == null)
      throw new ResponseStatusException(HttpStatus.CONFLICT, "La venta no tiene un checkout activo");

    String referencia = pago.getReferenciaExterna();
    String esperada = referencia != null && referencia.startsWith("garritas:")
        ? referencia : ventaId.toString();
    PaymentResult resultado;
    if (paymentId == null) {
      resultado = mpService.buscarPagos(esperada).stream()
          .filter(p -> corresponde(pago, esperada, p.payment()))
          .min(Comparator.comparingInt(p -> prioridad(p.payment().status())))
          .orElse(null);
      if (resultado == null) return mapper.toResponse(pago);
    } else {
      resultado = new PaymentResult(paymentId, mpService.verificarPago(paymentId));
      if (!corresponde(pago, esperada, resultado.payment()))
        throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_CONTENT, "El pago no corresponde a esta venta");
    }

    String estado = resultado.payment().status();
    boolean aprobado = "approved".equals(estado);
    if (!aprobado && !rechazo(estado)) return mapper.toResponse(pago);

    pago.setPaymentId(resultado.id());
    pago.setEstado(aprobado ? EstadoPago.APROBADO : EstadoPago.RECHAZADO);
    repository.saveAndFlush(pago);
    outbox.append(new SagaEvent(
        java.util.UUID.randomUUID(), 1, aprobado ? "pago.validado" : "pago.fallido",
        pago.getIdVenta(), pago.getIdCliente(), pago.getMonto(), pago.getMetodo().name(),
        java.util.UUID.randomUUID().toString(), List.of(), java.time.Instant.now()));
    return mapper.toResponse(pago);
  }

  private boolean corresponde(Pago pago, String referencia, VerifiedPayment confirmado) {
    return Objects.equals(referencia, confirmado.externalReference())
        && confirmado.amount() != null && pago.getMonto().compareTo(confirmado.amount()) == 0
        && "PEN".equals(confirmado.currency()) && mpService.expectedMode(confirmado.liveMode());
  }

  private static boolean rechazo(String status) {
    return "rejected".equals(status) || "cancelled".equals(status);
  }

  private static int prioridad(String status) {
    if ("approved".equals(status)) return 0;
    return rechazo(status) ? 2 : 1;
  }
}
