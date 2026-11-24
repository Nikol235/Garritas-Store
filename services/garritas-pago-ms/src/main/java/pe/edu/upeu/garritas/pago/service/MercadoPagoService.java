package pe.edu.upeu.garritas.pago.service;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

/**
 * Cliente de Checkout Pro (API de preferencias).
 *
 * <p>El mismo código sirve en DEV y desplegado; solo cambia la configuración:
 * <ul>
 *   <li>{@code app.mercadopago.enabled}: {@code auto} (activo si hay token), {@code true} o {@code false}.</li>
 *   <li>{@code app.mercadopago.mode}: {@code test} (credenciales de prueba) o {@code live} (cobros reales).</li>
 *   <li>{@code back-url} y {@code notification-url} solo se envían si son HTTPS, porque
 *       Mercado Pago no acepta dominios locales.</li>
 * </ul>
 */
@Service
public class MercadoPagoService {
  private static final Logger log = LoggerFactory.getLogger(MercadoPagoService.class);

  private final RestClient rest;
  private final boolean enabled;
  private final boolean live;
  private final String backUrl;
  private final String notificationUrl;
  private final String webhookSecret;

  public MercadoPagoService(
      @Value("${app.mercadopago.access-token:}") String accessToken,
      @Value("${app.mercadopago.enabled:auto}") String enabled,
      @Value("${app.mercadopago.mode:test}") String mode,
      @Value("${app.mercadopago.back-url:http://localhost:4200}") String backUrl,
      @Value("${app.mercadopago.notification-url:}") String notificationUrl,
      @Value("${app.mercadopago.webhook-secret:}") String webhookSecret) {
    String token = accessToken == null ? "" : accessToken.trim();
    this.enabled = switch (enabled.trim().toLowerCase(Locale.ROOT)) {
      case "true" -> {
        if (token.isEmpty())
          throw new IllegalStateException("MP_ACCESS_TOKEN es obligatorio con MP_CHECKOUT_ENABLED=true");
        yield true;
      }
      case "false" -> false;
      case "auto" -> !token.isEmpty();
      default -> throw new IllegalStateException("MP_CHECKOUT_ENABLED debe ser auto, true o false");
    };
    this.live = switch (mode.trim().toLowerCase(Locale.ROOT)) {
      case "live" -> true;
      case "test" -> false;
      default -> throw new IllegalStateException("MP_MODE debe ser test o live");
    };
    this.backUrl = backUrl.replaceFirst("/+$", "");
    this.notificationUrl = notificationUrl.trim();
    this.webhookSecret = webhookSecret.trim();
    var requests = new SimpleClientHttpRequestFactory();
    requests.setConnectTimeout(Duration.ofSeconds(4));
    requests.setReadTimeout(Duration.ofSeconds(8));
    this.rest = RestClient.builder()
        .baseUrl("https://api.mercadopago.com")
        .requestFactory(requests)
        .defaultHeader("Authorization", "Bearer " + token)
        .build();
    if (this.enabled)
      log.info("component=mercadopago checkout=activo modo={} backUrls={} webhook={}",
          live ? "live" : "test", this.backUrl.startsWith("https://"),
          this.notificationUrl.startsWith("https://"));
    else
      log.warn("component=mercadopago checkout=inactivo: sin MP_ACCESS_TOKEN los pagos se simulan");
  }

  public boolean enabled() {
    return enabled;
  }

  public record PreferenceResult(String preferenceId, String initPoint) {}

  public record VerifiedPayment(String status, String externalReference, BigDecimal amount,
                                String currency, Boolean liveMode) {}

  public record PaymentResult(long id, VerifiedPayment payment) {}

  public PreferenceResult crearPreferencia(long ventaId, String reference, BigDecimal total) {
    var item = new LinkedHashMap<String, Object>();
    item.put("id", "venta-" + ventaId);
    item.put("title", "Garritas Store - Venta #" + ventaId);
    item.put("description", "Productos para mascotas - Garritas Store");
    item.put("category_id", "others");
    item.put("quantity", 1);
    item.put("currency_id", "PEN");
    item.put("unit_price", total);
    var body = new LinkedHashMap<String, Object>();
    body.put("items", List.of(item));
    body.put("external_reference", reference);
    // Mercado Pago rechaza dominios locales: en localhost el comprador vuelve a "Mis compras"
    // y verifica el pago; desplegado (HTTPS) vuelve solo a /compras.
    if (backUrl.startsWith("https://")) {
      String back = backUrl + "/compras?venta_id=" + ventaId;
      body.put("back_urls", Map.of("success", back, "failure", back, "pending", back));
      body.put("auto_return", "approved");
    }
    if (notificationUrl.startsWith("https://"))
      body.put("notification_url", notificationUrl);
    var response = Objects.requireNonNull(rest.post().uri("/checkout/preferences")
        .contentType(MediaType.APPLICATION_JSON).body(body).retrieve().body(Map.class));
    Object id = response.get("id");
    Object url = response.get("init_point");
    if (!(id instanceof String preferenceId) || preferenceId.isBlank()
        || !(url instanceof String checkout) || !checkout.startsWith("https://"))
      throw new IllegalStateException("Mercado Pago no devolvió una preferencia válida");
    return new PreferenceResult(preferenceId, checkout);
  }

  public VerifiedPayment verificarPago(long paymentId) {
    var payment = Objects.requireNonNull(rest.get().uri("/v1/payments/{id}", paymentId)
        .retrieve().body(Map.class));
    return readPayment(payment);
  }

  public List<PaymentResult> buscarPagos(String referencia) {
    var result = Objects.requireNonNull(rest.get().uri(builder -> builder.path("/v1/payments/search")
        .queryParam("external_reference", referencia)
        .queryParam("sort", "date_created").queryParam("criteria", "desc")
        .build()).retrieve().body(Map.class));
    if (!(result.get("results") instanceof List<?> payments))
      throw new IllegalStateException("Mercado Pago no devolvió resultados válidos");
    return payments.stream()
        .filter(item -> item instanceof Map<?, ?> payment && payment.get("id") instanceof Number)
        .map(item -> (Map<?, ?>) item)
        .map(payment -> new PaymentResult(((Number) payment.get("id")).longValue(), readPayment(payment)))
        .toList();
  }

  private VerifiedPayment readPayment(Map<?, ?> payment) {
    return new VerifiedPayment(
        (String) payment.get("status"), (String) payment.get("external_reference"),
        payment.get("transaction_amount") instanceof Number amount ? new BigDecimal(amount.toString()) : null,
        (String) payment.get("currency_id"), (Boolean) payment.get("live_mode"));
  }

  /**
   * En modo live solo se aceptan cobros reales. En modo test el token ya limita la consulta a los
   * pagos de la cuenta de prueba, así que no se depende del valor de live_mode.
   */
  public boolean expectedMode(Boolean liveMode) {
    return !live || Boolean.TRUE.equals(liveMode);
  }

  public boolean webhookConfigured() {
    return !webhookSecret.isEmpty();
  }

  /**
   * Valida x-signature ("ts=...,v1=...") con HMAC-SHA256 sobre el manifiesto
   * "id:[data.id];request-id:[x-request-id];ts:[ts];" según la documentación de Webhooks.
   */
  public boolean firmaValida(String xSignature, String xRequestId, String dataId) {
    if (webhookSecret.isEmpty() || xSignature == null || dataId == null || dataId.isBlank())
      return false;
    String ts = null, v1 = null;
    for (String part : xSignature.split(",")) {
      String[] kv = part.trim().split("=", 2);
      if (kv.length != 2) continue;
      if (kv[0].trim().equals("ts")) ts = kv[1].trim();
      else if (kv[0].trim().equals("v1")) v1 = kv[1].trim();
    }
    if (ts == null || v1 == null) return false;
    var manifest = new StringBuilder("id:").append(dataId.toLowerCase(Locale.ROOT)).append(';');
    if (xRequestId != null && !xRequestId.isBlank())
      manifest.append("request-id:").append(xRequestId).append(';');
    manifest.append("ts:").append(ts).append(';');
    try {
      var mac = Mac.getInstance("HmacSHA256");
      mac.init(new SecretKeySpec(webhookSecret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
      byte[] expected = mac.doFinal(manifest.toString().getBytes(StandardCharsets.UTF_8));
      return MessageDigest.isEqual(expected, HexFormat.of().parseHex(v1.toLowerCase(Locale.ROOT)));
    } catch (IllegalArgumentException e) {
      return false;
    } catch (java.security.GeneralSecurityException e) {
      throw new IllegalStateException(e);
    }
  }
}
