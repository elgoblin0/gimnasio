-- Migración 004: peso actual y auditoría de plan/vencimiento.
-- Importar en phpMyAdmin o con el cliente mysql. Conserva los datos.
-- Se puede repetir: la tabla se conserva y los triggers se reemplazan.
-- Cada trigger tiene una sola sentencia: no hace falta cambiar DELIMITER.
USE gimnasio;

CREATE TABLE IF NOT EXISTS auditoria_socios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    socio_id INT NOT NULL,
    plan_anterior INT NOT NULL,
    plan_nuevo INT NOT NULL,
    vencimiento_anterior DATE NOT NULL,
    vencimiento_nuevo DATE NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (socio_id) REFERENCES socios(id),
    FOREIGN KEY (plan_anterior) REFERENCES planes(id),
    FOREIGN KEY (plan_nuevo) REFERENCES planes(id)
);

DROP TRIGGER IF EXISTS copiar_peso_socio;
CREATE TRIGGER copiar_peso_socio AFTER INSERT ON registros_peso
FOR EACH ROW
    UPDATE socios SET peso = NEW.peso WHERE id = NEW.socio_id;

DROP TRIGGER IF EXISTS auditar_plan_socio;
CREATE TRIGGER auditar_plan_socio AFTER UPDATE ON socios
FOR EACH ROW
    INSERT INTO auditoria_socios
        (socio_id, plan_anterior, plan_nuevo, vencimiento_anterior, vencimiento_nuevo)
    SELECT NEW.id, OLD.plan_id, NEW.plan_id, OLD.fecha_vencimiento, NEW.fecha_vencimiento FROM DUAL
    WHERE NOT (OLD.plan_id <=> NEW.plan_id)
       OR NOT (OLD.fecha_vencimiento <=> NEW.fecha_vencimiento);
