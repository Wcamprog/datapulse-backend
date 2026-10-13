# DataPulse Latam - Backend (Django REST Framework)

Este repositorio contiene la API REST y la lógica de negocio (Backend) para la plataforma DataPulse Latam. Está construido con Django y Django REST Framework, e incluye un servicio automatizado para el cálculo del Índice de Riesgo País Compuesto (IRPC).

## 🚀 Tecnologías Principales
* Python 3.11+
* Django 4.2+
* Django REST Framework (DRF)
* PostgreSQL
* Docker & Docker Compose
* JWT (JSON Web Tokens) para autenticación

---

## 🛠️ Despliegue en Entorno Local (Desarrollo)

Para levantar este proyecto en tu máquina local, utilizaremos Docker para simplificar la configuración de la base de datos y las dependencias.

### Requisitos previos
* Tener instalado [Docker Desktop](https://www.docker.com/products/docker-desktop/) o Docker Engine.

### Paso 1: Configurar las variables de entorno
Crea un archivo llamado `.env` en la raíz del proyecto (al mismo nivel que `manage.py` y `docker-compose.yml`). Copia el siguiente contenido base (no uses contraseñas reales de producción aquí):

```env
DEBUG=True
SECRET_KEY=django-insecure-clave-local-de-prueba
DATABASE_URL=postgres://datapulse_user:datapulse_password@db:5432/datapulse_db
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

### Paso 2: Construir y levantar los contenedores
Abre tu terminal en la raíz del proyecto y ejecuta el siguiente comando para construir la imagen e iniciar los servicios (Base de datos y Servidor Web):

```bash
docker-compose up -d --build
```

### Paso 3: Aplicar migraciones
Una vez que los contenedores estén corriendo, aplica las migraciones para crear las tablas en la base de datos de PostgreSQL:

```bash
docker-compose exec web python manage.py migrate
```

### Paso 4: Crear el usuario administrador
Crea un superusuario para poder acceder al panel de administración y a los endpoints que requieren rol de ADMIN:

```bash
docker-compose exec web python manage.py createsuperuser
```

**¡Listo!** Tu API estará disponible en: `http://localhost:8000/api/`
Puedes ver la documentación interactiva de Swagger en: `http://localhost:8000/api/docs/`

---

## 🌍 Despliegue en Producción

Para desplegar este backend en un entorno productivo (ej. Render, Railway, AWS, DigitalOcean), debes tener en cuenta las siguientes configuraciones de seguridad:

1. **Variables de Entorno Estrictas:**
   * `DEBUG=False` (CRÍTICO: Nunca dejes esto en True en producción).
   * `SECRET_KEY`: Genera una clave alfanumérica larga y aleatoria. Nunca la subas al repositorio.
   * `ALLOWED_HOSTS`: Agrega únicamente el dominio público de tu API (ej. `api.midominio.com`).
   * `CORS_ALLOWED_ORIGINS`: Agrega únicamente la URL donde esté alojado tu frontend (ej. `https://midominio.com`).
   * `DATABASE_URL`: La cadena de conexión real a tu base de datos gestionada en la nube.

2. **Servidor de Aplicaciones (WSGI):**
   El proyecto utiliza `gunicorn` para entornos productivos. El comando de inicio que debes configurar en tu servidor es:
   ```bash
   gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
   ```

3. **Archivos Estáticos:**
   Si tu plataforma no gestiona los estáticos automáticamente, asegúrate de correr en tu pipeline de despliegue:
   ```bash
   python manage.py collectstatic --noinput
   ```