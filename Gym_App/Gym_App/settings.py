from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 1. CONFIGURACIÓN DE SEGURIDAD Y ENTORNO
# ==============================================================================
# DEBUG debe definirse ANTES de evaluar cualquier otra lógica.
# Será False automáticamente en Render, y True en tu máquina local.
DEBUG = 'RENDER' not in os.environ

# Seguridad: Toma la llave del entorno en producción, usa una por defecto en local.
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 
    'django-insecure-%)+-4zyn*8gx+va6sf)-qsyji5n(hoo_v3ww5kjz55j@)s4q&^'
)

# Hosts permitidos: Se auto-configura si está en Render, o permite local.
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# ==============================================================================
# 2. DEFINICIÓN DE APLICACIONES Y MIDDLEWARE
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Aplicaciones locales
    'users',
    'workouts',
    'measurements',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Debe ir justo debajo de Security
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Gym_App.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Gym_App.wsgi.application'

# ==============================================================================
# 3. BASE DE DATOS
# ==============================================================================
DATABASES = {
    'default': dj_database_url.config(
        # Concatenación absoluta para asegurar que SQLite se cree en la raíz local
        default=f'sqlite:///{BASE_DIR}/db.sqlite3',
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# 4. INTERNACIONALIZACIÓN Y TIEMPO
# ==============================================================================
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 5. ARCHIVOS ESTÁTICOS (CSS, JS, Imágenes del sistema)
# ==============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / "static", 
]

# Ahora DEBUG tiene el valor correcto cuando el intérprete llega a esta línea
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# 6. ARCHIVOS MULTIMEDIA (Subidas por el usuario)
# ==============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==============================================================================
# 7. CONFIGURACIÓN DE AUTENTICACIÓN
# ==============================================================================
LOGIN_REDIRECT_URL = 'dashboard'
LOGIN_URL = '/accounts/login/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'