-- =============================================
-- Base de datos del sistema de gimnasio
-- Importar en phpMyAdmin (XAMPP)
-- =============================================

DROP DATABASE IF EXISTS gimnasio;
CREATE DATABASE gimnasio;
USE gimnasio;

-- ---------------------------------------------
-- PLANES
-- duracion_dias: cuántos días dura el plan
-- dias_por_semana: cuántas veces puede entrar por semana (7 = libre)
-- ---------------------------------------------
CREATE TABLE planes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    duracion_dias INT NOT NULL,
    dias_por_semana INT NOT NULL
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
-- SOCIOS
-- peso: peso actual en kg
-- altura: en metros (ej: 1.75)
-- ---------------------------------------------
CREATE TABLE socios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    dni VARCHAR(20) NOT NULL UNIQUE,
    telefono VARCHAR(20),
    peso DECIMAL(5,2) NOT NULL,
    altura DECIMAL(3,2) NOT NULL,
    objetivo VARCHAR(20) NOT NULL,
    nivel VARCHAR(20) NOT NULL,
    plan_id INT NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES planes(id)
);

-- ---------------------------------------------
-- ASISTENCIAS
-- Una fila por cada vez que un socio entra al gimnasio
-- ---------------------------------------------
CREATE TABLE asistencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    socio_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    FOREIGN KEY (socio_id) REFERENCES socios(id)
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


-- =============================================
-- DATOS DE EJEMPLO
-- =============================================

INSERT INTO planes (nombre, duracion_dias, dias_por_semana) VALUES
('Mensual libre', 30, 7),
('Mensual 3 dias', 30, 3),
('Trimestral', 90, 7),
('Anual', 365, 7);

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

-- Fechas relativas a hoy para que siempre haya socios en cada estado
INSERT INTO socios (nombre, dni, telefono, peso, altura, objetivo, nivel, plan_id, fecha_vencimiento) VALUES
('Ana Lopez',    '11111111A', '600111111', 68.00, 1.65, 'bajar peso',    'principiante', 1, DATE_ADD(CURDATE(), INTERVAL 20 DAY)), -- activo
('Carlos Ruiz',  '22222222B', '600222222', 75.50, 1.80, 'ganar musculo', 'intermedio',   2, DATE_ADD(CURDATE(), INTERVAL 5 DAY)),  -- por vencer
('Maria Gomez',  '33333333C', '600333333', 58.00, 1.60, 'mantenerse',    'avanzado',     3, DATE_SUB(CURDATE(), INTERVAL 3 DAY)),  -- vencido
('Luis Fernandez','44444444D','600444444', 90.00, 1.75, 'bajar peso',    'intermedio',   4, DATE_ADD(CURDATE(), INTERVAL 200 DAY)); -- activo

INSERT INTO registros_peso (socio_id, fecha, peso) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 60 DAY), 72.00),
(1, DATE_SUB(CURDATE(), INTERVAL 30 DAY), 70.00),
(1, CURDATE(), 68.00),
(2, DATE_SUB(CURDATE(), INTERVAL 30 DAY), 74.00),
(2, CURDATE(), 75.50),
(3, CURDATE(), 58.00),
(4, DATE_SUB(CURDATE(), INTERVAL 30 DAY), 88.00),
(4, CURDATE(), 90.00);

-- Carlos (plan 3 dias) ya entro 2 veces esta semana para poder probar el limite
INSERT INTO asistencias (socio_id, fecha_hora) VALUES
(1, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(2, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(2, DATE_SUB(NOW(), INTERVAL 2 DAY));
