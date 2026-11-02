# Versión estándar

## Objetivo
Conservar el proyecto de facultad sencillo de ejecutar y explicar. Mantener Flask, MySQL/MariaDB y JavaScript sin framework de frontend.

## Preparación completada
- [x] Guardar el estado inicial con la etiqueta `base-original`.
- [x] Separar la versión Pro en su propio repositorio, conservando el historial.

## Mejoras
Las funciones pedidas por el profesor están definidas en `SPEC.md`, divididas en tickets. Los tickets T1 a T10 ya están fusionados en `main`.

- [x] Validar números, campos vacíos y valores permitidos; devolver errores comprensibles (T1).
- [x] Confirmar o cancelar juntas las escrituras de alta, eliminación y registro de peso (T1).
- [x] Revisar entradas simultáneas para evitar check-ins duplicados (T1).
- [x] Probar las reglas de vencimiento, renovación y asistencia en sus casos límite (T1).
- [x] Mejorar formularios, mensajes y presentación en celulares (rediseño Hierro, PR #23).

## Límites
No incorporar cobros reales, IA, múltiples sedes ni una reescritura del stack en esta versión. Registrar pagos sí está permitido (ver `SPEC.md`). Se mantiene el acuerdo del grupo indicado en el README antes de cambiar código.

## Trabajo compartido
Revisar cada corrección aplicable a Pro y trasladarla mediante un commit específico o una adaptación. No fusionar las ramas principales completas entre repositorios cuando sus arquitecturas diverjan.
