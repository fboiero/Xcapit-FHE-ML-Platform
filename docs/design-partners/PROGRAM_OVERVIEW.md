# Xcapit Design Partners Program

> **Para CTOs, CISOs, Heads of Data, y líderes de innovación.**
> **Status**: Recibiendo aplicaciones para Q2-Q3 2026.

---

## El problema que resolvemos

Tu organización tiene datos. Tus competidores también. **Juntos podrían entrenar modelos ML mucho mejores** — detectar fraude cross-border, predecir riesgo crediticio con mejor recall, encontrar patrones de compliance que ninguno ve solo.

Pero **no pueden compartir los datos**:
- Regulación (GDPR, HIPAA, PCI-DSS 4.0, EU AI Act)
- Riesgo competitivo
- Pérdida de control sobre información sensible
- Imposibilidad de firmar contratos de data sharing entre 5+ entidades

Hoy esto se "resuelve" con consultoras armando data clean rooms cerradas, NDAs cruzados, y mucha confianza. **Es lento, caro, y no escala.**

---

## Lo que construimos

**Xcapit FHE-ML Platform** es una plataforma open-source y full-stack para **consorcios de datos** donde múltiples organizaciones entrenan modelos ML conjuntos sin que nadie vea los datos del otro.

Combinamos **4 capas criptográficas** integradas en una sola plataforma:

| Capa | Para qué | Tecnología |
|------|----------|------------|
| **FHE** (Fully Homomorphic Encryption) | Computar sobre datos cifrados sin descifrarlos | TenSEAL CKKS (128/192/256-bit) |
| **ZKP** (Zero-Knowledge Proofs) | Demostrar propiedades de los datos sin revelarlos | Pedersen + Schnorr + circuitos R1CS |
| **MPC** (Multi-Party Computation) | Computar entre múltiples partes sin centralizar | Shamir Secret Sharing (secp256k1) |
| **DP** (Differential Privacy) | Publicar resultados sin filtrar información individual | Laplace/Gaussian + RDP accounting |

Más:
- **Gobernanza on-chain** (Arbitrum smart contracts) — voting, audit trail inmutable, distribución automática de recompensas
- **24+ modelos ML** con soporte FHE escalonado
- **Compliance automatizado** — GDPR / HIPAA / SOC2 / PCI-DSS / ISO 27001
- **Open source** con licencia AGPL-3.0 — auditable, sin lock-in
- **SaaS multi-tenant** con tiers free/starter/professional/enterprise

---

## Por qué somos diferentes

| | Xcapit | Zama (Concrete-ML) | Duality | TripleBlind | OpenMined PySyft |
|---|---|---|---|---|---|
| Open source | ✅ | ✅ | ❌ | ❌ | ✅ |
| FHE | ✅ | ✅ | ✅ | Parcial | ✅ |
| ZKP | ✅ | ❌ | ❌ | ❌ | ❌ |
| MPC | ✅ | ❌ | ❌ | Parcial | ✅ |
| DP | ✅ | ❌ | ❌ | ❌ | ✅ |
| Blockchain governance | ✅ | ❌ | ❌ | ❌ | ❌ |
| Full platform (no solo SDK) | ✅ | ❌ | ✅ | ✅ | ❌ |
| Multi-vertical | ✅ | ✅ | Tech | Health | Research |

**Posicionamiento único**: somos el único stack que combina open-source + full-platform + 4 capas cripto + gobernanza on-chain.

---

## Lo que ofrecemos a los Design Partners

### Beneficios técnicos

- **Acceso completo gratuito** durante el pilot (90 días) — todos los tiers, todas las features
- **Roadmap input directo** con el equipo fundador (1 reunión cada 2 semanas)
- **Implementación asistida** por nuestro equipo de soluciones (hasta 40h de consultoría)
- **Custom integrations** priorizadas si encajan con el roadmap
- **Soporte directo** vía Slack compartido (response < 4h hábiles)

### Beneficios comerciales

- **Pricing privilegiado** post-pilot: 50% off durante el primer año
- **Contractual lock-in del precio** por 3 años post-pilot
- **Co-marketing** opcional (case study, joint webinar, logo en sitio)
- **Posición de Founding Partner** mencionada en materiales corporativos

### Beneficios estratégicos

- **First-mover advantage** en privacy-preserving ML para tu vertical
- **Equity warrant** opcional (a discutir caso por caso) para Founding Partners estratégicos
- **Mention en publicaciones académicas** que generemos durante el pilot

---

## Lo que pedimos a cambio

| Compromiso | Detalle |
|------------|---------|
| **Tiempo del equipo técnico** | 1 lead técnico + 1 data scientist asignados ~20% durante 90 días |
| **Caso de uso real** | Un problema real, no un POC sintético — datos de tu propia operación |
| **Feedback estructurado** | Reuniones bi-semanales documentadas + survey al cierre |
| **Permission para usar el caso** | Caso de éxito publicable (con o sin nombre, a tu elección) |
| **Sponsor ejecutivo** | Un C-level o VP que pueda destrabar bloqueos internos |

---

## Quiénes buscamos (perfil ideal)

**Verticales prioritarios** (en orden):
1. **Banking & Fintech** — fraud detection, credit risk, AML cross-institución
2. **Healthcare & Life Sciences** — clinical research, diagnóstico cross-hospital, pharma collaboration
3. **Insurance** — claims fraud, risk pooling, actuarial modeling
4. **Government & Public Sector** — fraud fiscal, statistics confidenciales, criminal pattern detection

**Tamaño de organización**:
- Mid-market (200-2000 empleados) — agilidad de decisión + recursos suficientes
- O Enterprise (2000+) con un sponsor ejecutivo identificado

**Madurez técnica mínima**:
- Equipo de data science establecido (mínimo 3 personas)
- Cloud infrastructure existente (AWS, GCP o Azure)
- Capacidad de hospedar workloads on-premise opcional

**Banderas rojas que descartamos**:
- "Queremos un POC sin compromiso" — no aplicar
- "El sponsor ejecutivo está pendiente de decidir" — no aplicar
- "Necesitamos firmar un MNDA antes de hablar" — no aplicar

---

## Cómo aplicar

📧 **Email**: design-partners@xcapit.com
🔗 **Form**: https://xcapit.com/design-partners (a configurar)
📅 **Discovery call directo**: https://cal.com/xcapit/dp-intro (a configurar)

**Próximos pasos**:
1. Discovery call (30 min) — entendemos tu caso de uso
2. Technical fit assessment (60 min) — workshop con tu equipo técnico
3. Pilot proposal (1 semana) — scope, métricas, timeline acordados
4. Kick-off del pilot (Day 1 of 90)

---

## Sobre Xcapit

Construido por el equipo de **QuarkID** — la primera identidad digital descentralizada con presencia en producción en LATAM, con **3.6M+ usuarios activos**.

Con esa misma rigurosidad técnica y experiencia operacional, estamos construyendo la próxima generación de infraestructura para colaboración de datos privada.

**Stack actual**: 2,116 tests / 96.23% cobertura / 19 jobs CI/CD / 391 endpoints REST / 3 smart contracts en Arbitrum / open source desde día 1.
