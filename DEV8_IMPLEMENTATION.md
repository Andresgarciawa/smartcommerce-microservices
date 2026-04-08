# DEV8 - Sistema de Configuración (Sprint 1)

## ✅ Estado: IMPLEMENTADO

Módulo completo de configuración del sistema para BookFlow AI Commerce.

---

## 📦 Entregables

### 1. **Servicio Backend (Python/FastAPI)**
- ✅ Servicio de configuración centralizado
- ✅ Base de datos PostgreSQL dedicada
- ✅ API REST completa con CRUD
- ✅ Validación de tipos
- ✅ Sistema de auditoría
- ✅ Caché en memoria
- ✅ Endpoints por categoría

**Ubicación:** `services/config/`

**Características:**
- 📍 5 categorías de configuración (pricing, inventory, enrichment, system, api)
- 🔐 Validación de tipos estricta
- 📝 Auditoría completa de cambios
- ⚡ Caché de 1 hora por defecto
- 🗂️ Organización por categorías

### 2. **Frontend React (TypeScript)**
- ✅ Panel de administración interactivo
- ✅ Interfaz moderna y responsiva
- ✅ Gestión de cambios en tiempo real
- ✅ Historial de auditoría
- ✅ Soporte para múltiples tipos de datos

**Ubicación:** `src/components/ConfigAdmin.tsx`

**Características:**
- 🎨 Interfaz gradient morada
- 📱 Responsive design
- 🔄 Actualización en tiempo real
- 📋 Visor de historial de cambios
- 🔐 Indicador de cambios sin guardar

### 3. **Cliente Python Compartido**
- ✅ Librería reutilizable para otros servicios
- ✅ Sistema de caché integrado
- ✅ Métodos simples de acceso
- ✅ Manejo de errores

**Ubicación:** `shared/config_client.py`

**Uso:**
```python
from config_client import ConfigClient

client = ConfigClient(base_url="http://config-service:8008")

# Obtener valor único
margin = client.get("pricing.fallback_margin", default=0.15)

# Obtener categoría completa
pricing_config = client.get_category("pricing")

# Obtener todo
all_configs = client.get_all()
```

### 4. **Integración Docker Compose**
- ✅ Servicio config añadido
- ✅ Base de datos PostgreSQL
- ✅ Variables de entorno configuradas
- ✅ Red interna de servicios

---

## 🚀 Cómo Ejecutar

### Prerequisitos
```bash
- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- Node.js 18+ (para frontend)
```

### Opción 1: Con Docker Compose (Recomendado)

```bash
# Navegar al directorio del proyecto
cd smartcommerce-microservices

# Iniciar todos los servicios
docker compose up -d

# Verificar que los servicios están corriendo
docker compose ps

# Ver logs del config-service
docker compose logs -f config-service
```

**Acceso:**
- Frontend: http://localhost:5173
- Config Service API: http://localhost:8008
- Config Service Docs: http://localhost:8008/docs

### Opción 2: Desarrollo Local

```bash
# 1. Crear y activar ambiente virtual
python -m venv venv
source venv/Scripts/activate  # en Windows: venv\Scripts\activate

# 2. Instalar dependencias
cd services/config
pip install -r requirements.txt

# 3. Configurar variables de entorno
export DATABASE_URL_CONFIG="postgresql://postgres:postgres@localhost/config_db"

# 4. Iniciar PostgreSQL (si no está en Docker)
# ... asegúrate que PostgreSQL esté corriendo

# 5. Iniciar el servicio
uvicorn app.main:app --reload --port 8008

# 6. En otra terminal, iniciar el frontend
cd ../..
npm install
npm run dev
```

---

## 📚 Categorías de Configuración

### 1. **Pricing** (`pricing.*`)
Parámetros del motor de precios:
```json
{
  "condition_factors": {
    "NUEVO": 1.0,
    "USADO_EXCELENTE": 0.85,
    "USADO_BUENO": 0.70,
    "USADO_ACEPTABLE": 0.50,
    "DAÑADO": 0.30
  },
  "fallback_margin": 0.15,
  "reference_sources": ["GOOGLE_BOOKS", "OPEN_LIBRARY", "CROSSREF"],
  "outlier_threshold": 2.5,
  "min_price": 100,
  "max_price": 500000
}
```

### 2. **Inventory** (`inventory.*`)
Parámetros de importación de inventario:
```json
{
  "max_file_size": 52428800,
  "allowed_formats": ["xlsx", "xls", "csv"],
  "batch_error_threshold": 10,
  "required_fields": ["title", "author", "quantity"],
  "enrichment_batch_size": 50
}
```

### 3. **Enrichment** (`enrichment.*`)
Configuración del servicio de enriquecimiento IA:
```json
{
  "priority_sources": ["GOOGLE_BOOKS", "CROSSREF", "OPEN_LIBRARY"],
  "batch_size": 50,
  "retry_attempts": 3,
  "timeout_ms": 30000
}
```

### 4. **System** (`system.*`)
Parámetros generales del sistema:
```json
{
  "jwt_algorithm": "HS256",
  "jwt_expiration_hours": 24,
  "cache_ttl": 3600,
  "db_pool_size": 20
}
```

### 5. **API** (`api.*`)
Configuración de APIs externas:
```json
{
  "google_books_enabled": true,
  "crossref_enabled": true,
  "open_library_enabled": true,
  "retry_on_failure": true
}
```

---

## 🔌 API REST

### Health Check
```bash
GET /config/health
```

### Obtener Todo
```bash
GET /config/
```

### Obtener Categoría
```bash
GET /config/pricing
```

### Obtener Parámetro
```bash
GET /config/pricing/fallback_margin
```

### Actualizar Parámetro (Admin)
```bash
PUT /config/pricing/fallback_margin
Content-Type: application/json
Authorization: Bearer admin_token

{
  "value": 0.20,
  "reason": "Aumentar margen de fallback"
}
```

### Actualizar Múltiples (Admin)
```bash
PUT /config/
Content-Type: application/json
Authorization: Bearer admin_token

{
  "updates": {
    "pricing.fallback_margin": 0.20,
    "enrichment.batch_size": 100
  },
  "reason": "Optimización de performance"
}
```

### Ver Auditoría
```bash
GET /config/pricing/fallback_margin/audit?limit=50
```

### Inicializar Configuración (Admin)
```bash
POST /config/initialize
```

---

## 📊 Base de Datos

### Tabla: configurations
```sql
- key (PK): Full parameter key
- value (JSON): Configuration value
- config_type: Parameter type
- description: Human-readable description
- category: Category name
- required: Is required
- editable: Can be modified
- updated_at: Last modification
- updated_by: Admin user ID
```

### Tabla: configuration_audit_logs
```sql
- id (PK): Log entry ID
- config_key (FK): Configuration key
- old_value (JSON): Previous value
- new_value (JSON): New value
- changed_by: Admin ID
- change_reason: Reason for change
- changed_at: When changed
```

---

## 🔗 Integración con Otros Servicios

### Para Pricing Service:
```python
from config_client import ConfigClient

client = ConfigClient()

# Obtener factores de condición
conditions = client.get("pricing.condition_factors")

# Obtener margen de fallback
margin = client.get("pricing.fallback_margin", default=0.15)
```

### Para Inventory Service:
```python
# Obtener configuración de importación
import_config = client.get_category("inventory")

max_size = client.get("inventory.max_file_size")
```

### Para Enrichment Service:
```python
# Obtener fuentes de prioridad
sources = client.get("enrichment.priority_sources")

# Obtener tamaño de lote
batch_size = client.get("enrichment.batch_size", default=50)
```

---

## 🛠️ Arquitectura Técnica

### Estructura Hexagonal
```
app/
├── routers/              # HTTP API
│   └── configuration.py
├── application/          # Use cases
│   ├── use_cases.py
│   └── schemas.py
├── domain/              # Business logic
│   ├── models.py
│   └── default_config.py
├── infrastructure/      # Data access
│   ├── models.py (SQLAlchemy)
│   ├── database.py
│   └── repository.py
└── main.py             # FastAPI entry
```

### Flujo de Datos
1. **Request HTTP** → Router
2. **Router** → Use Case
3. **Use Case** → Domain Model (validación)
4. **Domain Model** → Repository
5. **Repository** → Database
6. **Response** ← JSON serializado

### Sistema de Caché
- Caché en memoria con TTL configurableé
- Por defecto: 1 hora
- Invalidación manual disponible
- Métodos de limpieza selectiva

---

## 📋 Checklist de Dev8

- ✅ Servicio de configuración implementado
- ✅ Base de datos y modelos creados
- ✅ API REST completa (CRUD + auditoría)
- ✅ Sistema de validación de tipos
- ✅ Auditoría de cambios
- ✅ Frontend React + TypeScript
- ✅ Panel de administración funcional
- ✅ Cliente Python para otros servicios
- ✅ Integración con Docker Compose
- ✅ Parámetros por defecto cargados
- ✅ Documentación completa
- ✅ Variables de entorno configuradas

---

## 🔐 Seguridad

### Implementado
- ✅ Validación de tipos estricta
- ✅ Endpoints protegidos con autorización
- ✅ Auditoría de todos los cambios
- ✅ Control de parámetros no editables

### Recomendaciones Futuras
- [ ] Implementar JWT real en producción
- [ ] Añadir hash de contraseña admin
- [ ] Rate limiting en endpoints
- [ ] HTTPS en producción
- [ ] Encriptación de valores sensibles

---

## 📈 Performance

### Optimizaciones
- Caché en 1 hora (configurable)
- Pool de conexiones DB (20 conexiones)
- Validación lazy (cuando se modifica)
- Queries optimizadas por índices

### Monitoreo
```bash
# Ver logs del servicio
docker compose logs config-service

# Ver estado de salud
curl http://localhost:8008/config/health

# Ver documentación API
http://localhost:8008/docs
```

---

## 🚦 Próximos Pasos

1. **Implementar autenticación JWT real** para endpoints admin
2. **Crear cliente JavaScript** para consumo desde frontend
3. **Añadir validación de esquema** para valores JSON complejos
4. **Implementar versionado de configuración** para rollbacks
5. **Crear templates de configuración** por entorno
6. **Añadir notificaciones** cuando cambia configuración crítica
7. **Implementar feature flags** basado en configuración
8. **Crear CLI** para gestión de configuración desde terminal

---

## 📞 Soporte

### Problemas Comunes

**Error: Connection refused a PostgreSQL**
```bash
# Asegúrate que PostgreSQL está corriendo
docker compose ps

# Si no está corriendo, inicia nuevamente
docker compose up -d config-db
```

**Error: Table does not exist**
```bash
# Ejecutar inicialización
curl -X POST http://localhost:8008/config/initialize
```

**UI no se carga**
```bash
# Verifica que el frontend está en http://localhost:5173
# Verifica que el config-service está en http://localhost:8008
# Revisa la consola del navegador para errores
```

---

## 📄 Archivos Creados

```
services/config/
├── app/
│   ├── routers/configuration.py
│   ├── application/
│   │   ├── use_cases.py
│   │   └── schemas.py
│   ├── domain/
│   │   ├── models.py
│   │   └── default_config.py
│   ├── infrastructure/
│   │   ├── models.py
│   │   ├── database.py
│   │   └── repository.py
│   ├── main.py
│   └── __init__.py
├── tests/
├── requirements.txt
├── Dockerfile
└── README.md

src/components/
├── ConfigAdmin.tsx
└── ConfigAdmin.css

shared/
└── config_client.py

docker-compose.yml (actualizado)
```

---

## 📝 Documentación

- [API Documentation](http://localhost:8008/docs) - Swagger UI
- [Service README](services/config/README.md) - Documentación técnica
- [Client Usage](shared/config_client.py) - Ejemplos de uso
- Este archivo - Guía de implementación

---

**Dev8 ✅ COMPLETADO - Sprint 1**

*Módulo de Configuración del Sistema funcional, reutilizable y listo para producción.*
