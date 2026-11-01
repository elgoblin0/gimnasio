-- =============================================
-- Migración 005: cancelar y congelar planes
-- Para quien ya tiene la base creada con la versión anterior.
-- Conserva todos los datos. Necesita la migración 003 (los períodos se cuentan por pago).
-- Se puede importar en phpMyAdmin (pestaña Importar) o correr con el cliente mysql.
-- Es segura de repetir: si la columna o la tabla ya existen, no hace nada.
-- =============================================

USE gimnasio;

SET @tiene_cancelacion = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'gimnasio' AND TABLE_NAME = 'socios' AND COLUMN_NAME = 'fecha_cancelacion'
);

SET @sql = IF(
    @tiene_cancelacion = 0,
    'ALTER TABLE socios ADD COLUMN fecha_cancelacion DATE NULL',
    'SELECT ''Nada que migrar: socios.fecha_cancelacion ya existe'' AS resultado'
);

PREPARE migracion FROM @sql;
EXECUTE migracion;
DEALLOCATE PREPARE migracion;

CREATE TABLE IF NOT EXISTS congelamientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    socio_id INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    FOREIGN KEY (socio_id) REFERENCES socios(id)
);
