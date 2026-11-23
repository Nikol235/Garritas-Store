package pe.edu.upeu.garritas.pago.service;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.web.server.ResponseStatusException;
import pe.edu.upeu.garritas.common.CurrentUser;
import pe.edu.upeu.garritas.common.Outbox;
import pe.edu.upeu.garritas.common.SagaEvent;
import pe.edu.upeu.garritas.pago.entity.EstadoPago;
import pe.edu.upeu.garritas.pago.entity.MetodoPago;
import pe.edu.upeu.garritas.pago.entity.Pago;
import pe.edu.upeu.garritas.pago.mapper.PagoMapper;
import pe.edu.upeu.garritas.pago.repository.PagoRepository;
import pe.edu.upeu.garritas.pago.service.MercadoPagoService.PaymentResult;
import pe.edu.upeu.garritas.pago.service.MercadoPagoService.VerifiedPayment;

class PagoConfirmacionTest {
  private final PagoRepository pagos = mock(PagoRepository.class);
  private final MercadoPagoService proveedor = mock(MercadoPagoService.class);
  private final Outbox outbox = mock(Outbox.class);
  private final PagoService servicio = new PagoService(pagos, mock(PagoMapper.class), proveedor, outbox);
  private final Pago pago = Pago.builder()
      .idVenta(42L).idCliente("cliente").monto(new BigDecimal("15.50"))
      .metodo(MetodoPago.TARJETA).estado(EstadoPago.PENDIENTE)
      .referenciaExterna("garritas:referencia-prueba").preferenceId("preferencia-prueba").build();

  @BeforeEach
  void preparar() {
    when(pagos.lockByVenta(42L)).thenReturn(Optional.of(pago));
    when(proveedor.enabled()).thenReturn(true);
    when(proveedor.expectedMode(false)).thenReturn(true);
  }

  @Test
  void confirmaUnaVezYPublicaLaSaga() {
    responde("approved", pago.getReferenciaExterna(), "15.50", "PEN", false);
    try (var usuario = mockStatic(CurrentUser.class)) {
      servicio.confirmar(42L, 100L);
      servicio.confirmar(42L, 100L);
      usuario.verify(() -> CurrentUser.requireOwner("cliente"), times(2));
    }
    assertEquals(EstadoPago.APROBADO, pago.getEstado());
    assertEquals(100L, pago.getPaymentId());
    verify(proveedor).verificarPago(100L);
    var evento = ArgumentCaptor.forClass(SagaEvent.class);
    verify(outbox).append(evento.capture());
    assertEquals("pago.validado", evento.getValue().type());
  }

  @Test
  void noConfirmaCuandoElImporteNoCoincide() {
    responde("approved", pago.getReferenciaExterna(), "14.50", "PEN", false);
    assertInvalido();
  }

  @Test
  void noConfirmaCuandoLaReferenciaNoCoincide() {
    responde("approved", "referencia-no-vinculada", "15.50", "PEN", false);
    assertInvalido();
  }

  @Test
  void noConfirmaCuandoLaMonedaOElEntornoNoCoinciden() {
    responde("approved", pago.getReferenciaExterna(), "15.50", "USD", false);
    assertInvalido();
    responde("approved", pago.getReferenciaExterna(), "15.50", "PEN", true);
    assertInvalido();
  }

  @Test
  void mantienePendienteUnPagoEnRevision() {
    responde("in_process", pago.getReferenciaExterna(), "15.50", "PEN", false);
    try (var usuario = mockStatic(CurrentUser.class)) {
      servicio.confirmar(42L, 100L);
    }
    assertEquals(EstadoPago.PENDIENTE, pago.getEstado());
    verify(pagos, never()).saveAndFlush(any());
    verifyNoInteractions(outbox);
  }

  @Test
  void publicaRechazoCuandoElProveedorLoConfirma() {
    responde("rejected", pago.getReferenciaExterna(), "15.50", "PEN", false);
    try (var usuario = mockStatic(CurrentUser.class)) {
      servicio.confirmar(42L, 100L);
    }
    assertEquals(EstadoPago.RECHAZADO, pago.getEstado());
    var evento = ArgumentCaptor.forClass(SagaEvent.class);
    verify(outbox).append(evento.capture());
    assertEquals("pago.fallido", evento.getValue().type());
  }

  @Test
  void buscaPorReferenciaYConfirmaSinRetornoDelNavegador() {
    var anterior = new VerifiedPayment("rejected", pago.getReferenciaExterna(), pago.getMonto(), "PEN", false);
    var aprobado = new VerifiedPayment("approved", pago.getReferenciaExterna(), pago.getMonto(), "PEN", false);
    when(proveedor.buscarPagos(pago.getReferenciaExterna()))
        .thenReturn(List.of(new PaymentResult(99L, anterior), new PaymentResult(100L, aprobado)));
    try (var usuario = mockStatic(CurrentUser.class)) {
      servicio.confirmar(42L, null);
    }
    assertEquals(EstadoPago.APROBADO, pago.getEstado());
    assertEquals(100L, pago.getPaymentId());
    verify(proveedor, never()).verificarPago(anyLong());
  }

  @Test
  void mantienePendienteSiElProveedorTodaviaNoTienePago() {
    when(proveedor.buscarPagos(pago.getReferenciaExterna())).thenReturn(List.of());
    try (var usuario = mockStatic(CurrentUser.class)) {
      servicio.confirmar(42L, null);
    }
    assertEquals(EstadoPago.PENDIENTE, pago.getEstado());
    verifyNoInteractions(outbox);
  }

  private void responde(String estado, String referencia, String monto, String moneda, boolean real) {
    when(proveedor.verificarPago(100L))
        .thenReturn(new VerifiedPayment(estado, referencia, new BigDecimal(monto), moneda, real));
  }

  private void assertInvalido() {
    try (var usuario = mockStatic(CurrentUser.class)) {
      var error = assertThrows(ResponseStatusException.class, () -> servicio.confirmar(42L, 100L));
      assertEquals(422, error.getStatusCode().value());
    }
    assertEquals(EstadoPago.PENDIENTE, pago.getEstado());
    verify(pagos, never()).saveAndFlush(any());
    verifyNoInteractions(outbox);
  }
}
