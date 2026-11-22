package pe.edu.upeu.garritas.pago.repository;

import java.util.List;
import java.util.Optional;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.jpa.repository.JpaRepository;
import pe.edu.upeu.garritas.pago.entity.Pago;

public interface PagoRepository extends JpaRepository<Pago, Long> {
  List<Pago> findByIdVenta(Long idVenta);

  @Lock(LockModeType.PESSIMISTIC_WRITE)
  @Query("select p from Pago p where p.idVenta = :idVenta")
  Optional<Pago> lockByVenta(@Param("idVenta") Long idVenta);

  List<Pago> findByIdCliente(String idCliente);
}
