---
name: mypens-release-checklist
description: >-
  Pre-release checklist for myPENS web (Next.js) and mobile (Expo). Build,
  lint, test, Prisma migrate status, env parity, smoke test /api/health and
  key flows on web + mypens-mobile. Use before Vercel prod deploy or mobile
  store build.
---

# myPENS release checklist

**Model tier: CHEAP**

Web: `Projects/mypens/`. Mobile: `Projects/mypens/mypens-mobile/`. Details: `Projects/mypens/docs/DEPLOY.md`.

## Preflight

```powershell
$web = Join-Path $PWD 'Projects\mypens'
$mobile = Join-Path $web 'mypens-mobile'
git -C $web check-ignore .env   # must be ignored — never commit secrets
```

## Web build gate

```powershell
cd $web
npx prisma migrate status
npm run lint && npm test && npm run build
```

Fix before deploy. On schema errors, read `prisma/schema.prisma` first.

## Env parity (Vercel Production + mobile)

Web `.env` vs Vercel: `DATABASE_URL`, `DIRECT_URL` (if in schema), `MOBILE_PENS_API_TOKEN`, optional `ANTHROPIC_API_KEY`, `STRIPE_*`.

Mobile `.env`: `EXPO_PUBLIC_SUPABASE_URL`, anon key, `EXPO_PUBLIC_PENS_API_TOKEN` must match web.

## Production DB

```powershell
cd $web
npx prisma migrate deploy
```

Cross-app once if needed: `Projects/cockpit/cross_app_sync_migration.sql`.

## Deploy web

Push `main` → Vercel, or `vercel --prod`.

## Smoke — web (prod URL)

- [ ] `GET /api/health` — `hasDatabaseUrl`, `hasMobileToken` as expected
- [ ] `/morning-brief` loads
- [ ] One sleep/weight/journal write updates `cross_app.daily_snapshot` (if enabled)
- [ ] Cockpit shows live row

Local dev: `npm run dev` → `http://localhost:5000`.

## Smoke — mobile

```powershell
cd $mobile
npm run typecheck && npm run start
```

- [ ] Session against prod Supabase
- [ ] One write syncs to web-visible data
- [ ] Bearer `/api/*` works when token set

## Done when

- [ ] Schema matches `prisma/migrations/`
- [ ] Vercel health green; mobile typecheck clean; one E2E write verified
- [ ] No open P0 in `memory/projects/mypens-master-roadmap.md` for this release

No production DB resets. Railway investing cron — separate check if touched.
