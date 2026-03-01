# Dashboard Frontend

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| React | 18.2 | UI framework |
| Vite | 5.x | Build tool, dev server on `:3000` |
| react-router-dom | 6.20 | Client-side routing |
| TailwindCSS | 3.3 | Utility-first styling |
| react-i18next | 16.4 + i18next 25.7 | i18n (ES/EN/DE) |
| framer-motion | 12.29 | Animations |
| @heroicons/react | 2.2 + lucide-react | Icons |
| sonner | 2.x | Toast notifications |
| @sentry/react | 10.38 | Error tracking (prod only) |

No state management library — uses React Context + `useState`/`useEffect` only.

## Directory Structure

```
dashboard/
├── index.html              # Entry HTML, Inter font, OG meta
├── package.json            # type: "module", no test runner
├── vite.config.js          # Proxy /api -> :8000, manual chunks
├── tailwind.config.js      # brand + navy color palettes
├── vercel.json             # SPA rewrites, security headers, CSP
└── src/
    ├── main.jsx            # BrowserRouter, StrictMode, Sentry init
    ├── App.jsx             # All routes, lazy loading, ProtectedRoute
    ├── index.css           # Tailwind directives, status/role utilities
    ├── api/                # Native fetch wrappers (no axios)
    │   ├── client.js       # Main API client (consortiums, auth, training)
    │   ├── sandbox.js      # Sandbox lead capture + token API
    │   ├── governance.js   # Governance endpoints
    │   ├── compliance.js   # Compliance endpoints
    │   └── dataQuality.js  # Data quality endpoints
    ├── config/
    │   ├── index.js        # Re-exports blockchain config
    │   ├── demo.js         # DEMO_API_KEY, DEMO_EMAIL constants
    │   └── blockchain.js   # Arbitrum testnet/mainnet config
    ├── context/
    │   └── DemoContext.jsx  # DemoProvider + useDemo hook, industry scenarios
    ├── i18n/
    │   ├── index.js        # i18next init (localStorage detection, fallback: en)
    │   └── locales/{en,es}/translation.json
    ├── lib/sentry.js       # initSentry(), prod only
    ├── components/
    │   ├── Layout.jsx      # Navbar + Sidebar + Outlet + Toaster
    │   ├── Navbar.jsx      # Fixed top bar, company menu, demo badge
    │   ├── Sidebar.jsx     # Fixed left 64px, NavLink items
    │   ├── Breadcrumbs.jsx # Auto-generated from route path
    │   ├── ErrorBoundary.jsx # Class component, Sentry integration
    │   ├── LanguageSwitcher.jsx # 3 variants: dropdown, toggle, minimal
    │   └── ui/             # Reusable primitives
    │       ├── Button.jsx  # primary|secondary|danger|ghost, sm|md|lg
    │       ├── Card.jsx    # default|elevated|interactive + sub-components
    │       ├── Modal.jsx   # Portal, focus trap, Escape close
    │       ├── Badge.jsx   # 6 variants + StatusBadge preset
    │       └── Toaster.jsx # sonner wrapper, brand-styled
    └── pages/              # 42 pages, all lazy-loaded
```

## Routing Pattern

Three tiers in `App.jsx`:

```jsx
// 1. Public (redirect to /dashboard if authenticated)
<PublicRoute><Login /></PublicRoute>

// 2. Semi-public (no auth required)
<Route path="/sandbox-demo" element={<SandboxDemo />} />

// 3. Protected (redirect to / if not authenticated)
<Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
  <Route path="/dashboard" element={<Dashboard />} />
  <Route path="/governance/:consortiumId" element={<Governance />} />
</Route>
```

- Auth check: `isAuthenticated()` reads `xcapit_api_key` from `localStorage`
- All page components are `lazy()` loaded with `<Suspense fallback={<PageLoader />}>`
- Many routes accept optional `/:consortiumId` param

## API Client Pattern

Native `fetch` wrapper with `fetchWithRetry` (3 retries, exponential backoff, 30s timeout). Auth via `X-API-Key` header from localStorage.

| Module | Base Path |
|--------|-----------|
| `client.js` | `/api/v1/consortiums` |
| `governance.js` | `/api/v1` |
| `compliance.js` | `/api/v1` |
| `dataQuality.js` | `/api/v1` |
| `sandbox.js` | `/api/v2/sandbox` |

## Component Patterns

### UI Primitives (`src/components/ui/`)

Import via barrel: `import { Button, Card, Modal, Badge } from '../components/ui'`

- `variant` + `size` props with Tailwind class maps
- `className` prop for overrides
- Compound pattern: `Card.Header`, `Card.Title`, `Card.Body`, `Card.Footer`
- Loading states with inline SVG spinner

### Page Pattern

1. `useTranslation()` for text
2. `useDemo()` for demo mode detection
3. `useEffect` fetch with loading/error states
4. `SkeletonCard` for loading, `EmptyState` for empty

## i18n

```jsx
const { t, i18n } = useTranslation()
return <h1>{t('dashboard.title')}</h1>
```

- Detection: `localStorage` (`xcapit_language`) > browser > `en`
- Add keys to both `en/translation.json` and `es/translation.json`

## Theming

- **Colors**: `brand-50..950` (indigo/purple), `navy-800..950` (dark backgrounds)
- **Font**: Inter (Google Fonts)
- **Radius**: `rounded-xl` cards/buttons, `rounded-full` badges
- **Focus**: `focus:ring-2 focus:ring-brand-500 focus:ring-offset-2`
- **Layout**: Navbar `h-16 bg-navy-900`, Sidebar `w-64 bg-white`, Main `md:ml-64`

## Environment Variables (prefix `VITE_`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `/api/v1/consortiums` | Backend API base |
| `VITE_SENTRY_DSN` | (none) | Sentry DSN |
| `VITE_BLOCKCHAIN_ENV` | `testnet` | `testnet` or `mainnet` |

## Build & Deploy

```bash
npm run dev      # Dev server on :3000
npm run build    # Production build to dist/
npm run preview  # Preview production build
```

Deploy: Vercel. SPA rewrite, security headers (HSTS, CSP, X-Frame-Options: DENY).

## Rules

1. All JSX files use `.jsx` extension — no TypeScript
2. Functional components only (except ErrorBoundary)
3. Icons: prefer `@heroicons/react/24/outline`
4. Toasts: `import { toast } from 'sonner'`
5. Every page MUST be `lazy()` imported in `App.jsx`
6. Demo awareness: check `isDemoMode()` or `useDemo()`
7. No CSS modules — Tailwind utility classes only
