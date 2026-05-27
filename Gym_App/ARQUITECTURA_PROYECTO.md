# Arquitectura del proyecto Gym App (resumen)

## 1) Vista general
Aplicación web Django para gestión de rutinas y registro de sesiones de entrenamiento.

Capas principales:
- Backend Django (modelos, vistas, formularios, rutas, autenticación)
- Frontend server-rendered con templates Django
- Estilos y comportamiento en archivos static (CSS y JavaScript)
- Base de datos relacional (SQLite local y PostgreSQL en despliegue vía URL)

## 2) Stack tecnológico
Dependencias principales:
- Django 6.0.3
- dj-database-url
- psycopg2-binary
- gunicorn
- whitenoise
- asgiref, sqlparse, tzdata, packaging

Configuración clave:
- Idioma: es-co
- Zona horaria: America/Bogota
- Archivos estáticos: static + staticfiles con WhiteNoise en producción
- Archivos media: carpeta media
- Autenticación: rutas nativas de Django en /accounts/

## 3) Arquitectura backend
### 3.1 Apps
- Gym_App (configuración global)
- workouts (núcleo de negocio)
- users (dashboard y capa de usuario)
- measurements (estructura creada, sin lógica funcional relevante aún)

### 3.2 Enrutamiento
Rutas globales:
- /admin/
- /accounts/ (login/logout/password views de Django)
- / (dashboard)
- /workouts/...

Rutas de workouts:
- /workouts/routines/
- /workouts/routines/create/
- /workouts/routines/edit/<id>/
- /workouts/routines/delete/<id>/
- /workouts/records/
- /workouts/records/add/
- /workouts/api/search-exercises/
- /workouts/api/create-exercise/

### 3.3 Modelos de datos (workouts)
Taxonomía y catálogo global:
- MovementPattern: patrón de movimiento (Push, Pull, Piernas, etc.)
- MuscleGroup: grupo muscular, ligado a MovementPattern
- Exercise: catálogo global de ejercicios
  - Atributos importantes: nombre, grupo muscular, imagen URL, tipo de ejercicio, tracks_weight, activo
  - Regla automática: el tipo de ejercicio se sincroniza según grupo muscular

Plantillas de usuario:
- Routine: rutina del usuario, con opción pública
- RoutineItem: ejercicio dentro de rutina, series/repeticiones recomendadas y orden

Datos transaccionales (registro histórico):
- WorkoutSession: sesión de entrenamiento (inicio, fin, notas)
- SessionExerciseEntry: ejercicio ejecutado en una sesión
  - Fase: calentamiento, principal, cardio final
  - Tipo: fuerza, cardio, cuerpo completo
- StrengthSetEntry: series de fuerza (reps, peso, unidad)
- CardioEntry: duración y distancia (km o steps)
- FullBodyEntry: distintos modos de seguimiento

### 3.4 Funciones principales del backend
Funciones destacadas en la lógica de workouts:
- create_routine_view y edit_routine_view: creación/edición de rutina
- search_exercises_api y create_exercise_api: búsqueda y alta asíncrona de ejercicios
- routines_view y delete_routine_view: listado y eliminación de rutinas
- records_view: historial de sesiones
- add_record_view: guardado completo de sesión con validaciones y persistencia transaccional
- workout_sessions_list y _build_session_detail_payload: construcción de payload de sesiones para dashboard y records

Utilidades internas relevantes:
- normalización de texto
- inferencia de tipo de ejercicio por grupo muscular
- validación de payload JSON para bloques de cardio y cuerpo completo
- formateo de duración para UI

### 3.5 Formularios
- RoutineForm: nombre y visibilidad de rutina
- ExerciseAsyncForm: creación de ejercicio, validación de duplicado por nombre

## 4) Arquitectura frontend
### 4.1 Templates
Base:
- templates/base.html: layout principal, navbar, footer, carga de fuentes y css/js base

Pantallas principales:
- templates/dashboard.html
- templates/registration/login.html
- templates/workouts/routines.html
- templates/workouts/create_routine.html
- templates/workouts/records.html
- templates/workouts/add_record.html
- templates/workouts/modal_view_routine.html
- templates/workouts/modal_view_session.html

### 4.2 JavaScript principal
- static/js/base.js
  - resaltado de ruta activa en navegación
  - manejo de menú móvil
  - manejo de submenús con atributos aria

- static/js/workouts/create_routine.js
  - búsqueda de ejercicios
  - inferencia de tipo desde grupo muscular
  - adición/eliminación dinámica de ejercicios de rutina
  - envío asíncrono para crear ejercicio

- static/js/workouts/add_record.js
  - lógica compleja del formulario de sesión
  - manejo de fases (calentamiento, principal, cardio final)
  - validaciones cliente
  - borrador local y restauración
  - serialización JSON para backend

- static/js/workouts/records.js y modal_view_routine.js
  - render y apertura/cierre de modales
  - gestión de contenido visual en listados y detalles

### 4.3 Estilos CSS
Base:
- static/css/base.css
- static/css/dashboard.css
- static/css/login.css

Módulo workouts:
- static/css/workouts/routines.css
- static/css/workouts/create_routine.css
- static/css/workouts/add_record.css
- static/css/workouts/records.css
- static/css/workouts/modal_view_routine.css

## 5) Sistema visual (tipografías, colores y UI)
### 5.1 Tipografías
Fuentes cargadas desde Google Fonts:
- Kanit (display, títulos)
- Inter (texto general)

Variables CSS:
- --font-display: Kanit
- --font-main: Inter

### 5.2 Paleta de colores (variables globales)
Colores base definidos en static/css/base.css:
- Fondo principal: #010409
- Fondo secundario: #0d1117
- Azul soporte: #121d2f
- Verde acción/éxito: #238636
- Texto principal: #f0f6fc
- Texto secundario: #656c76
- Enlaces: #4493f8
- Advertencia: #d84a3f
- Acento menta: #B0E4CC

Dirección visual:
- Tema oscuro predominante
- Botones con variantes de acción, peligro y éxito
- Sombras y bordes suaves
- Tipografía en mayúsculas para encabezados

### 5.3 Responsividad y navegación
- Breakpoints en varios CSS (por ejemplo 1050, 850, 700, 650, 600 px)
- Navbar desktop + menú móvil desplegable
- Submenús de Rutinas y Registros con estados aria para accesibilidad

## 6) Flujo general frontend-backend
1. El usuario navega por templates renderizados por Django.
2. Formularios tradicionales y payloads JSON conviven según el caso.
3. Endpoints API de workouts atienden búsqueda/creación asíncrona de ejercicios.
4. add_record serializa bloques complejos (fuerza/cardio/full body) y backend valida y guarda dentro de transacción.
5. Dashboard y Records leen payload consolidado de sesiones para mostrar métricas y detalle.

## 7) Estado actual del dominio
- Núcleo funcional completo en workouts.
- users aporta dashboard y autenticación integrada con Django.
- measurements está disponible como app base, pero sin modelos/vistas de negocio desarrollados.

---
Documento resumido generado desde el estado actual del código fuente del proyecto.
