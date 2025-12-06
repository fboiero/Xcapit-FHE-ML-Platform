# Capítulo 1: Introducción a la Encriptación Homomórfica

## 1.1 ¿Qué es la Encriptación Homomórfica?

La **Encriptación Homomórfica (HE)** es un tipo especial de encriptación que permite realizar operaciones matemáticas sobre datos encriptados sin necesidad de descifrarlos primero.

### Definición Formal

Sea `E` una función de encriptación y `D` una función de descifrado. Un esquema de encriptación es **homomórfico** si:

```
D(E(a) ⊕ E(b)) = a ○ b
```

Donde:
- `⊕` es una operación en el espacio cifrado
- `○` es la operación correspondiente en el espacio original
- `a` y `b` son datos en texto plano

### Analogía Simple

Imagina una **caja fuerte mágica** con guantes incorporados:

```
┌─────────────────────────────────────────────────────────────┐
│                      CAJA FUERTE MÁGICA                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │    🔢 Datos Encriptados                             │   │
│  │    (Solo el dueño puede ver el contenido real)      │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  🧤 ─────────────────────────────────────────────── 🧤     │
│     Guantes: Puedes manipular sin ver                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- Puedes meter las manos (a través de los guantes)
- Puedes manipular lo que hay dentro
- **Pero no puedes ver** lo que estás manipulando
- Solo el dueño de la llave puede abrir y ver el resultado

---

## 1.2 Tipos de Encriptación Homomórfica

### Diagrama Comparativo

![Tipos de HE](../diagrams/he-types.svg)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TIPOS DE ENCRIPTACIÓN HOMOMÓRFICA                │
├─────────────────────┬─────────────────────┬─────────────────────────┤
│   PARCIALMENTE      │   ALGO              │   COMPLETAMENTE         │
│   HOMOMÓRFICA       │   HOMOMÓRFICA       │   HOMOMÓRFICA (FHE)     │
│   (PHE)             │   (SHE)             │                         │
├─────────────────────┼─────────────────────┼─────────────────────────┤
│                     │                     │                         │
│  Solo UNA           │  Operaciones        │  CUALQUIER              │
│  operación:         │  LIMITADAS:         │  operación:             │
│                     │                     │                         │
│  • RSA: ×           │  • Suma hasta N     │  • Suma ✓               │
│  • Paillier: +      │  • Mult hasta M     │  • Mult ✓               │
│  • ElGamal: ×       │                     │  • Sin límite ✓         │
│                     │                     │                         │
├─────────────────────┼─────────────────────┼─────────────────────────┤
│  Rápido pero        │  Más flexible       │  Máxima flexibilidad    │
│  muy limitado       │  pero con límites   │  pero más lento         │
├─────────────────────┼─────────────────────┼─────────────────────────┤
│  Uso: Votación      │  Uso: Cálculos      │  Uso: ML, Analytics     │
│  electrónica        │  específicos        │  completos              │
└─────────────────────┴─────────────────────┴─────────────────────────┘
```

### 1.2.1 Encriptación Parcialmente Homomórfica (PHE)

Permite **una sola operación** (suma O multiplicación) un número ilimitado de veces.

**Ejemplo: RSA (multiplicativamente homomórfico)**

```python
# RSA permite multiplicar números encriptados
E(a) × E(b) = E(a × b)

# Ejemplo numérico:
E(3) × E(5) = E(15)
```

### 1.2.2 Encriptación Algo Homomórfica (SHE)

Permite **ambas operaciones** pero con un número **limitado** de veces.

```
Límite: ~10-15 multiplicaciones antes de que el "ruido" corrompa los datos
```

### 1.2.3 Encriptación Completamente Homomórfica (FHE)

Permite **cualquier operación**, **cualquier número de veces**.

**Este es el tipo que usa Xcapit FHE-ML.**

---

## 1.3 Historia de FHE

```
┌─────────────────────────────────────────────────────────────────────┐
│                          LÍNEA TEMPORAL                              │
├──────────┬──────────────────────────────────────────────────────────┤
│   1978   │  Rivest, Adleman, Dertouzos proponen la idea             │
│          │  "¿Es posible computar sobre datos encriptados?"         │
├──────────┼──────────────────────────────────────────────────────────┤
│   2009   │  Craig Gentry (IBM) presenta el PRIMER esquema FHE       │
│          │  Tesis doctoral en Stanford - revolucionario             │
├──────────┼──────────────────────────────────────────────────────────┤
│   2011   │  Brakerski-Gentry-Vaikuntanathan (BGV)                   │
│          │  Más eficiente, basado en Learning With Errors (LWE)     │
├──────────┼──────────────────────────────────────────────────────────┤
│   2012   │  Brakerski-Fan-Vercauteren (BFV)                         │
│          │  Optimizado para enteros                                  │
├──────────┼──────────────────────────────────────────────────────────┤
│   2017   │  CKKS (Cheon-Kim-Kim-Song)                               │
│          │  ⭐ Soporta números decimales (punto flotante)           │
│          │  ⭐ IDEAL PARA MACHINE LEARNING                          │
├──────────┼──────────────────────────────────────────────────────────┤
│   2020+  │  Implementaciones prácticas: SEAL, TenSEAL, OpenFHE     │
│          │  FHE se vuelve viable para producción                    │
└──────────┴──────────────────────────────────────────────────────────┘
```

---

## 1.4 ¿Por qué FHE para Machine Learning?

### El Problema de la Privacidad en ML

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ESCENARIO TRADICIONAL (INSEGURO)                 │
│                                                                      │
│   Hospital                    Nube/Servidor                         │
│  ┌─────────┐                 ┌─────────────┐                        │
│  │ Datos   │────────────────▶│   Modelo    │                        │
│  │Pacientes│  TEXTO PLANO    │     ML      │                        │
│  │  (PHI)  │   ⚠️ RIESGO     │             │                        │
│  └─────────┘                 └─────────────┘                        │
│                                                                      │
│  ❌ Datos expuestos durante transmisión                             │
│  ❌ Servidor puede ver datos sensibles                              │
│  ❌ Riesgo de breach de datos                                       │
│  ❌ Problemas de compliance (HIPAA, GDPR)                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    ESCENARIO CON FHE (SEGURO)                       │
│                                                                      │
│   Hospital                    Nube/Servidor                         │
│  ┌─────────┐                 ┌─────────────┐                        │
│  │ Datos   │──── E(datos) ──▶│   Modelo    │                        │
│  │Pacientes│    CIFRADO      │     ML      │                        │
│  │  (PHI)  │    🔒 SEGURO    │  (ve solo   │                        │
│  └─────────┘                 │   ruido)    │                        │
│       │                      └──────┬──────┘                        │
│       │                             │                               │
│       │◀────── E(predicción) ───────┘                               │
│       │         CIFRADO                                             │
│       ▼                                                             │
│  ┌─────────┐                                                        │
│  │Descifrar│  Solo el hospital puede ver el resultado               │
│  │resultado│                                                        │
│  └─────────┘                                                        │
│                                                                      │
│  ✅ Datos NUNCA expuestos                                           │
│  ✅ Servidor NO puede ver datos                                     │
│  ✅ Compliance automático                                           │
│  ✅ Zero-knowledge computation                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1.5 Propiedades Matemáticas

### Homomorfismo Aditivo

```
E(a) + E(b) = E(a + b)
```

**Demostración visual:**

```
    Espacio Original          Espacio Cifrado
    ─────────────────         ─────────────────
         3                        E(3) = 🔒₁
         +                          +
         5                        E(5) = 🔒₂
         ↓                          ↓
         8          ═══════       E(8) = 🔒₃

    D(E(3) + E(5)) = D(🔒₃) = 8 ✓
```

### Homomorfismo Multiplicativo

```
E(a) × E(b) = E(a × b)
```

**Demostración visual:**

```
    Espacio Original          Espacio Cifrado
    ─────────────────         ─────────────────
         3                        E(3) = 🔒₁
         ×                          ×
         5                        E(5) = 🔒₂
         ↓                          ↓
        15          ═══════       E(15) = 🔒₄

    D(E(3) × E(5)) = D(🔒₄) = 15 ✓
```

---

## 1.6 El Concepto de "Ruido" en FHE

Una característica fundamental de FHE es el **ruido criptográfico**.

### ¿Qué es el Ruido?

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CONCEPTO DE RUIDO                           │
│                                                                      │
│   Valor Original: 42.0                                              │
│                                                                      │
│   Después de Encriptar:                                             │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  E(42.0) = [valor_cifrado] + ruido_pequeño                  │   │
│   │                                                              │   │
│   │  El ruido es NECESARIO para la seguridad                    │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   Después de MUCHAS operaciones:                                    │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  E(resultado) = [valor_cifrado] + RUIDO_GRANDE              │   │
│   │                                                              │   │
│   │  ⚠️ Si el ruido crece demasiado, el resultado se corrompe  │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   Solución: BOOTSTRAPPING (re-encriptar para reducir ruido)         │
└─────────────────────────────────────────────────────────────────────┘
```

### Crecimiento del Ruido por Operación

```
Nivel de Ruido
     │
  100│                                    ╱ CORRUPTO
     │                                  ╱
   80│                                ╱
     │                              ╱ ← Límite
   60│                            ╱
     │                    ╱──────╱
   40│              ╱────╱
     │        ╱────╱
   20│  ╱────╱
     │╱
    0└──────┬──────┬──────┬──────┬──────┬──────▶
            5     10     15     20     25    Operaciones

    ───── Suma (crece lento)
    ╱──── Multiplicación (crece rápido)
```

---

## 1.7 Seguridad de FHE

### Basado en Problemas Matemáticos Difíciles

FHE basa su seguridad en el problema **Learning With Errors (LWE)**:

```
Dado:  A · s + e = b  (mod q)

Donde:
- A es una matriz aleatoria conocida
- s es el secreto (clave privada)
- e es un vector de error pequeño
- b es el resultado

Problema: Encontrar s dado A y b

Este problema es considerado difícil incluso para computadoras cuánticas.
```

### Niveles de Seguridad

```
┌─────────────────────────────────────────────────────────────────────┐
│                      NIVELES DE SEGURIDAD                           │
├──────────────┬──────────────────┬───────────────────────────────────┤
│    Nivel     │   Bits Seguridad │   Equivalencia                    │
├──────────────┼──────────────────┼───────────────────────────────────┤
│  TC128       │      128 bits    │   AES-128, RSA-3072               │
│  TC192       │      192 bits    │   AES-192, RSA-7680               │
│  TC256       │      256 bits    │   AES-256, RSA-15360              │
└──────────────┴──────────────────┴───────────────────────────────────┘

Nota: 128 bits de seguridad significa que un atacante necesitaría
2^128 operaciones para romper la encriptación.

Tiempo estimado para romper 128-bit con supercomputadora:
> Edad del universo × 10^20
```

---

## 1.8 Resumen del Capítulo

| Concepto | Descripción |
|----------|-------------|
| **FHE** | Encriptación que permite computar sobre datos cifrados |
| **Homomorfismo** | Propiedad matemática que preserva operaciones |
| **Ruido** | Error necesario para seguridad, limita operaciones |
| **CKKS** | Esquema FHE que soporta números decimales (ideal para ML) |
| **Seguridad** | Basada en LWE, resistente a ataques cuánticos |

---

## 1.9 Ejercicios

1. **Conceptual**: Explica con tus palabras por qué FHE es importante para la privacidad en ML.

2. **Matemático**: Si `E(3) ⊕ E(4) = E(7)`, ¿qué operación representa `⊕`?

3. **Análisis**: ¿Por qué el ruido crece más rápido con multiplicaciones que con sumas?

---

**Siguiente capítulo**: [El Esquema CKKS →](02-ckks-scheme.md)
