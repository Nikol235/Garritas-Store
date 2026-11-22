package pe.edu.upeu.garritas.pago.service;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class MercadoPagoService {
  private final RestClient rest;
  private final boolean enabled;
  private final boolean sandbox;
  private final String backUrl;

  public MercadoPagoService(
      @Value("${app.mercadopago.access-token:}") String accessToken,
      @Value("${app.mercadopago.enabled:false}") boolean enabled,
      @Value("${app.mercadopago.sandbox:true}") boolean sandbox,
      @Value("${app.mercadopago.back-url:http://localhost:4200}") String backUrl) {
    if (enabled && accessToken.isBlank())
      throw new IllegalStateException("MP_ACCESS_TOKEN es obligatorio al habilitar Checkout Pro");
    this.enabled = enabled;
    this.sandbox = sandbox;
    this.backUrl = backUrl.replaceFirst("/+$", "");
    var requests = new SimpleClientHttpRequestFactory();
    requests.setConnectTimeout(Duration.ofSeconds(4));
    requests.setReadTimeout(Duration.ofSeconds(8));
    this.rest = RestClient.builder()
        .baseUrl("https://api.mercadopago.com")
        .requestFactory(requests)
        .defaultHeader("Authorization", "Bearer " + accessToken)
        .build();
  }

  public boolean enabled() {
    return enabled;
  }

  public record PreferenceResult(String preferenceId, String initPoint) {}

  public record VerifiedPayment(String status, String externalReference, BigDecimal amount,
                                String currency, Boolean liveMode) {}

  public PreferenceResult crearPreferencia(long ventaId, String reference, BigDecimal total) {
    String back = backUrl + "/compras?venta_id=" + ventaId;
    var item = Map.of("title", "Garritas Store - Venta #" + ventaId,
        "quantity", 1, "unit_price", total, "currency_id", "PEN");
    var body = Map.of("items", List.of(item), "external_reference", reference,
        "back_urls", Map.of("success", back, "failure", back, "pending", back),
        "auto_return", "approved");
    var response = Objects.requireNonNull(rest.post().uri("/checkout/preferences")
        .contentType(MediaType.APPLICATION_JSON).body(body).retrieve().body(Map.class));
    Object id = response.get("id");
    Object url = response.get(sandbox ? "sandbox_init_point" : "init_point");
    if (!(id instanceof String preferenceId) || preferenceId.isBlank()
        || !(url instanceof String checkout) || !checkout.startsWith("https://"))
      throw new IllegalStateException("Mercado Pago no devolvió una preferencia válida");
    return new PreferenceResult(preferenceId, checkout);
  }

  public VerifiedPayment verificarPago(long paymentId) {
    var payment = Objects.requireNonNull(rest.get().uri("/v1/payments/{id}", paymentId)
        .retrieve().body(Map.class));
    return new VerifiedPayment(
        (String) payment.get("status"), (String) payment.get("external_reference"),
        payment.get("transaction_amount") instanceof Number amount ? new BigDecimal(amount.toString()) : null,
        (String) payment.get("currency_id"), (Boolean) payment.get("live_mode"));
  }

  public boolean expectedMode(Boolean liveMode) {
    return liveMode != null && liveMode != sandbox;
  }
}
