package pe.edu.upeu.garritas.pago.service;

import java.util.List;
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

    var confirmado = mpService.verificarPago(paymentId);
    String referencia = pago.getReferenciaExterna();
    String esperada = referencia != null && referencia.startsWith("garritas:")
        ? referencia : ventaId.toString();
    if (!Objects.equals(esperada, confirmado.externalReference())
        || confirmado.amount() == null || pago.getMonto().compareTo(confirmado.amount()) != 0
        || !"PEN".equals(confirmado.currency()) || !mpService.expectedMode(confirmado.liveMode()))
      throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY, "El pago no corresponde a esta venta");

    boolean aprobado = "approved".equals(confirmado.status());
    boolean rechazado = "rejected".equals(confirmado.status()) || "cancelled".equals(confirmado.status());
    if (!aprobado && !rechazado) return mapper.toResponse(pago);

    pago.setPaymentId(paymentId);
    pago.setEstado(aprobado ? EstadoPago.APROBADO : EstadoPago.RECHAZADO);
    repository.saveAndFlush(pago);
    outbox.append(new SagaEvent(
        java.util.UUID.randomUUID(), 1, aprobado ? "pago.validado" : "pago.fallido",
        pago.getIdVenta(), pago.getIdCliente(), pago.getMonto(), pago.getMetodo().name(),
        java.util.UUID.randomUUID().toString(), List.of(), java.time.Instant.now()));
    return mapper.toResponse(pago);
  }
}
