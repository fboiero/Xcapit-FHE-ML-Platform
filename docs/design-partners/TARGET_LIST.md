# Target List — Design Partners

> Documento interno. NO compartir externamente.

## Ideal Customer Profile (ICP)

### Criterios de calificación (los 5 must-have)

1. **Trabajan con datos sensibles regulados** (PII, PHI, datos financieros, datos clasificados)
2. **Tienen al menos un caso de uso multi-organización identificado** (consorcio, intercambio inter-bancario, federación de hospitales)
3. **Equipo de data science establecido** (mínimo 3 personas dedicadas, no shared con otros roles)
4. **Cloud-native o cloud-friendly** (AWS, GCP o Azure operativo)
5. **Sponsor ejecutivo identificable** (CTO, CISO, Head of Innovation, Chief Data Officer)

### Anti-criterios (descartar inmediatamente)

- ❌ "Estamos evaluando ML" sin caso concreto
- ❌ Sin presupuesto identificado para 2026
- ❌ Procurement >6 meses (ej: gobiernos centrales sin programa de innovación)
- ❌ Requieren on-premise puro sin conectividad (eso es fase 2)
- ❌ Ya invirtieron en competidor cerrado (Duality/TripleBlind/Enveil) hace <12 meses

---

## Verticales priorizados

### 🏦 Banking & Fintech (PRIORIDAD 1)

**Por qué**: regulación clara (PCI-DSS 4.0, Basel III), casos de fraude obvios, presupuesto disponible, ya hablan de "data sharing" en industry forums.

**Casos de uso ancla**:
- Detección de fraude cross-institución (ATM skimming, card-not-present)
- AML / KYC / sanctions screening colaborativo
- Credit scoring para no-bancarizados (datos alternativos cross-fintech)
- Risk pooling para reaseguros bancarios

**LATAM target accounts** (warm intro candidates via QuarkID network):
- Argentina: Banco Galicia, BBVA, Santander, Itaú, Banco Macro, Mercado Pago
- Chile: Banco de Chile, BCI, Falabella Bank
- México: BBVA México, Banorte, Banco Azteca, Konfío, Klar
- Brasil: Itaú, Bradesco, Nubank, Stone, PagBank
- Colombia: Bancolombia, Davivienda, Banco de Bogotá

**EU/US target accounts** (cold outreach):
- Innovation labs: ING Labs, JP Morgan AI Research, BBVA New Digital Businesses
- Fintech consortia: Open Banking Standard, Project Aurora (BIS)

**Industry events 2026** (presencia obligatoria):
- Money 2020 Las Vegas (Octubre)
- Singapore FinTech Festival (Noviembre)
- Open Banking Expo London (Septiembre)
- LATAM: Felaban CL Compliance, Argenfintech

---

### 🏥 Healthcare & Life Sciences (PRIORIDAD 2)

**Por qué**: HIPAA modernización 2026 (encryption obligatorio), pharma collaboration crece post-COVID, hospitales con datos pero sin escala individual para entrenar.

**Casos de uso ancla**:
- Diagnóstico cross-hospital (radiología, patología) sin centralizar imágenes
- Clinical research multi-sitio sin data lock contractual
- Pharma collaboration (real-world evidence pooling)
- Detección de fraude en seguros médicos cross-payer

**Target accounts**:
- USA: Mayo Clinic Platform, Cleveland Clinic, Kaiser Permanente Innovation
- EU: Karolinska, Charité Berlin, Erasmus MC
- LATAM: Hospital Italiano BA, Hospital Albert Einstein SP, Galenia MX
- Pharma: Roche.AI, Novartis Data42, Pfizer Digital Medicine
- Health tech: Tempus, Flatiron Health, Nightingale Open Science

**Banderas de oportunidad**:
- HIMSS announcement de nuevo programa de data collaboration
- NIH grants en federated learning healthcare
- EHDS (European Health Data Space) Article 41 — encryption requirements

---

### 🛡️ Insurance (PRIORIDAD 3)

**Por qué**: ratemaking depende de pools grandes, claims fraud es común, reinsurance ya colabora pero con métodos arcaicos.

**Casos de uso ancla**:
- Fraud detection cross-aseguradora (mismo siniestro reclamado en N pólizas)
- Pricing actuarial con pools privados
- Cyber insurance underwriting con datos de breaches reales

**Target accounts**:
- Reinsurance: Munich Re, Swiss Re, SCOR, Hannover Re
- LATAM: Sancor Seguros, Allianz LATAM, MAPFRE
- InsurTech: Lemonade Tech, Wefox, Hippo

---

### 🏛️ Government & Public Sector (PRIORIDAD 4 — long sales cycle)

**Por qué**: presupuesto grande pero ciclo de venta >12 meses. Solo perseguir si hay programa de innovación activo.

**Casos de uso ancla**:
- Fraude fiscal cross-jurisdiccional
- Estadísticas confidenciales (censos, encuestas)
- Pattern detection en lavado / corrupción

**Target accounts** (solo si hay sponsor identificado):
- AFIP / SAT México / Receita Federal Brasil (programas de fraude)
- INDEC / IBGE / INE Chile (estadística)
- BID / CAF / Banco Mundial (programas regionales)
- EU: EuroStat innovation programs

---

## Lista priorizada de los primeros 30 outreach

> Plantilla — completar con la lista real basada en QuarkID network y warm intros disponibles.

| # | Empresa | Vertical | País | Persona objetivo | Warm intro disponible | Owner Xcapit | Status |
|---|---------|----------|------|------------------|----------------------|--------------|--------|
| 1 | [completar] | Banking | AR | Head of Innovation | ✅ via QuarkID | F.Boiero | Pending outreach |
| 2 | | | | | | | |
| ... | | | | | | | |

---

## Pipeline targets

| Fase | Target | Métrica |
|------|--------|---------|
| Lista total | 30 | Cuentas calificadas con ICP completo |
| Outreach inicial | 30 | Email + LinkedIn enviado |
| Discovery calls aceptadas | 8-10 | 30% conversion |
| Demos avanzadas | 5-6 | 60% conversion de discovery |
| Pilot proposals | 4-5 | 80% conversion de demo |
| **Pilots cerrados** | **3-5** | **objetivo del programa** |

**Funnel benchmark**: 30 cuentas → 3-5 pilots = 10-17% conversion total. Esto es alto pero realista en B2B con producto novedoso + warm intros.
