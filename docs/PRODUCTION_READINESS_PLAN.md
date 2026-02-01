# Plan de Preparación para Producción - v1.0.0

**Fecha:** 29 Enero 2026
**Plataforma:** Xcapit FHE-ML Platform
**Objetivo:** Release pre-productivo final

---

## Resumen Ejecutivo

| Componente | Estado Actual | Objetivo | Esfuerzo Estimado |
|------------|---------------|----------|-------------------|
| **Backend Django** | 90% ✅ | 100% | ~8 horas |
| **Frontend React** | 65% ⚠️ | 100% | ~40 horas |
| **SDK** | 95% ✅ | 100% | ~4 horas |
| **Documentación** | 85% ✅ | 100% | ~4 horas |

---

## BACKEND DJANGO - Estado: EXCELENTE ✅

### Lo que ya está bien implementado:
- ✅ Django 5.2 LTS (soporte hasta Abril 2028)
- ✅ DEBUG deshabilitado por defecto en producción
- ✅ SECRET_KEY desde variables de entorno (mínimo 50 chars)
- ✅ ALLOWED_HOSTS validado (sin wildcards)
- ✅ CSRF/Session cookies con Secure, HttpOnly, SameSite
- ✅ HTTPS forzado con HSTS (1 año)
- ✅ Protección XSS, Clickjacking, Content-Type sniffing
- ✅ JWT con rotación de tokens y blacklist
- ✅ Contraseñas: mínimo 12 caracteres + validadores
- ✅ Rate limiting: 100/hora anon, 1000/hora users
- ✅ Protección brute-force: django-axes (5 intentos, 30 min lockout)
- ✅ API Keys hasheadas (SHA256)
- ✅ PostgreSQL obligatorio en producción
- ✅ Docker con usuario non-root
- ✅ Gunicorn optimizado (4 workers, 2 threads)
- ✅ Health checks configurados
- ✅ Sentry integrado
- ✅ Logging estructurado JSON
- ✅ Audit logging completo
- ✅ Scripts de validación pre-deploy

### Acciones Pendientes Backend:

#### CRÍTICO (Antes de producción)
- [ ] Ejecutar `python scripts/validate_env.py --strict`
- [ ] Ejecutar `python scripts/verify_production.py`
- [ ] Generar SECRET_KEY fuerte: `openssl rand -hex 32`
- [ ] Configurar SENTRY_DSN en producción

#### ALTA PRIORIDAD
- [ ] Remover localhost de CORS_ALLOWED_ORIGINS en producción
- [ ] Configurar email backend (SendGrid recomendado)
- [ ] Verificar que DATABASE_URL use PostgreSQL 15+

#### MEDIA PRIORIDAD
- [ ] Configurar backups automáticos de base de datos
- [ ] Implementar CI/CD pipeline con tests
- [ ] Configurar alertas de Sentry

---

## FRONTEND REACT - Estado: REQUIERE ATENCIÓN ⚠️

### Problemas CRÍTICOS a resolver:

#### 1. API Key Hardcodeada en Código Fuente ❌
**Ubicación:** `src/context/DemoContext.jsx`, `src/api/client.js`
```javascript
// PROBLEMA: Key visible en el código
const DEMO_API_KEY = 'demo_xcapit_2024_public_access';
```

**Solución:**
```javascript
// Usar variable de entorno
const DEMO_API_KEY = import.meta.env.VITE_DEMO_API_KEY;
```

#### 2. Tokens en localStorage (Vulnerable a XSS) ❌
**Ubicación:** Múltiples archivos (`client.js`, `sandbox.js`, etc.)
```javascript
// PROBLEMA: XSS puede robar tokens
localStorage.setItem('xcapit_api_key', key);
```

**Solución:** Migrar a httpOnly cookies (requiere cambio en backend)

#### 3. Sin Headers de Seguridad en Vercel ❌
**Ubicación:** `vercel.json`

**Solución:** Agregar configuración:
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Content-Security-Policy", "value": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:;" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains" }
      ]
    }
  ]
}
```

#### 4. Source Maps en Producción ❌
**Ubicación:** `vite.config.js`
```javascript
// PROBLEMA: Expone código fuente
build: { sourcemap: true }
```

**Solución:**
```javascript
build: {
  sourcemap: false, // o 'hidden' para Sentry
}
```

#### 5. Sin Code Splitting ❌
**Problema:** Todo el código cargado en un solo bundle (~1MB)

**Solución:**
```javascript
// Lazy loading de rutas
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Compliance = React.lazy(() => import('./pages/Compliance'));
```

### Problemas ALTA PRIORIDAD:

#### 6. console.log en Producción
**Archivos afectados:** 11 instancias
- Governance.jsx
- Compliance.jsx (3)
- DataUpload.jsx
- DataQuality.jsx (3)
- ConsortiumDetail.jsx
- Navbar.jsx

**Solución:** Reemplazar con Sentry o condicionales de entorno

#### 7. Sin Error Tracking (Sentry)
**Solución:** Agregar en `main.jsx`:
```javascript
import * as Sentry from "@sentry/react";

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
  });
}
```

#### 8. Sin Retry en Llamadas API
**Problema:** Fallas de red causan error inmediato

**Solución:** Implementar retry con backoff exponencial

### Problemas MEDIA PRIORIDAD:

#### 9. Meta Tags Estáticos
- Sin Open Graph tags
- Sin descripción dinámica por página
- Título estático

#### 10. Accesibilidad Incompleta
- SVG icons sin aria-label
- Sin skip links
- Sin aria-invalid en formularios

#### 11. Sin Cache Headers
- Assets cacheados indefinidamente sin versión

---

## CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Seguridad Crítica (8-12 horas)

```bash
# Frontend - Día 1
```

- [ ] **1.1** Mover DEMO_API_KEY a variable de entorno
  - Archivo: `src/context/DemoContext.jsx`
  - Archivo: `src/api/client.js`

- [ ] **1.2** Agregar headers de seguridad a Vercel
  - Archivo: `dashboard/vercel.json`

- [ ] **1.3** Deshabilitar source maps en producción
  - Archivo: `dashboard/vite.config.js`

- [ ] **1.4** Configurar Sentry en frontend
  - Instalar: `npm install @sentry/react`
  - Archivo: `src/main.jsx`

- [ ] **1.5** Crear `.env.production` con variables requeridas

### Fase 2: Optimización Performance (6-8 horas)

```bash
# Frontend - Día 2
```

- [ ] **2.1** Implementar lazy loading de rutas
  - Archivo: `src/App.jsx`

- [ ] **2.2** Configurar code splitting en Vite
  - Archivo: `vite.config.js`

- [ ] **2.3** Agregar ErrorBoundary global
  - Crear: `src/components/ErrorBoundary.jsx`

- [ ] **2.4** Implementar retry logic en API client
  - Archivo: `src/api/client.js`

### Fase 3: Calidad de Código (4-6 horas)

```bash
# Frontend - Día 3
```

- [ ] **3.1** Eliminar/condicionar console.log statements
  - 11 archivos afectados

- [ ] **3.2** Agregar manejo de timeout en requests
  - Archivo: `src/api/client.js`

- [ ] **3.3** Mejorar mensajes de error
  - Reemplazar "Error desconocido" con mensajes específicos

### Fase 4: Backend Final (4-6 horas)

```bash
# Backend - Día 3-4
```

- [ ] **4.1** Ejecutar scripts de validación
  ```bash
  cd backend_django
  python scripts/validate_env.py --strict
  python scripts/verify_production.py
  ```

- [ ] **4.2** Configurar variables de producción
  - DJANGO_SECRET_KEY
  - DATABASE_URL
  - SENTRY_DSN
  - CORS_ALLOWED_ORIGINS (sin localhost)

- [ ] **4.3** Ejecutar test suite completa
  ```bash
  pytest --cov=apps --cov-report=html
  ```

### Fase 5: Documentación (2-4 horas)

- [ ] **5.1** Actualizar README con instrucciones de producción
- [ ] **5.2** Documentar variables de entorno requeridas
- [ ] **5.3** Crear runbook de deployment
- [ ] **5.4** Documentar procedimiento de rollback

---

## VARIABLES DE ENTORNO REQUERIDAS

### Backend (.env)
```bash
# CRÍTICO
DJANGO_SECRET_KEY=<min-50-chars-high-entropy>
DJANGO_DEBUG=False
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DJANGO_ALLOWED_HOSTS=apifhe.xcapit.com

# IMPORTANTE
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=https://key@sentry.io/project
JWT_SIGNING_KEY=<separate-from-django-secret>
CORS_ALLOWED_ORIGINS=https://appfhe.xcapit.com

# OPCIONAL
FHE_SECURITY_LEVEL=128
BLOCKCHAIN_ENV=testnet
```

### Frontend (.env.production)
```bash
# CRÍTICO
VITE_API_URL=https://apifhe.xcapit.com
VITE_SENTRY_DSN=https://key@sentry.io/frontend

# IMPORTANTE
VITE_DEMO_API_KEY=<desde-backend-no-hardcodeado>

# OPCIONAL
VITE_GA_ID=G-XXXXXXXXXX
VITE_ENABLE_ANALYTICS=true
```

---

## COMANDOS DE VERIFICACIÓN

```bash
# 1. Verificar backend
cd backend_django
python scripts/validate_env.py --strict
python scripts/verify_production.py
pytest --tb=short

# 2. Verificar frontend
cd dashboard
npm run build
# Verificar que no hay warnings de seguridad

# 3. Verificar headers de seguridad
curl -I https://appfhe.xcapit.com | grep -E "(Content-Security|X-Frame|X-Content)"

# 4. Verificar source maps
ls -la dashboard/dist/assets/*.map  # No debería existir

# 5. Verificar bundle size
du -sh dashboard/dist/
# Target: < 500KB gzipped
```

---

## MATRIZ DE RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| API Key expuesta | Alta | Crítico | Mover a env vars |
| XSS roba tokens | Media | Crítico | httpOnly cookies |
| Source code expuesto | Alta | Alto | Disable sourcemaps |
| Falla sin tracking | Alta | Alto | Configurar Sentry |
| Bundle lento | Media | Medio | Code splitting |
| Brute force | Baja | Alto | Ya mitigado (axes) |
| SQL Injection | Muy Baja | Crítico | ORM Django protege |

---

## TIMELINE SUGERIDO

| Día | Tareas | Horas |
|-----|--------|-------|
| 1 | Fase 1: Seguridad Crítica Frontend | 8h |
| 2 | Fase 2: Performance Frontend | 6h |
| 3 | Fase 3: Código + Fase 4: Backend | 8h |
| 4 | Fase 5: Docs + Testing Final | 6h |
| 5 | Buffer + Deploy Staging | 4h |

**Total estimado:** 32 horas (4-5 días)

---

## APROBACIÓN PARA PRODUCCIÓN

### Criterios de Aceptación

- [ ] Todos los items CRÍTICOS completados
- [ ] `validate_env.py --strict` pasa sin errores
- [ ] `verify_production.py` pasa sin errores
- [ ] Test suite 100% passing
- [ ] Security headers verificados
- [ ] Sentry configurado y recibiendo eventos
- [ ] Source maps deshabilitados
- [ ] No hay secrets en código fuente
- [ ] Documentación actualizada

### Sign-off

| Rol | Nombre | Fecha | Firma |
|-----|--------|-------|-------|
| Developer | | | |
| Security Review | | | |
| QA | | | |

---

*Documento generado el 29 de Enero de 2026*
