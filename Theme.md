# NetPay visual system

`frontend/app/globals.css` is the canonical source for application theme tokens, typography, spacing, containers, and responsive breakpoints. Keep this document aligned with that stylesheet.

## Identity and modes

NetPay uses a calm navy-and-teal identity for its M-Pesa Daraja gateway. Light is the first-visit default; dark is an optional user-selected mode. Both modes use the same semantic token names across public pages and the authenticated dashboard shell.

| Field | Value |
|---|---|
| Light theme id | `light` |
| Dark theme id | `dark` |
| Default | `light` |
| Preference key | `netpay_theme` |
| Valid stored values | `light`, `dark` |
| Theme application | `document.documentElement[data-theme]` |
| First-paint restore | Inline script from `frontend/lib/theme.ts` in `frontend/app/layout.tsx` |

Unknown or unavailable stored values fall back to light. The theme preference is non-sensitive UI state only; do not store credentials, tokens, payment data, or user identifiers in it.

## Palette tokens

Use semantic variables from `frontend/app/globals.css`; do not introduce page-local palettes.

| Token | Light | Dark | Purpose |
|---|---|---|---|
| `--navy` | `#071e32` | `#071e32` | Brand chrome and dark feature surfaces |
| `--navy-soft` | `#0b2b43` | `#0b2b43` | Nested brand surface |
| `--accent` | `#06736a` | `#70dfc8` | Primary action and accent |
| `--accent-hover` | `#055d56` | `#93ebd8` | Hover/active action state |
| `--accent-soft` | `#dff5f0` | `#1a3f45` | Soft accent surface |
| `--ink` | `#10283e` | `#edf5f8` | Primary text |
| `--muted` | `#4c6273` | `#b5c6cf` | Supporting text |
| `--on-navy` | `#f7fbff` | `#f7fbff` | Primary text on navy |
| `--on-navy-muted` | `#c1d4de` | `#c1d4de` | Supporting text on navy |
| `--on-navy-accent` | `#70dfc8` | `#70dfc8` | Accent links on navy |
| `--on-accent` | `#ffffff` | `#062b38` | Text on accent actions |
| `--bg` | `#f5f8fa` | `#0b1722` | Page canvas |
| `--panel` | `#ffffff` | `#112331` | Cards and raised surfaces |
| `--surface` | `#edf3f5` | `#172c3a` | Recessed surfaces |
| `--line` | `#d5e0e5` | `#2b4351` | Default borders |
| `--line-strong` | `#adbec7` | `#456170` | Strong borders |
| `--focus-ring` | `#087f75` | `#8ce8d4` | Keyboard focus indicator |

Status colors use `--danger`, `--warn`, `--ok`, and `--info` with their matching `*-soft` surfaces. Legacy `--teal*` names remain aliases for compatibility; prefer `--accent*` in new code.

## Typography, shape, and layout

- Body copy is at least 16px; supporting text is at least 14px and labels at least 12px.
- Use `--np-text-*`, `--np-weight-*`, `--np-leading-*`, and `--np-tracking-*`, or semantic classes such as `.np-display`, `.np-h1`, `.np-h2`, `.np-lead`, `.np-body`, `.np-small`, and `.np-label`.
- Use `--radius-*`, `--shadow-*`, `--space-page-x`, and `--space-section-y` for consistent shape, elevation, and rhythm.
- Shared Tailwind breakpoints are declared in `@theme` in `frontend/app/globals.css`: `sm` 40rem, `md` 48rem, `lg` 64rem, `xl` 80rem, and `2xl` 96rem.
- Use `.np-container` and `.np-section` for shared page width and spacing. Components can define their own composition but should use the global breakpoints and semantic theme tokens.

## Component and accessibility rules

| Surface | Rule |
|---|---|
| Primary action | `--accent` fill and `--on-accent` text; use the semantic hover/focus states |
| Action on navy | Accent fill with sufficient text contrast; use `--on-navy` for surrounding text |
| Cards | `--panel` fill, `--line` border, and a shared `--shadow-*` |
| Inputs and controls | Theme-aware surface/border and a visible `--focus-ring` |
| Status | Pair semantic color with clear text or an icon; never rely on color alone |
| Motion | Respect `prefers-reduced-motion` |

Meet WCAG 2.2 AA contrast: at least 4.5:1 for normal text, 3:1 for large text, and 3:1 for meaningful control boundaries and graphics. Verify both themes, hover/focus states, and mobile layouts. Keep visible and accessible names aligned; preserve logical heading order and keyboard operation.

## Public site and search

The shared public header owns the theme toggle and navigation. Public pages use the same global theme as the dashboard shell. The `/theme-test/` route is a noindex visual check of the actual shared tokens and stays out of the sitemap.

Keep page titles, descriptions, structured data, and visible content accurate. Do not invent customer logos, metrics, prices, guarantees, rankings, or product capabilities. Do not infer payment success from STK initiation acceptance; distinguish provider evidence from the request acknowledgement. Do not add analytics or tracking without approval.

`frontend/app/opengraph-image.tsx` and `frontend/app/icon.svg` use literal colors because static image generation cannot read CSS variables; keep them visually aligned with the navy-and-teal identity.
