# NetPay Theme — Ledger (source of truth)

> **Product default theme is `ledger`.**  
> Agents and humans must not reintroduce ad-hoc hex, alternate brand palettes, or “temporary” colours on product UI without an approved Theme.md change.

Related: `frontend/app/globals.css`, `frontend/lib/theme.ts`, `/theme` lab (noindex).

---

## 1. Identity

| Field | Value |
|--------|--------|
| **Theme id** | `ledger` |
| **Name** | Ledger |
| **Positioning** | Modern fintech / API product — indigo structure, sky-blue action |
| **Typeface** | **Plus Jakarta Sans** 400–800 (UI); **IBM Plex Mono** 400–600 (code) |
| **Mode (v1)** | Light only (`color-scheme: light`) |

Lab-only alternatives (not product default): `harbor` (navy + teal), `shamba` (forest + gold). Do not ship marketing/dashboard chrome on those ids unless Theme.md is updated.

---

## 2. Colour tokens (Ledger)

Use **CSS variables** only in components. Prefer `var(--token)` or mapped Tailwind `np-*` / arbitrary `bg-[var(--…)]`.

### Structure & action

| Token | Hex | Role |
|--------|-----|------|
| `--navy` | `#1e1b4b` | Header, hero chrome, dark panels, code wells |
| `--navy-soft` | `#2e2a5a` | Nested dark surface |
| `--navy-muted` | `#3f3a6d` | Dark secondary |
| `--accent` | `#3b82f6` | Primary CTA, links, focus accent |
| `--accent-hover` | `#2563eb` | Hover/active primary |
| `--accent-soft` | `#eff6ff` | Soft fills, selected nav, icon wells |
| `--on-navy` | `#f5f3ff` | **Primary text on navy** (titles) |
| `--on-navy-muted` | `#c4b5fd` | Secondary text on navy only |
| `--on-accent` | `#ffffff` | Text on solid accent buttons |

### Canvas & text

| Token | Hex | Role |
|--------|-----|------|
| `--bg` | `#f4f2f8` | Page canvas |
| `--panel` | `#ffffff` | Cards, modals, toasts |
| `--surface` | `#eeecf5` | Recessed wells, table header |
| `--line` | `#ddd6e8` | Default borders |
| `--line-strong` | `#c4b9d6` | Strong / dashed borders |
| `--ink` | `#1e1b2e` | Primary text on light |
| `--muted` | `#5b5675` | Secondary text on light |

### Semantic

| Token | Hex | Soft |
|--------|-----|------|
| `--danger` | `#dc2626` | `--danger-soft` `#fef2f2` |
| `--warn` | `#d97706` | `--warn-soft` `#fffbeb` |
| `--ok` | `#059669` | `--ok-soft` `#ecfdf5` |
| `--info` | `#4f46e5` | `--info-soft` `#eef2ff` |
| `--focus-ring` | `#3b82f6` | Focus outline |

### Elevation & radius

| Token | Value |
|--------|--------|
| `--shadow-sm` | Soft 1px lift |
| `--shadow` | Card elevation |
| `--shadow-lg` | Modal / hero depth |
| `--radius-sm` | `10px` |
| `--radius` | `14px` |
| `--radius-lg` | `18px` |
| `--radius-xl` | `24px` |

### Legacy aliases

`--teal`, `--teal-dark`, `--teal-soft` map to `--accent*` for older class names. **New code should use `--accent*`.**

---

## 3. Typography rules

| Role | Weight | Notes |
|------|--------|--------|
| Page / hero H1 | **800** | On navy → `color: var(--on-navy)` only |
| Section H2 / H3 | **700** | |
| Body | **500–600** | Default body 500; controls 600 |
| Muted / meta | **500** | `var(--muted)` |
| Labels / badges | **700** uppercase, tracked | |
| Code | Mono **500** | On navy wells use `on-navy-muted` |

Do not use thin/light weights for primary UI.

---

## 4. Component rules

| Surface | Rules |
|---------|--------|
| **Buttons primary** | `bg-accent` + `text-on-accent`; hover `accent-hover` |
| **Buttons on navy** | Same accent fill; outline uses white/20 border + on-navy text |
| **Cards** | `panel` + `line` border + `shadow-sm` or `shadow` |
| **Inputs / select** | `panel` fill, `line` border; focus → accent border / focus-ring |
| **Toasts / modals** | `panel` + `shadow-lg`; status via left border semantic colour |
| **Tables** | Header `surface`; rows `line` dividers |
| **Spinners** | Accent colour; respect `prefers-reduced-motion` |
| **Hardcoded hex** | **Forbidden** on product pages (landing, dashboard, primitives) |

Contrast: titles on navy must use `--on-navy`, never `--muted` or `--ink`.

---

## 5. Persistence & defaults

| Item | Value |
|------|--------|
| Storage key | `netpay_theme` |
| Product default | `ledger` |
| Apply | `document.documentElement.dataset.theme` / `data-theme` |
| Pre-paint | Inline script in `frontend/app/layout.tsx` |

`/theme` may still switch lab themes for comparison; product chrome must assume Ledger tokens in `:root`.

---

## 6. Agent checklist (anti-drift)

Before shipping UI:

1. Read **this file** and `frontend/app/globals.css` `:root` / `data-theme="ledger"`.
2. No new raw `#hex` in JSX for brand colours — only tokens.
3. Do not reintroduce green-teal-as-primary unless Theme.md is revised and approved.
4. Keep SEO/metadata changes separate from palette play.
5. Prefer existing primitives: `Button`, `Card`, `Badge`, `Container`, `Section`.
6. Dashboard remains noindex until identity is live; still use Ledger tokens.

---

## 7. Files to touch when changing the theme

| File | Why |
|------|-----|
| `Theme.md` | This SOT (update first in the PR description) |
| `frontend/app/globals.css` | Token values |
| `frontend/lib/theme.ts` | Ids, meta, default |
| `frontend/app/layout.tsx` | `themeColor`, default `data-theme`, init script |
| `frontend/components/ui/*` | Primitives if API changes |
| `frontend/app/theme/*` | Lab only |

---

## 8. Out of scope (v1)

- Full dark-mode product theme (may be a later Theme.md revision)
- Restoring the pruned Vite SPA visual system
- Merchant-branded white-label colours per tenant


---

## 9. Type scale & layout tokens (globals.css)

All product UI sizing should come from CSS variables in `frontend/app/globals.css`:

| Token | Role |
|-------|------|
| `--text-xs` … `--text-display` | Font sizes (`clamp` on large steps for responsiveness) |
| `--weight-*` | Font weights |
| `--leading-*` / `--tracking-*` | Line height / tracking |
| `--space-page-x` / `--space-section-y` | Responsive page padding |

Prefer semantic classes: `.np-display`, `.np-h1`, `.np-h2`, `.np-h3`, `.np-lead`, `.np-body`, `.np-small`, `.np-label`, `.np-chrome`, `.np-panel`, `.np-page`, `.np-section`, `.np-container`, `.np-footer`, `.np-skip-link`.

**Exceptions:** `opengraph-image.tsx` and `icon.svg` require literal colors for static image generation; keep them aligned with Ledger hex values documented above.

## 10. Theme lab (local only)

`/theme` and `ThemeLab.tsx` are for local comparison and are **gitignored**. Do not commit them. Product default remains Ledger via `:root`.
