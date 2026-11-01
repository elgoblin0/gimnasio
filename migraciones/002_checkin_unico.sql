-- =============================================
-- Migración 002: una sola entrada por socio y por día
-- Para quien ya tiene la base creada con la versión anterior.
-- Ojo: si un socio tiene varias entradas el mismo día, conserva la más antigua
-- y borra las demás. No toca ningún otro dato.
-- Se puede importar en phpMyAdmin (pestaña Importar) o correr con el cliente mysql.
-- Es segura de repetir: si la columna ya existe, no hace nada.
-- =============================================

USE gimnasio;

DELETE a
FROM asistencias a
JOIN asistencias b
    ON a.socio_id = b.socio_id
    AND DATE(a.fecha_hora) = DATE(b.fecha_hora)
    AND (a.fecha_hora > b.fecha_hora OR (a.fecha_hora = b.fecha_hora AND a.id > b.id));

SET @tiene_fecha = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'gimnasio' AND TABLE_NAME = 'asistencias' AND COLUMN_NAME = 'fecha'
);

SET @sql = IF(
    @tiene_fecha = 0,
    'ALTER TABLE asistencias
        ADD COLUMN fecha DATE GENERATED ALWAYS AS (DATE(fecha_hora)) STORED,
        ADD UNIQUE KEY una_entrada_por_dia (socio_id, fecha)',
    'SELECT ''Nada que migrar: asistencias.fecha ya existe'' AS resultado'
);

PREPARE migracion FROM @sql;
EXECUTE migracion;
DEALLOCATE PREPARE migracion;
