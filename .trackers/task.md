# Task: Professional home + Lucide icons + observability

**Branch:** feat/lucide-professional-home → **dev**  
**Related:** follow-up to merged #46 (home/logging/outbound audit)

## Goals
- [x] Replace emoji nav/header with **lucide-react** icons
- [x] Professional Home: quiet copy, stats, recent payments, single suggested next step (not shouty checklist)
- [x] Top bar actions with icons
- [x] package.json dependency `lucide-react`

## Prior (#46) still in scope context
- [x] DEBUG logging, no noise filter
- [x] outbound_requests audit for Daraja
- [x] register-urls error detail
- [x] Home as landing; System status at `/status`

## Verify
- [ ] `npm run build` (tsc + vite) with lucide-react
- [ ] Visual: sidebar + header + home on light/dark
