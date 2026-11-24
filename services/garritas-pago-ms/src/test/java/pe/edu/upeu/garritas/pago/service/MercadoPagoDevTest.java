package pe.edu.upeu.garritas.pago.service;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.HexFormat;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

class MercadoPagoDevTest {
  private static MercadoPagoService servicio(String token, String enabled, String mode, String back,
                                             String notification, String secret) {
    return new MercadoPagoService(token, enabled, mode, back, notification, secret);
  }

  @Test
  void sinTokenEnAutoSeSimulaYNoFallaElArranque() {
    assertFalse(servicio("", "auto", "test", "http://localhost:4200", "", "").enabled());
    assertTrue(servicio("credencial", "auto", "test", "http://localhost:4200", "", "").enabled());
    assertThrows(IllegalStateException.class,
        () -> servicio("", "true", "test", "http://localhost:4200", "", ""));
  }

  @Test
  void modoTestAceptaPagosDePruebaYModoLiveSoloReales() {
    var test = servicio("credencial", "true", "test", "http://localhost:4200", "", "");
    assertTrue(test.expectedMode(false));
    assertTrue(test.expectedMode(true));
    var live = servicio("credencial", "true", "live", "https://example.test", "", "");
    assertTrue(live.expectedMode(true));
    assertFalse(live.expectedMode(false));
    assertFalse(live.expectedMode(null));
  }

  @Test
  void localhostNoEnviaBackUrlsNiWebhookYBuscaSinRetorno() {
    var service = servicio("credencial", "true", "test", "http://localhost:4200", "", "");
    var builder = RestClient.builder().baseUrl("https://mock.example");
    var server = MockRestServiceServer.bindTo(builder).build();
    ReflectionTestUtils.setField(service, "rest", builder.build());
    server.expect(requestTo("https://mock.example/checkout/preferences"))
        .andExpect(method(HttpMethod.POST))
        .andExpect(jsonPath("$.external_reference").value("garritas:prueba"))
        .andExpect(jsonPath("$.items[0].id").value("venta-1"))
        .andExpect(jsonPath("$.items[0].currency_id").value("PEN"))
        .andExpect(jsonPath("$.back_urls").doesNotExist())
        .andExpect(jsonPath("$.auto_return").doesNotExist())
        .andExpect(jsonPath("$.notification_url").doesNotExist())
        .andRespond(withSuccess("""
            {"id":"preferencia","init_point":"https://example.test/checkout",
             "sandbox_init_point":"https://example.test/sandbox"}
            """, MediaType.APPLICATION_JSON));
    server.expect(requestToUriTemplate(
            "https://mock.example/v1/payments/search?external_reference=garritas:prueba&sort=date_created&criteria=desc"))
        .andRespond(withSuccess("""
            {"results":[{"id":42,"status":"approved","external_reference":"garritas:prueba",
              "transaction_amount":15.50,"currency_id":"PEN","live_mode":false}]}
            """, MediaType.APPLICATION_JSON));

    var preference = service.crearPreferencia(1, "garritas:prueba", new BigDecimal("15.50"));
    assertEquals("https://example.test/checkout", preference.initPoint());
    var payment = service.buscarPagos("garritas:prueba").getFirst();
    assertEquals(42, payment.id());
    assertEquals("approved", payment.payment().status());
    server.verify();
  }

  @Test
  void desplegadoEnviaBackUrlsYWebhook() {
    var service = servicio("credencial", "true", "test", "https://tienda.example/",
        "https://gateway.example/api/v1/pagos/webhook", "secreto");
    var builder = RestClient.builder().baseUrl("https://mock.example");
    var server = MockRestServiceServer.bindTo(builder).build();
    ReflectionTestUtils.setField(service, "rest", builder.build());
    server.expect(requestTo("https://mock.example/checkout/preferences"))
        .andExpect(jsonPath("$.back_urls.success").value("https://tienda.example/compras?venta_id=7"))
        .andExpect(jsonPath("$.auto_return").value("approved"))
        .andExpect(jsonPath("$.notification_url").value("https://gateway.example/api/v1/pagos/webhook"))
        .andRespond(withSuccess("""
            {"id":"preferencia","init_point":"https://example.test/checkout"}
            """, MediaType.APPLICATION_JSON));
    service.crearPreferencia(7, "garritas:x", new BigDecimal("10.00"));
    server.verify();
  }

  @Test
  void validaFirmaDelWebhook() throws Exception {
    var service = servicio("credencial", "true", "test", "http://localhost:4200", "", "secreto");
    String manifest = "id:123456;request-id:req-1;ts:1704908010;";
    var mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec("secreto".getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
    String v1 = HexFormat.of().formatHex(mac.doFinal(manifest.getBytes(StandardCharsets.UTF_8)));

    assertTrue(service.firmaValida("ts=1704908010,v1=" + v1, "req-1", "123456"));
    assertFalse(service.firmaValida("ts=1704908010,v1=" + v1, "req-2", "123456"));
    assertFalse(service.firmaValida("ts=1704908010,v1=" + v1, "req-1", "999"));
    assertFalse(service.firmaValida("ts=1704908010,v1=zz", "req-1", "123456"));
    assertFalse(service.firmaValida(null, "req-1", "123456"));
    assertFalse(servicio("credencial", "true", "test", "http://localhost:4200", "", "")
        .firmaValida("ts=1704908010,v1=" + v1, "req-1", "123456"));
  }
}
