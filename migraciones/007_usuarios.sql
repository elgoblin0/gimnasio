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
('Administrador', 'admin', 'pbkdf2:sha256:1000000$79aXwzeXFi883svR$9a185357f81721df53cab79860b2a60537548e43578e791275ca760612316c18', 'admin'),
('Recepción', 'recepcion', 'pbkdf2:sha256:1000000$HDhysvAH8vT1Tw2a$85f539f7b95f5e75f6c2fa223ba99e76baef0ee796f9fa5f1b4373bcd0e9c7d4', 'recepcion');
