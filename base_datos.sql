-- =============================================
-- Base de datos del sistema de gimnasio
-- Importar en phpMyAdmin (XAMPP)
-- =============================================

DROP DATABASE IF EXISTS gimnasio;
CREATE DATABASE gimnasio;
USE gimnasio;

-- ---------------------------------------------
-- USUARIOS
-- Quienes entran al sistema. clave_hash: nunca la contraseña en texto plano
-- rol: 'admin' o 'recepcion'
-- ---------------------------------------------
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    clave_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1
);

-- ---------------------------------------------
-- PLANES
-- duracion_dias: cuántos días dura el plan
-- dias_por_semana: cuántas veces puede entrar por semana (7 = libre)
-- precio: lo que se cobra hoy por el plan
-- ---------------------------------------------
CREATE TABLE planes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    duracion_dias INT NOT NULL,
    dias_por_semana INT NOT NULL,
    precio DECIMAL(8,2) NOT NULL
);

-- ---------------------------------------------
-- RUTINAS
-- Cada rutina corresponde a un objetivo + un nivel
-- objetivo: 'bajar peso', 'ganar musculo', 'mantenerse'
-- nivel: 'principiante', 'intermedio', 'avanzado'
-- ---------------------------------------------
CREATE TABLE rutinas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    objetivo VARCHAR(20) NOT NULL,
    nivel VARCHAR(20) NOT NULL,
    descripcion TEXT NOT NULL
);

-- ---------------------------------------------
-- EJERCICIOS DE CADA RUTINA
-- dia: 1 a 3. orden: posición del ejercicio dentro del día
-- ---------------------------------------------
CREATE TABLE rutina_ejercicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rutina_id INT NOT NULL,
    dia INT NOT NULL,
    orden INT NOT NULL,
    nombre VARCHAR(60) NOT NULL,
    series_repeticiones VARCHAR(20) NOT NULL,
    UNIQUE KEY un_ejercicio_por_lugar (rutina_id, dia, orden),
    FOREIGN KEY (rutina_id) REFERENCES rutinas(id)
);

-- ---------------------------------------------
-- SOCIOS
-- peso: peso actual en kg
-- altura: en metros (ej: 1.75)
-- fecha_cancelacion: NULL mientras el socio no esté cancelado
-- ---------------------------------------------
CREATE TABLE socios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ci VARCHAR(20) NOT NULL UNIQUE,
    telefono VARCHAR(20),
    peso DECIMAL(5,2) NOT NULL,
    altura DECIMAL(3,2) NOT NULL,
    objetivo VARCHAR(20) NOT NULL,
    nivel VARCHAR(20) NOT NULL,
    plan_id INT NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    fecha_cancelacion DATE NULL,
    FOREIGN KEY (plan_id) REFERENCES planes(id)
);

-- ---------------------------------------------
-- ASISTENCIAS
-- Una fila por cada vez que un socio entra al gimnasio
-- fecha: se calcula sola a partir de fecha_hora
-- rutina_id y dia_rutina: la rutina y el día que le tocaron en esa entrada
-- El UNIQUE impide dos entradas del mismo socio el mismo día
-- ---------------------------------------------
CREATE TABLE asistencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    socio_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    fecha DATE GENERATED ALWAYS AS (DATE(fecha_hora)) STORED,
    rutina_id INT NULL,
    dia_rutina INT NULL,
    UNIQUE KEY una_entrada_por_dia (socio_id, fecha),
    FOREIGN KEY (socio_id) REFERENCES socios(id),
    FOREIGN KEY (rutina_id) REFERENCES rutinas(id)
);

-- ---------------------------------------------
-- EJERCICIOS REALIZADOS
-- Una fila por cada ejercicio que el socio hizo en una entrada
-- ---------------------------------------------
CREATE TABLE ejercicios_realizados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asistencia_id INT NOT NULL,
    ejercicio_id INT NOT NULL,
    UNIQUE KEY un_ejercicio_por_entrada (asistencia_id, ejercicio_id),
    FOREIGN KEY (asistencia_id) REFERENCES asistencias(id),
    FOREIGN KEY (ejercicio_id) REFERENCES rutina_ejercicios(id)
);

-- ---------------------------------------------
-- REGISTROS DE PESO
-- Historial para ver el progreso del socio
-- ---------------------------------------------
CREATE TABLE registros_peso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    socio_id INT NOT NULL,
    fecha DATE NOT NULL,
    peso DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (socio_id) REFERENCES socios(id)
);

-- ---------------------------------------------
-- PAGOS
-- monto: se copia del plan, para que un cambio de precio no altere el historial
-- dias_restantes: los días que le quedaban al socio al pagar (sus "días extra")
-- vencimiento_nuevo: fecha de vencimiento que quedó después del pago
-- ---------------------------------------------
CREATE TABLE pagos (
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

-- ---------------------------------------------
-- CONGELAMIENTOS
-- El socio está congelado mientras fecha_inicio <= hoy < fecha_fin
-- ---------------------------------------------
CREATE TABLE congelamientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    socio_id INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    FOREIGN KEY (socio_id) REFERENCES socios(id)
);


-- T4: los triggers se crean antes de cargar los ejemplos.
CREATE TABLE auditoria_socios (
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
    SELECT NEW.id, OLD.plan_id, NEW.plan_id, OLD.fecha_vencimiento, NEW.fecha_vencimiento
    WHERE NOT (OLD.plan_id <=> NEW.plan_id)
       OR NOT (OLD.fecha_vencimiento <=> NEW.fecha_vencimiento);


-- =============================================
-- DATOS DE EJEMPLO
-- =============================================

-- Claves de prueba, indicadas en el README
INSERT INTO usuarios (nombre, usuario, clave_hash, rol) VALUES
('Administrador', 'admin', 'scrypt:32768:8:1$I2iosHuGMSOnvFl2$40495a77ec78854a5888ea54784fcb19a3fd4d90f1eeee63cc22c85a3a305d8fbde8196b283b2fcd2a058a3d244db6d28df48e9c048a4b1fb97cbafd0e8060ad', 'admin'),
('Recepción', 'recepcion', 'scrypt:32768:8:1$hbjtRoBZQnMGhguF$f3eb7e6aea797359965f263fa890f106b220eb3af7b2d7eb27b243cea8652809e94c979b1957473ec23b7bba3e8649cb86a86e68bef356ae3bec17538a2f0b14', 'recepcion');

INSERT INTO planes (nombre, duracion_dias, dias_por_semana, precio) VALUES
('Mensual libre', 30, 7, 1500.00),
('Mensual 3 dias', 30, 3, 1000.00),
('Trimestral', 90, 7, 4000.00),
('Anual', 365, 7, 14000.00);

INSERT INTO rutinas (nombre, objetivo, nivel, descripcion) VALUES
('Quema inicial',     'bajar peso',    'principiante', '30 min cinta + circuito suave de cuerpo completo'),
('Quema media',       'bajar peso',    'intermedio',   '40 min cardio por intervalos + circuito de fuerza'),
('Quema intensa',     'bajar peso',    'avanzado',     'HIIT 20 min + pesas en superserie'),
('Fuerza base',       'ganar musculo', 'principiante', 'Maquinas guiadas, 3x12 cuerpo completo'),
('Hipertrofia media', 'ganar musculo', 'intermedio',   'Rutina dividida torso / pierna, 4x10'),
('Hipertrofia pro',   'ganar musculo', 'avanzado',     'Rutina dividida por grupo muscular, 5x8 peso libre'),
('Activo suave',      'mantenerse',    'principiante', '20 min cardio + estiramientos'),
('Activo medio',      'mantenerse',    'intermedio',   '30 min cardio + 3x12 cuerpo completo'),
('Activo pro',        'mantenerse',    'avanzado',     'Entrenamiento funcional + cardio moderado');

INSERT INTO rutina_ejercicios (rutina_id, dia, orden, nombre, series_repeticiones) VALUES
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

-- Fechas relativas a hoy para que siempre haya socios en cada estado
INSERT INTO socios (nombre, ci, telefono, peso, altura, objetivo, nivel, plan_id, fecha_vencimiento) VALUES
('Ana Lopez',    '11111111A', '600111111', 68.00, 1.65, 'bajar peso',    'principiante', 1, DATE_ADD(CURDATE(), INTERVAL 20 DAY)), -- activo
('Carlos Ruiz',  '22222222B', '600222222', 75.50, 1.80, 'ganar musculo', 'intermedio',   2, DATE_ADD(CURDATE(), INTERVAL 5 DAY)),  -- por vencer
('Maria Gomez',  '33333333C', '600333333', 58.00, 1.60, 'mantenerse',    'avanzado',     3, DATE_SUB(CURDATE(), INTERVAL 3 DAY)),  -- vencido
('Luis Fernandez','44444444D','600444444', 90.00, 1.75, 'bajar peso',    'intermedio',   4, DATE_ADD(CURDATE(), INTERVAL 200 DAY)), -- activo
('Diego Pereira',  '66666666F', '600666666', 81.00, 1.78, 'mantenerse',    'principiante', 2, DATE_ADD(CURDATE(), INTERVAL 15 DAY)),  -- activo
('Lucia Rodriguez','77777777G', '600777777', 91.00, 1.70, 'bajar peso',    'intermedio',   1, DATE_ADD(CURDATE(), INTERVAL 2 DAY)),   -- por vencer
('Valentina Diaz', '99999999I', '600999999', 52.00, 1.72, 'mantenerse',    'intermedio',   1, DATE_SUB(CURDATE(), INTERVAL 10 DAY)),  -- vencido
('Javier Gomez',   '10101010J', '601010101', 84.00, 1.82, 'bajar peso',    'avanzado',     2, DATE_ADD(CURDATE(), INTERVAL 25 DAY)),  -- activo
('Paula Sosa',     '12121212K', '601212121', 63.00, 1.68, 'mantenerse',    'principiante', 1, DATE_ADD(CURDATE(), INTERVAL 10 DAY)),  -- se cancela abajo
('Martin Silva',   '13131313L', '601313131', 79.00, 1.76, 'ganar musculo', 'principiante', 1, DATE_ADD(CURDATE(), INTERVAL 32 DAY));  -- congelado abajo

-- Paula canceló con 10 días sin usar
UPDATE socios SET fecha_cancelacion = DATE_SUB(CURDATE(), INTERVAL 5 DAY) WHERE id = 9;

-- Martin congeló 14 días hace 2 días: ya están sumados a su vencimiento
INSERT INTO congelamientos (socio_id, fecha_inicio, fecha_fin) VALUES
(10, DATE_SUB(CURDATE(), INTERVAL 2 DAY), DATE_ADD(CURDATE(), INTERVAL 12 DAY));

-- Ana renovó cuando le quedaban 5 días: 30 del plan + 5 restantes
INSERT INTO pagos (socio_id, plan_id, fecha, monto, dias_plan, dias_restantes, vencimiento_nuevo) VALUES
(1, 1, DATE_SUB(CURDATE(), INTERVAL 40 DAY),  1500.00, 30,  0, DATE_SUB(CURDATE(), INTERVAL 10 DAY)),
(1, 1, DATE_SUB(CURDATE(), INTERVAL 15 DAY),  1500.00, 30,  5, DATE_ADD(CURDATE(), INTERVAL 20 DAY)),
(2, 2, DATE_SUB(CURDATE(), INTERVAL 25 DAY),  1000.00, 30,  0, DATE_ADD(CURDATE(), INTERVAL 5 DAY)),
(3, 3, DATE_SUB(CURDATE(), INTERVAL 93 DAY),  4000.00, 90,  0, DATE_SUB(CURDATE(), INTERVAL 3 DAY)),
(4, 4, DATE_SUB(CURDATE(), INTERVAL 165 DAY), 14000.00, 365, 0, DATE_ADD(CURDATE(), INTERVAL 200 DAY)),
(5, 2, DATE_SUB(CURDATE(), INTERVAL 15 DAY),  1000.00, 30,  0, DATE_ADD(CURDATE(), INTERVAL 15 DAY)),
(6, 1, DATE_SUB(CURDATE(), INTERVAL 28 DAY),  1500.00, 30,  0, DATE_ADD(CURDATE(), INTERVAL 2 DAY)),
(7, 1, DATE_SUB(CURDATE(), INTERVAL 40 DAY),  1500.00, 30,  0, DATE_SUB(CURDATE(), INTERVAL 10 DAY)),
(8, 2, DATE_SUB(CURDATE(), INTERVAL 5 DAY),   1000.00, 30,  0, DATE_ADD(CURDATE(), INTERVAL 25 DAY)),
(9, 1, DATE_SUB(CURDATE(), INTERVAL 20 DAY),  1500.00, 30,  0, DATE_ADD(CURDATE(), INTERVAL 10 DAY)),
(10, 1, DATE_SUB(CURDATE(), INTERVAL 12 DAY), 1500.00, 30,  0, DATE_ADD(CURDATE(), INTERVAL 18 DAY));

INSERT INTO registros_peso (socio_id, fecha, peso) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 60 DAY), 72.00),
(1, DATE_SUB(CURDATE(), INTERVAL 30 DAY), 70.00),
(1, CURDATE(), 68.00),
(2, DATE_SUB(CURDATE(), INTERVAL 30 DAY), 74.00),
(2, CURDATE(), 75.50),
(3, CURDATE(), 58.00),
(4, DATE_SUB(CURDATE(), INTERVAL 30 DAY), 88.00),
(4, CURDATE(), 90.00),
(5, DATE_SUB(CURDATE(), INTERVAL 30 DAY), 80.00),
(5, CURDATE(), 81.00),
(6, DATE_SUB(CURDATE(), INTERVAL 45 DAY), 95.00),
(6, DATE_SUB(CURDATE(), INTERVAL 20 DAY), 93.00),
(6, CURDATE(), 91.00),
(7, DATE_SUB(CURDATE(), INTERVAL 40 DAY), 48.00),
(7, CURDATE(), 52.00),
(8, DATE_SUB(CURDATE(), INTERVAL 30 DAY), 86.00),
(8, CURDATE(), 84.00),
(9, DATE_SUB(CURDATE(), INTERVAL 20 DAY), 63.00),
(10, DATE_SUB(CURDATE(), INTERVAL 12 DAY), 79.00);

-- Carlos (plan 3 dias) ya entro 2 veces esta semana para poder probar el limite
INSERT INTO asistencias (socio_id, fecha_hora, rutina_id, dia_rutina) VALUES
(2, DATE_SUB(NOW(), INTERVAL 2 DAY), 5, 1),
(2, DATE_SUB(NOW(), INTERVAL 1 DAY), 5, 2),
-- Ana (rutina 1) lleva 8 entradas en 28 dias: con su cumplimiento se le sugiere subir de nivel
(1, DATE_SUB(NOW(), INTERVAL 22 DAY), 1, 1),
(1, DATE_SUB(NOW(), INTERVAL 19 DAY), 1, 2),
(1, DATE_SUB(NOW(), INTERVAL 16 DAY), 1, 3),
(1, DATE_SUB(NOW(), INTERVAL 13 DAY), 1, 1),
(1, DATE_SUB(NOW(), INTERVAL 10 DAY), 1, 2),
(1, DATE_SUB(NOW(), INTERVAL 7 DAY), 1, 3),
(1, DATE_SUB(NOW(), INTERVAL 4 DAY), 1, 1),
(1, DATE_SUB(NOW(), INTERVAL 1 DAY), 1, 2),
(5, DATE_SUB(NOW(), INTERVAL 2 DAY), 7, 1),
(6, DATE_SUB(NOW(), INTERVAL 4 DAY), 2, 1),
(7, DATE_SUB(NOW(), INTERVAL 15 DAY), 8, 1),
-- Javier (plan 3 dias) ya uso sus 3 dias de los ultimos 7: el check-in se rechaza
(8, DATE_SUB(NOW(), INTERVAL 5 DAY), 3, 1),
(8, DATE_SUB(NOW(), INTERVAL 3 DAY), 3, 2),
(8, DATE_SUB(NOW(), INTERVAL 1 DAY), 3, 3);

-- Ana hizo todos sus ejercicios. Carlos hizo todo el Dia 1 y solo uno del Dia 2.
-- Javier solo el Dia 1: se ve claro lo hecho y lo no hecho.
INSERT INTO ejercicios_realizados (asistencia_id, ejercicio_id)
SELECT a.id, e.id
FROM asistencias a
JOIN rutina_ejercicios e ON e.rutina_id = a.rutina_id AND e.dia = a.dia_rutina
WHERE a.socio_id = 1
   OR (a.socio_id = 2 AND (a.dia_rutina = 1 OR e.orden = 1))
   OR (a.socio_id = 8 AND a.dia_rutina = 1);


-- Ejemplos históricos de T4 (la migración no inventa auditoría del pasado).
-- Ana renovó con 5 días restantes; Martin congeló 14 días hace 2 días.
INSERT INTO auditoria_socios
    (socio_id, plan_anterior, plan_nuevo, vencimiento_anterior, vencimiento_nuevo, fecha_hora) VALUES
(1, 1, 1, DATE_SUB(CURDATE(), INTERVAL 10 DAY), DATE_ADD(CURDATE(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 15 DAY)),
(10, 1, 1, DATE_ADD(CURDATE(), INTERVAL 4 DAY), DATE_ADD(CURDATE(), INTERVAL 18 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY));
