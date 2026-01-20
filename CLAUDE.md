# Xcapit FHE-ML Platform - Claude Context

## Project Overview

Privacy-preserving machine learning platform using Fully Homomorphic Encryption (FHE). Enables ML on encrypted data without exposing underlying information - targeting healthcare, finance, government, and other sensitive data verticals.

## Tech Stack

### Backend (Python)
- **Framework**: FastAPI with OpenAPI 3.1
- **FHE Engine**: TenSEAL (CKKS scheme) - 128/192/256-bit security
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Blockchain**: Arbitrum integration for audit trails
- **Testing**: pytest (566+ tests)

### Frontend (React/Vite)
- **Framework**: React 18 + Vite 5
- **Styling**: TailwindCSS 3
- **i18n**: react-i18next (ES/EN)
- **State**: React Context (DemoContext)
- **Forms**: Web3Forms API for contact submissions
- **Deployment**: Vercel

### Smart Contracts (Solidity)
- ConsortiumGovernance.sol - Voting and member management
- ModelRegistry.sol - Model versioning and verification
- ComputationVerifier.sol - Proof verification

## Project Structure

```
/
├── sdk/                    # Python SDK (FHE models, encryption)
├── api/                    # FastAPI backend
│   ├── routes/            # API endpoints
│   ├── database.py        # DB connection
│   └── auth.py            # Authentication
├── dashboard/             # React frontend
│   ├── src/
│   │   ├── pages/         # Page components
│   │   │   ├── LandingHub.jsx       # Industry selector
│   │   │   ├── LandingFintech.jsx   # Fintech vertical
│   │   │   ├── LandingHealthcare.jsx # Healthcare vertical
│   │   │   ├── LandingGobierno.jsx  # Government vertical
│   │   │   ├── LandingOtros.jsx     # Other industries
│   │   │   ├── Dashboard.jsx        # Main dashboard
│   │   │   ├── Governance.jsx       # Blockchain governance
│   │   │   ├── Compliance.jsx       # Regulatory compliance
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── ui/        # Reusable UI components
│   │   │   ├── Layout.jsx
│   │   │   ├── Navbar.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── api/           # API client functions
│   │   ├── i18n/          # Translations
│   │   └── context/       # React context
│   └── public/videos/     # Demo videos (es/en)
├── contracts/             # Solidity smart contracts
├── tests/                 # Python tests
├── docs/                  # Documentation & copy
└── data/                  # SQLite database
```

## Key URLs

- **Production**: https://xcapit-privacy.vercel.app
- **Hub**: /hub
- **Fintech**: /fintech
- **Healthcare**: /healthcare
- **Government**: /gobierno
- **Other Industries**: /industrias
- **Dashboard**: /dashboard
- **GitLab**: gitlab.com:xcapit/investigacion/xcapit-fhe-ml.git

## Landing Pages Design System

Each vertical landing page follows this structure:
1. **Hero Section** - Animated SVG illustration + headline + CTA
2. **Stats Section** - 3 key metrics with icons
3. **How It Works** - 4-step process
4. **Use Cases** - 3 cards with specific applications
5. **Compliance Badges** - Industry-specific certifications
6. **Contact Form** - Web3Forms integration

### Color Themes by Vertical
- **Hub**: Gradient purple/blue
- **Fintech**: Blue/Indigo (`blue-500`, `indigo-600`)
- **Healthcare**: Emerald/Teal (`emerald-500`, `teal-600`)
- **Government**: Slate/Gray (`slate-600`, `gray-700`)
- **Other Industries**: Purple/Indigo (`purple-500`, `indigo-600`)

### Common Components
- `ParticleBackground` - Animated floating particles
- `HeroIllustration` - SVG with data flow animation
- `StatCard` - Metric display with icon
- `StepCard` - Numbered process step
- `UseCaseCard` - Feature/use case highlight
- `ComplianceBadge` - Certification badge
- `ContactForm` - Form with Web3Forms submission

## Development Commands

```bash
# Dashboard
cd dashboard
npm install
npm run dev          # Dev server (localhost:5173)
npm run build        # Production build
vercel --prod --yes  # Deploy to Vercel

# Backend
pip install -e ".[dev]"
python -m api.main   # Start API server
pytest              # Run tests

# Full stack (Docker)
docker-compose up
```

## Current State & Recent Work

### Completed
- Professional landing pages for all 5 verticals
- Animated SVG illustrations showing encrypted data flows
- Glassmorphism navbar with scroll effects
- Particle background animations
- Web3Forms contact integration
- Compliance badges per industry
- Reusable UI component library

### Pending Improvements
1. **Landing Pages**: More animations, micro-interactions, content polish
2. **Main Dashboard**: UI/UX improvements, functionality enhancements
3. **Navigation**: Better flow between pages, transitions

## Key Patterns

### Contact Form Submission
```jsx
const handleSubmit = async (e) => {
  e.preventDefault()
  const response = await fetch('https://api.web3forms.com/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      access_key: 'd7f419bc-95cf-498d-8d8b-5f4830622bf4',
      subject: 'Demo Request - [Vertical] - Xcapit Privacy',
      ...formData
    }),
  })
}
```

### Scroll-based Navbar
```jsx
const [scrolled, setScrolled] = useState(false)
useEffect(() => {
  const handleScroll = () => setScrolled(window.scrollY > 20)
  window.addEventListener('scroll', handleScroll)
  return () => window.removeEventListener('scroll', handleScroll)
}, [])
```

### SVG Data Flow Animation
```jsx
<circle className="animate-pulse" r="8" fill="currentColor">
  <animateMotion dur="3s" repeatCount="indefinite">
    <mpath href="#dataPath" />
  </animateMotion>
</circle>
```

## FHE Technical Details

- **Scheme**: CKKS (Cheon-Kim-Kim-Song) for approximate arithmetic
- **Security Levels**: 128, 192, 256 bits
- **Supported Models**: LinearRegression, LogisticRegression, DecisionTree, KMeans
- **Key Features**:
  - Encrypt data client-side
  - Train/predict on encrypted data server-side
  - Decrypt results client-side only
  - Multi-party consortium support

## Notes for Future Sessions

- Build takes ~3 minutes, produces warning about chunk size >500KB (acceptable)
- Vercel deployment is automatic on push to main
- Local dev server may have issues; deploy to Vercel for testing if needed
- User prefers Spanish communication
- Design feedback: Should look professional, like a security/privacy company
