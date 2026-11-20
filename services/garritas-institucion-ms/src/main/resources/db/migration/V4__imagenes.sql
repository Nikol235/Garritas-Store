-- La FK garantiza que una foto pertenece a un registro del mismo microservicio.
CREATE TABLE recurso_imagen (
  id_recurso BIGINT PRIMARY KEY REFERENCES sedes(id) ON DELETE CASCADE,
  archivo VARCHAR(64) NOT NULL UNIQUE
);
