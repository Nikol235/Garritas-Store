-- Almacenar imagen en la base de datos (bytea) en vez de disco local.
ALTER TABLE recurso_imagen ADD COLUMN datos BYTEA;
ALTER TABLE recurso_imagen ADD COLUMN content_type VARCHAR(16);
ALTER TABLE recurso_imagen ALTER COLUMN archivo DROP NOT NULL;
