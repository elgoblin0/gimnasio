-- =============================================
-- Migración 006: rutina por día
-- Para quien ya tiene la base creada con la versión anterior.
-- Conserva todos los datos. Las entradas anteriores quedan sin rutina ni día.
-- Se puede importar en phpMyAdmin (pestaña Importar) o correr con el cliente mysql.
-- Es segura de repetir: lo que ya existe no se vuelve a crear.
-- =============================================

USE gimnasio;

SET @tiene_dia = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'gimnasio' AND TABLE_NAME = 'asistencias' AND COLUMN_NAME = 'dia_rutina'
);

SET @sql = IF(
    @tiene_dia = 0,
    'ALTER TABLE asistencias
        ADD COLUMN rutina_id INT NULL,
        ADD COLUMN dia_rutina INT NULL,
        ADD FOREIGN KEY (rutina_id) REFERENCES rutinas(id)',
    'SELECT ''Nada que migrar: asistencias.dia_rutina ya existe'' AS resultado'
);

PREPARE migracion FROM @sql;
EXECUTE migracion;
DEALLOCATE PREPARE migracion;

CREATE TABLE IF NOT EXISTS rutina_ejercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rutina_id INT NOT NULL,
    dia INT NOT NULL,
    orden INT NOT NULL,
    nombre VARCHAR(60) NOT NULL,
    series_repeticiones VARCHAR(20) NOT NULL,
    UNIQUE KEY un_ejercicio_por_lugar (rutina_id, dia, orden),
    FOREIGN KEY (rutina_id) REFERENCES rutinas(id)
);

CREATE TABLE IF NOT EXISTS ejercicios_realizados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asistencia_id INT NOT NULL,
    ejercicio_id INT NOT NULL,
    UNIQUE KEY un_ejercicio_por_entrada (asistencia_id, ejercicio_id),
    FOREIGN KEY (asistencia_id) REFERENCES asistencias(id),
    FOREIGN KEY (ejercicio_id) REFERENCES rutina_ejercicios(id)
);

-- INSERT IGNORE: el UNIQUE evita duplicar los ejercicios al repetir la migración
INSERT IGNORE INTO rutina_ejercicios (rutina_id, dia, orden, nombre, series_repeticiones) VALUES
(1, 1, 1, 'Caminata en cinta', '20 min'),
(1, 1, 2, 'Sentadilla sin peso', '3x12'),
(1, 1, 3, 'Plancha', '3x20 s'),
(1, 2, 1, 'Bicicleta fija', '20 min'),
(1, 2, 2, 'Remo en máquina', '3x12'),
(1, 2, 3, 'Elevación de talones', '3x15'),
(1, 3, 1, 'Elíptica', '20 min'),
(1, 3, 2, 'Prensa de piernas', '3x12'),
(1, 3, 3, 'Abdominales cortos', '3x15'),
(2, 1, 1, 'Intervalos en cinta', '25 min'),
(2, 1, 2, 'Sentadilla con mancuernas', '3x12'),
(2, 1, 3, 'Flexiones', '3x10'),
(2, 2, 1, 'Intervalos en bicicleta', '25 min'),
(2, 2, 2, 'Peso muerto rumano', '3x12'),
(2, 2, 3, 'Plancha lateral', '3x30 s'),
(2, 3, 1, 'Remo cardio', '20 min'),
(2, 3, 2, 'Zancadas', '3x12'),
(2, 3, 3, 'Press de hombros', '3x12'),
(3, 1, 1, 'HIIT en cinta', '20 min'),
(3, 1, 2, 'Sentadilla frontal', '4x8'),
(3, 1, 3, 'Dominadas', '4x6'),
(3, 2, 1, 'Burpees', '5x12'),
(3, 2, 2, 'Peso muerto', '4x6'),
(3, 2, 3, 'Press de banca', '4x8'),
(3, 3, 1, 'Saltos a cajón', '5x10'),
(3, 3, 2, 'Zancadas con barra', '4x10'),
(3, 3, 3, 'Remo con barra', '4x8'),
(4, 1, 1, 'Press de pecho en máquina', '3x12'),
(4, 1, 2, 'Jalón al pecho', '3x12'),
(4, 1, 3, 'Prensa de piernas', '3x12'),
(4, 2, 1, 'Curl de bíceps', '3x12'),
(4, 2, 2, 'Extensión de tríceps', '3x12'),
(4, 2, 3, 'Extensión de piernas', '3x12'),
(4, 3, 1, 'Press de hombros en máquina', '3x12'),
(4, 3, 2, 'Remo en máquina', '3x12'),
(4, 3, 3, 'Curl femoral', '3x12'),
(5, 1, 1, 'Press de banca', '4x10'),
(5, 1, 2, 'Remo con barra', '4x10'),
(5, 1, 3, 'Press militar', '4x10'),
(5, 2, 1, 'Sentadilla', '4x10'),
(5, 2, 2, 'Peso muerto rumano', '4x10'),
(5, 2, 3, 'Elevación de talones', '4x15'),
(5, 3, 1, 'Dominadas asistidas', '4x10'),
(5, 3, 2, 'Fondos', '4x10'),
(5, 3, 3, 'Curl de bíceps', '4x10'),
(6, 1, 1, 'Press de banca', '5x8'),
(6, 1, 2, 'Press inclinado', '5x8'),
(6, 1, 3, 'Fondos con lastre', '5x8'),
(6, 2, 1, 'Sentadilla', '5x8'),
(6, 2, 2, 'Peso muerto', '5x5'),
(6, 2, 3, 'Prensa de piernas', '5x10'),
(6, 3, 1, 'Dominadas con lastre', '5x8'),
(6, 3, 2, 'Remo con barra', '5x8'),
(6, 3, 3, 'Curl con barra', '5x8'),
(7, 1, 1, 'Caminata', '20 min'),
(7, 1, 2, 'Estiramiento de piernas', '10 min'),
(7, 1, 3, 'Movilidad de hombros', '5 min'),
(7, 2, 1, 'Bicicleta suave', '20 min'),
(7, 2, 2, 'Estiramiento de espalda', '10 min'),
(7, 2, 3, 'Movilidad de cadera', '5 min'),
(7, 3, 1, 'Elíptica suave', '20 min'),
(7, 3, 2, 'Estiramiento general', '10 min'),
(7, 3, 3, 'Respiración y equilibrio', '5 min'),
(8, 1, 1, 'Cardio moderado', '30 min'),
(8, 1, 2, 'Sentadilla', '3x12'),
(8, 1, 3, 'Flexiones', '3x12'),
(8, 2, 1, 'Bicicleta', '30 min'),
(8, 2, 2, 'Remo con mancuerna', '3x12'),
(8, 2, 3, 'Plancha', '3x40 s'),
(8, 3, 1, 'Elíptica', '30 min'),
(8, 3, 2, 'Zancadas', '3x12'),
(8, 3, 3, 'Press de hombros', '3x12'),
(9, 1, 1, 'Circuito funcional', '30 min'),
(9, 1, 2, 'Kettlebell swing', '4x15'),
(9, 1, 3, 'Plancha con toque', '4x20'),
(9, 2, 1, 'Cardio moderado', '30 min'),
(9, 2, 2, 'Sentadilla con salto', '4x12'),
(9, 2, 3, 'Dominadas', '4x8'),
(9, 3, 1, 'Circuito con TRX', '30 min'),
(9, 3, 2, 'Peso muerto con kettlebell', '4x12'),
(9, 3, 3, 'Flexiones con rotación', '4x12');
