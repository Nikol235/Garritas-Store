package pe.edu.upeu.garritas.pago.service;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

import java.math.BigDecimal;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.mock.env.MockEnvironment;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

class MercadoPagoDevTest {
  @Test
  void localDevUsesTestCheckoutAndCanSearchWithoutARedirect() {
    var environment = new MockEnvironment();
    environment.setActiveProfiles("dev");
    var service = new MercadoPagoService("credencial-ficticia", true, false,
        "http://localhost:4200", environment);
    assertTrue(service.expectedMode(false));
    assertFalse(service.expectedMode(true));

    var builder = RestClient.builder().baseUrl("https://mock.example");
    var server = MockRestServiceServer.bindTo(builder).build();
    ReflectionTestUtils.setField(service, "rest", builder.build());
    server.expect(requestTo("https://mock.example/checkout/preferences"))
        .andExpect(method(HttpMethod.POST))
        .andExpect(jsonPath("$.external_reference").value("garritas:prueba"))
        .andExpect(jsonPath("$.back_urls").doesNotExist())
        .andExpect(jsonPath("$.auto_return").doesNotExist())
        .andRespond(withSuccess("""
            {"id":"preferencia","init_point":"https://example.test/real",
             "sandbox_init_point":"https://example.test/prueba"}
            """, MediaType.APPLICATION_JSON));
    server.expect(requestToUriTemplate(
            "https://mock.example/v1/payments/search?external_reference=garritas:prueba&sort=date_created&criteria=desc"))
        .andRespond(withSuccess("""
            {"results":[{"id":42,"status":"approved","external_reference":"garritas:prueba",
              "transaction_amount":15.50,"currency_id":"PEN","live_mode":false}]}
            """, MediaType.APPLICATION_JSON));

    var preference = service.crearPreferencia(1, "garritas:prueba", new BigDecimal("15.50"));
    assertEquals("https://example.test/prueba", preference.initPoint());
    var payment = service.buscarPagos("garritas:prueba").getFirst();
    assertEquals(42, payment.id());
    assertEquals("approved", payment.payment().status());
    server.verify();
  }

  @Test
  void realModeRequiresExplicitProdProfile() {
    var environment = new MockEnvironment();
    environment.setActiveProfiles("prod");
    var service = new MercadoPagoService("credencial-ficticia", true, false,
        "https://example.test", environment);
    assertTrue(service.expectedMode(true));
    assertFalse(service.expectedMode(false));
  }
}
