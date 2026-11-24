-- Almacenar imagen en la base de datos (bytea) en vez de disco local.
-- Esto es necesario para Railway donde el filesystem es efímero.
ALTER TABLE recurso_imagen ADD COLUMN datos BYTEA;
ALTER TABLE recurso_imagen ADD COLUMN content_type VARCHAR(16);
ALTER TABLE recurso_imagen ALTER COLUMN archivo DROP NOT NULL;
