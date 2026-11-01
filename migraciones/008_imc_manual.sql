-- =============================================
-- Migración 008: IMC manual (T9)
-- Para quien ya tiene la base creada con la versión anterior.
-- Conserva todos los datos. Ningún socio empieza con IMC manual.
-- Se puede importar en phpMyAdmin (pestaña Importar) o correr con el cliente mysql.
-- Es segura de repetir: si la columna ya existe, no hace nada.
-- =============================================

USE gimnasio;

SET @tiene_imc_manual = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'gimnasio' AND TABLE_NAME = 'socios' AND COLUMN_NAME = 'imc_manual'
);

SET @sql = IF(
    @tiene_imc_manual = 0,
    'ALTER TABLE socios ADD COLUMN imc_manual DECIMAL(4,2) NULL',
    'SELECT ''Nada que migrar: socios.imc_manual ya existe'' AS resultado'
);

PREPARE migracion FROM @sql;
EXECUTE migracion;
DEALLOCATE PREPARE migracion;
