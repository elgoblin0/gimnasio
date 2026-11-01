-- =============================================
-- Migración 007: usuarios para el login
-- Para quien ya tiene la base creada con la versión anterior.
-- Conserva todos los datos.
-- Crea dos usuarios de ejemplo, con las claves de prueba indicadas en el README.
-- Se puede importar en phpMyAdmin (pestaña Importar) o correr con el cliente mysql.
-- Es segura de repetir: lo que ya existe no se vuelve a crear.
-- =============================================

USE gimnasio;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    clave_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL,
    activo TINYINT(1) NOT NULL DEFAULT 1
);

INSERT IGNORE INTO usuarios (nombre, usuario, clave_hash, rol) VALUES
('Administrador', 'admin', 'scrypt:32768:8:1$I2iosHuGMSOnvFl2$40495a77ec78854a5888ea54784fcb19a3fd4d90f1eeee63cc22c85a3a305d8fbde8196b283b2fcd2a058a3d244db6d28df48e9c048a4b1fb97cbafd0e8060ad', 'admin'),
('Recepción', 'recepcion', 'scrypt:32768:8:1$hbjtRoBZQnMGhguF$f3eb7e6aea797359965f263fa890f106b220eb3af7b2d7eb27b243cea8652809e94c979b1957473ec23b7bba3e8649cb86a86e68bef356ae3bec17538a2f0b14', 'recepcion');
