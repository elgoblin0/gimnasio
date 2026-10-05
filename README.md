# Sistema de gimnasio

Proyecto de la facultad: gestión de socios de un gimnasio.

**Stack:** XAMPP (MySQL/MariaDB) + Python Flask (backend) + JavaScript (frontend).

## Reglas del proyecto

1. Siempre lo más sencillo posible, para poder explicar el código al profesor.
2. Antes de escribir código, todo el grupo tiene que estar 100% de acuerdo.

## Cómo ponerlo en marcha

1. Instalar **XAMPP** y arrancar **MySQL** (y **Apache** para usar phpMyAdmin).
2. Abrir `http://localhost/phpmyadmin`, pestaña **Importar**, y subir `base_datos.sql`.
   (Ojo: borra y vuelve a crear la base de datos `gimnasio` con los datos de ejemplo.)
3. Instalar las librerías de Python:
   ```
   pip3 install -r requirements.txt
   ```
4. Arrancar el servidor:
   ```
   python3 app.py
   ```
5. Abrir `http://localhost:5001` en el navegador.

> En Windows puede que los comandos sean `pip` y `python` en vez de `pip3` y `python3`.

## Archivos

```
gimnasio/
├── base_datos.sql   ← tablas y datos de ejemplo
├── app.py           ← backend Flask: reglas + API
└── static/
    ├── index.html   ← lista de socios, check-in y alta
    ├── socio.html   ← ficha: IMC, rutina, progreso, renovar
    ├── app.js       ← llamadas a la API (fetch)
    └── estilos.css
```

## Reglas del gimnasio (la lógica que se evalúa)

Todas están en `app.py`.

| # | Regla |
|---|---|
| 1 | Al dar de alta o renovar se calcula el vencimiento. Si sigue activo, se suma a lo que le queda; si no, desde hoy. |
| 2 | Estado del socio: Vencido / Por vencer (7 días o menos) / Activo. |
| 3 | Check-in: se rechaza si el plan está vencido, si ya entró hoy o si ya usó sus días por semana (últimos 7 días). |
| 4 | IMC = peso / altura², con su categoría. |
| 5 | Rutina asignada según objetivo + nivel. |
| 6 | Progreso: primer peso vs último según el objetivo (mantenerse = 2 kg o menos de diferencia). |

## Comandos básicos de git

```
git pull                      # traer los cambios de los compañeros (¡siempre antes de empezar!)
git add .                     # preparar mis cambios
git commit -m "qué he hecho"  # guardarlos con un mensaje
git push                      # subirlos a GitHub
```
