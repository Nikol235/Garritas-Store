package pe.edu.upeu.garritas.venta.controller;

import jakarta.validation.Valid;
import java.util.*;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import pe.edu.upeu.garritas.venta.dto.*;
import pe.edu.upeu.garritas.venta.service.VentaService;

@RestController
@RequestMapping("/api/v1/ventas")
@RequiredArgsConstructor
public class VentaController {
  private final VentaService service;
  private final pe.edu.upeu.garritas.venta.service.ComprobanteService comprobantes;

  @GetMapping(value = "/{id}/comprobante", produces = "application/pdf")
  public org.springframework.http.ResponseEntity<byte[]> comprobante(@PathVariable Long id) {
    return org.springframework.http.ResponseEntity.ok()
        .header("Content-Disposition", "attachment; filename=Garritas-compra-" + id + ".pdf")
        .cacheControl(org.springframework.http.CacheControl.noStore())
        .body(comprobantes.generar(id));
  }

  @GetMapping
  public List<VentaResponse> listar() {
    return service.listar();
  }

  @GetMapping("/{id}")
  public VentaResponse obtener(@PathVariable Long id) {
    return service.obtener(id);
  }

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  public VentaResponse crear(
      @Valid @RequestBody VentaRequest request, @RequestHeader("Idempotency-Key") UUID key) {
    return service.crear(request, key);
  }
}
