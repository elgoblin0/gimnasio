-- =============================================
-- Migración 003: precio de los planes y tabla de pagos
-- Para quien ya tiene la base creada con la versión anterior.
-- Conserva todos los datos. Los socios existentes empiezan sin pagos en su historial.
-- Los planes de ejemplo reciben su precio; otro plan queda en 0 hasta editarlo en la pantalla.
-- Se puede importar en phpMyAdmin (pestaña Importar) o correr con el cliente mysql.
-- Es segura de repetir: si la columna o la tabla ya existen, no hace nada.
-- =============================================

USE gimnasio;

SET @tiene_precio = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'gimnasio' AND TABLE_NAME = 'planes' AND COLUMN_NAME = 'precio'
);

SET @sql = IF(
    @tiene_precio = 0,
    'ALTER TABLE planes ADD COLUMN precio DECIMAL(8,2) NOT NULL DEFAULT 0',
    'SELECT ''Nada que migrar: planes.precio ya existe'' AS resultado'
);

PREPARE migracion FROM @sql;
EXECUTE migracion;
DEALLOCATE PREPARE migracion;

UPDATE planes SET precio = 1500.00 WHERE nombre = 'Mensual libre' AND precio = 0;
UPDATE planes SET precio = 1000.00 WHERE nombre = 'Mensual 3 dias' AND precio = 0;
UPDATE planes SET precio = 4000.00 WHERE nombre = 'Trimestral' AND precio = 0;
UPDATE planes SET precio = 14000.00 WHERE nombre = 'Anual' AND precio = 0;

CREATE TABLE IF NOT EXISTS pagos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    socio_id INT NOT NULL,
    plan_id INT NOT NULL,
    fecha DATE NOT NULL,
    monto DECIMAL(8,2) NOT NULL,
    dias_plan INT NOT NULL,
    dias_restantes INT NOT NULL,
    vencimiento_nuevo DATE NOT NULL,
    FOREIGN KEY (socio_id) REFERENCES socios(id),
    FOREIGN KEY (plan_id) REFERENCES planes(id)
);
