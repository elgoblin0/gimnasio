-- =============================================
-- Migración 010: claves de ejemplo que funcionan en cualquier Python
-- Para quien ya tiene la base creada con la versión anterior.
-- Las claves de ejemplo estaban guardadas con scrypt, que no existe en el Python
-- que trae la Mac: el login fallaba. Se cambian por pbkdf2 (las mismas claves).
-- Solo toca a admin y recepcion si todavía tienen la clave de ejemplo original.
-- Se puede importar en phpMyAdmin (pestaña Importar) o correr con el cliente mysql.
-- Es segura de repetir: si ya se cambió, no hace nada.
-- =============================================

USE gimnasio;

UPDATE usuarios
SET clave_hash = 'pbkdf2:sha256:1000000$79aXwzeXFi883svR$9a185357f81721df53cab79860b2a60537548e43578e791275ca760612316c18'
WHERE usuario = 'admin'
  AND clave_hash = 'scrypt:32768:8:1$I2iosHuGMSOnvFl2$40495a77ec78854a5888ea54784fcb19a3fd4d90f1eeee63cc22c85a3a305d8fbde8196b283b2fcd2a058a3d244db6d28df48e9c048a4b1fb97cbafd0e8060ad';

UPDATE usuarios
SET clave_hash = 'pbkdf2:sha256:1000000$HDhysvAH8vT1Tw2a$85f539f7b95f5e75f6c2fa223ba99e76baef0ee796f9fa5f1b4373bcd0e9c7d4'
WHERE usuario = 'recepcion'
  AND clave_hash = 'scrypt:32768:8:1$hbjtRoBZQnMGhguF$f3eb7e6aea797359965f263fa890f106b220eb3af7b2d7eb27b243cea8652809e94c979b1957473ec23b7bba3e8649cb86a86e68bef356ae3bec17538a2f0b14';
