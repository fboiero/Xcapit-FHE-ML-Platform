# Copy Landing Hub / Selector de Industria

## Propósito
Página principal minimalista que dirige a cada visitante a su landing vertical específica.

---

## DISEÑO RECOMENDADO

### Estilo Visual
- Full-screen
- Minimalista
- 4 cards grandes centradas
- Fondo gradiente sutil (marca)
- Sin scroll (todo visible)

---

## HERO SECTION

### Headline

**ES:**
> La plataforma donde empresas competidoras colaboran con datos sin compartirlos.

**EN:**
> The platform where competing companies collaborate on data without sharing it.

### Subheadline

**ES:**
> Forma consorcios de datos, entrena modelos de ML conjuntos y preserva la privacidad total con cifrado homomorfico.

**EN:**
> Form data consortiums, train joint ML models, and preserve total privacy with homomorphic encryption.

---

## SELECTOR DE INDUSTRIA

### Título

**ES:** ¿En qué industria operas?
**EN:** What industry are you in?

### 3 Cards Principales (Grid horizontal)

**Orden:** Fintech → Healthcare → Gobierno

---

#### Card 1: Finanzas y Banca (PRIMERA POSICIÓN)

**Icono:** 🏦 o icono de banco/moneda

**Título:**
- ES: Finanzas y Banca
- EN: Finance & Banking

**Descripción corta:**
- ES: Detección de fraude, credit scoring y KYC/AML colaborativo entre instituciones financieras.
- EN: Fraud detection, credit scoring, and collaborative KYC/AML across financial institutions.

**Ejemplos (bullets pequeños):**
- ES: Fraude / Credit Scoring / KYC-AML
- EN: Fraud / Credit Scoring / KYC-AML

**CTA:**
- ES: Ver soluciones Fintech →
- EN: See Fintech solutions →

**Link:** `/fintech`

---

#### Card 2: Salud y Healthcare

**Icono:** 🏥 o icono de hospital/cruz

**Título:**
- ES: Salud y Healthcare
- EN: Healthcare

**Descripción corta:**
- ES: Investigación médica colaborativa y diagnóstico asistido por IA sin exponer datos de pacientes.
- EN: Collaborative medical research and AI-assisted diagnosis without exposing patient data.

**Ejemplos (bullets pequeños):**
- ES: Diagnóstico / Drug Discovery / Ensayos Clínicos
- EN: Diagnosis / Drug Discovery / Clinical Trials

**CTA:**
- ES: Ver soluciones Healthcare →
- EN: See Healthcare solutions →

**Link:** `/healthcare`

---

#### Card 3: Gobierno y Sector Público

**Icono:** 🏛️ o icono de edificio gubernamental

**Título:**
- ES: Gobierno y Sector Público
- EN: Government & Public Sector

**Descripción corta:**
- ES: Colaboración inter-agencias para detección de fraude fiscal y políticas públicas basadas en datos.
- EN: Cross-agency collaboration for tax fraud detection and data-driven public policy.

**Ejemplos (bullets pequeños):**
- ES: Fraude Fiscal / Políticas Públicas / Ventanilla Única
- EN: Tax Fraud / Public Policy / Single Window

**CTA:**
- ES: Ver soluciones Gobierno →
- EN: See Government solutions →

**Link:** `/gobierno`

---

### Link secundario: Otras Industrias

**Formato:** Texto link centrado debajo de las 3 cards (no es una card)

**ES:**
> ¿Otra industria? Retail, seguros, telecomunicaciones y más → [Ver soluciones]

**EN:**
> Different industry? Retail, insurance, telecom and more → [See solutions]

**Link:** `/industrias`

---

## FOOTER MÍNIMO

### Texto

**ES:**
> Desarrollado por el equipo de QuarkID (3.6M+ usuarios)

**EN:**
> Built by the QuarkID team (3.6M+ users)

### Links

- Documentación / Documentation
- GitHub
- Contacto / Contact

---

## VARIANTE: CON CONTEXTO ADICIONAL

Si se quiere agregar más información antes del selector:

### Sección "Por qué funciona"

**3 puntos visuales (iconos + texto corto):**

| Icono | ES | EN |
|-------|----|----|
| 🔐 | **Datos siempre cifrados** - Nadie puede descifrar tus datos, ni siquiera nosotros | **Data always encrypted** - No one can decrypt your data, not even us |
| ⛓️ | **Gobernanza blockchain** - Auditoría inmutable de todas las operaciones | **Blockchain governance** - Immutable audit of all operations |
| 🤝 | **Colaboración sin confianza** - No necesitas confiar en otros participantes | **Trustless collaboration** - No need to trust other participants |

---

## ANALYTICS A IMPLEMENTAR

### Eventos a trackear

1. **Page view hub** - Cuántos llegan al selector
2. **Card hover** - Qué verticales generan interés
3. **Card click** - A qué vertical navegan
4. **Source attribution** - De dónde vienen (ads, orgánico, referral)
5. **Time to decision** - Cuánto tardan en elegir

### Segmentación para campañas

```
utm_source=google&utm_medium=cpc&utm_campaign=fintech_latam
utm_source=linkedin&utm_medium=cpc&utm_campaign=healthcare_usa
utm_source=google&utm_medium=cpc&utm_campaign=gobierno_argentina
```

---

## DISEÑO RESPONSIVO

### Desktop
- 4 cards en grid 2x2
- Hero arriba centrado
- Footer abajo

### Tablet
- 4 cards en grid 2x2 más compacto
- Scroll mínimo

### Mobile
- 4 cards apiladas verticalmente
- Hero más pequeño
- Scroll necesario

---

## CÓDIGO PSEUDO-ESTRUCTURA

```jsx
<HubLanding>
  <Header minimal>
    <Logo />
    <LanguageSwitcher />
  </Header>

  <Hero centered>
    <Headline />   {/* "Entrena modelos con datos que no puedes ver." */}
    <Subheadline /> {/* "Múltiples organizaciones entrenan UN modelo..." */}
  </Hero>

  <IndustrySelector>
    <SelectorTitle /> {/* "¿En qué industria operas?" */}

    <Grid cols={3}> {/* 3 cards en fila */}
      <IndustryCard
        icon="🏦"
        title="Finanzas y Banca"
        description="Detección de fraude, credit scoring y KYC/AML..."
        examples={["Fraude", "Credit Scoring", "KYC-AML"]}
        link="/fintech"
      />
      <IndustryCard
        icon="🏥"
        title="Salud y Healthcare"
        description="Investigación médica colaborativa..."
        examples={["Diagnóstico", "Drug Discovery", "Ensayos"]}
        link="/healthcare"
      />
      <IndustryCard
        icon="🏛️"
        title="Gobierno"
        description="Colaboración inter-agencias..."
        examples={["Fraude Fiscal", "Políticas", "Ventanilla"]}
        link="/gobierno"
      />
    </Grid>

    <SecondaryLink> {/* Link texto, no card */}
      "¿Otra industria? Retail, seguros, telecomunicaciones y más →"
      link="/industrias"
    </SecondaryLink>
  </IndustrySelector>

  <Footer minimal>
    <Credencial /> {/* "Desarrollado por QuarkID (3.6M+ usuarios)" */}
    <Links />
  </Footer>
</HubLanding>
```

---

## VARIANTES A/B PARA TESTEAR

### Variante A: Selector puro
- Solo cards, sin texto adicional
- Más limpio, más directo

### Variante B: Selector con contexto
- Agrega sección "Por qué funciona" antes de cards
- Más información, posiblemente mayor conversión

### Variante C: Selector con video
- Video corto (30s) explicando FHE antes de cards
- Mayor engagement, posiblemente mayor drop-off

### Métricas de éxito
- **Click-through rate** a cada vertical
- **Bounce rate** del hub
- **Conversión final** (demo agendada) por origen

---

## NOTAS DE IMPLEMENTACIÓN

### SEO
- Title: "Xcapit Privacy - Plataforma de Consorcios de Datos con Privacidad Criptografica"
- Meta description diferente por idioma
- Structured data para organización

### Performance
- Cards deben cargar instantáneamente
- No dependencias pesadas
- LCP < 1.5s

### Accesibilidad
- Cards navegables con teclado
- Alt text para iconos
- Contraste suficiente
