-- =============================================
-- Migración 009: salida del gimnasio (T10)
-- Para quien ya tiene la base creada con la versión anterior.
-- Conserva todos los datos. Las entradas viejas quedan sin salida:
-- solo cuentan como "adentro" las de hoy, así que no inflan la ocupación.
-- Se puede importar en phpMyAdmin (pestaña Importar) o correr con el cliente mysql.
-- Es segura de repetir: si la columna ya existe, no hace nada.
-- =============================================

USE gimnasio;

SET @tiene_salida = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'gimnasio' AND TABLE_NAME = 'asistencias' AND COLUMN_NAME = 'fecha_hora_salida'
);

SET @sql = IF(
    @tiene_salida = 0,
    'ALTER TABLE asistencias ADD COLUMN fecha_hora_salida DATETIME NULL AFTER fecha_hora',
    'SELECT ''Nada que migrar: asistencias.fecha_hora_salida ya existe'' AS resultado'
);

PREPARE migracion FROM @sql;
EXECUTE migracion;
DEALLOCATE PREPARE migracion;
