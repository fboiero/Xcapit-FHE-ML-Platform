# Xcapit FHE-ML Platform Documentation

## Documentación Completa del SDK de Machine Learning con Encriptación Homomórfica

---

## Tabla de Contenidos

### Parte I: Fundamentos Teóricos
1. [Introducción a la Encriptación Homomórfica](theory/01-homomorphic-encryption.md)
2. [El Esquema CKKS](theory/02-ckks-scheme.md)
3. [Machine Learning sobre Datos Encriptados](theory/03-ml-on-encrypted-data.md)
4. [Aproximaciones Polinomiales para FHE](theory/04-polynomial-approximations.md)

### Parte II: Arquitectura del Sistema
5. [Arquitectura General](guides/01-architecture.md)
6. [Capa de Encriptación](guides/02-encryption-layer.md)
7. [Modelos de Machine Learning](guides/03-ml-models.md)
8. [Integración Blockchain](guides/04-blockchain-integration.md)

### Parte III: Guías Prácticas
9. [Guía de Inicio Rápido](guides/05-quickstart.md)
10. [Entrenamiento de Modelos](guides/06-training-models.md)
11. [Deployment en Producción](guides/07-deployment.md)
12. [Casos de Uso](guides/08-use-cases.md)

### Parte IV: Referencia API
13. [SDK Python](api/python-sdk.md)
14. [REST API](api/rest-api.md)
15. [CLI](api/cli-reference.md)

### Anexos
- [Glosario](glossary.md)
- [Referencias Bibliográficas](references.md)
- [FAQ](faq.md)

---

## ¿Qué es Xcapit FHE-ML?

Xcapit FHE-ML es una plataforma que permite realizar **Machine Learning sobre datos encriptados** utilizando **Encriptación Homomórfica Completa (FHE)**. Esto significa que:

1. Los datos **nunca se descifran** durante el procesamiento
2. Los modelos pueden **entrenarse y hacer predicciones** sin ver los datos originales
3. Solo el propietario de los datos puede **descifrar los resultados**

### Diagrama Conceptual

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Datos         │     │   Servidor ML   │     │   Resultados    │
│   Originales    │     │   (No ve datos) │     │   Descifrados   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
    ┌─────────┐            ┌─────────┐            ┌─────────┐
    │Encriptar│───────────▶│Procesar │───────────▶│Descifrar│
    │ (CKKS)  │  Cifrado   │Cifrado  │  Cifrado   │ (CKKS)  │
    └─────────┘            └─────────┘            └─────────┘
         │                       │                       │
    ┌────┴────┐            ┌────┴────┐            ┌────┴────┐
    │ Llave   │            │Solo ve  │            │ Llave   │
    │ Pública │            │números  │            │ Privada │
    └─────────┘            │aleatorio│            └─────────┘
                           └─────────┘
```

---

## Audiencia

Esta documentación está diseñada para:

- **Científicos de datos** que quieren proteger datos sensibles
- **Desarrolladores** que implementan soluciones de ML privadas
- **Investigadores** interesados en criptografía aplicada
- **Oficiales de cumplimiento** (HIPAA, GDPR, LGPD)
- **Estudiantes** aprendiendo sobre FHE y ML

---

## Requisitos Previos

Para entender completamente esta documentación, se recomienda conocimiento básico de:

- Álgebra lineal (vectores, matrices)
- Probabilidad y estadística
- Machine Learning básico
- Python programming

No se requiere conocimiento previo de criptografía.

---

## Navegación Rápida

| Quiero... | Ir a... |
|-----------|---------|
| Entender qué es FHE | [Teoría: Encriptación Homomórfica](theory/01-homomorphic-encryption.md) |
| Empezar a usar el SDK | [Guía: Inicio Rápido](guides/05-quickstart.md) |
| Ver ejemplos de código | [Demos](demos/) |
| Entender la arquitectura | [Arquitectura General](guides/01-architecture.md) |
| Usar la REST API | [API Reference](api/rest-api.md) |

---

*Versión: 1.0.0 | Última actualización: Diciembre 2024*
