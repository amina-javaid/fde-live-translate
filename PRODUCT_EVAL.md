# Product Evaluation — Live Translate

- **Student:** Amina Javaid
- **Date:** 2026-07-13
- **Video demo:** [FDE Live Translate Demo](https://www.loom.com/share/570ca0ee658245469062c329159d47f9)
- **LLM provider / model:** OpenAI / `gpt-4o-mini`
- **Backend target:** benchmark run locally at `http://localhost:8787`; live-website test against the deployed gateway at `https://fde-translate-gw-aj.fly.dev` (AI service private at `fde-translate-ai-aj.internal:8000`)

## Verdict

> This is shippable as an MVP. The product does exactly what it promises: the provided widget lights up on a real, third-party site and flips the page into fluent Mexican Spanish, with prices, SKUs, and model codes left intact. The strongest part is the caching layer — a two-tier (memory + SQLite) cache that survives restarts, delivers a ~56× speedup on repeats (hit p95 23 ms vs miss p95 1299 ms), holds a 75% hit rate under load with **zero errors**, and cuts projected monthly LLM spend by ~75%. Correctness is handled the right way: on an LLM error the service **fails loud** (HTTP 5xx) rather than silently serving English, and a single request ID is traceable across both services' logs. The weakest points are operational, not functional: cache-miss latency (~1.3 s p95) is inherited from the LLM provider and is the main user-visible wait; the cost figures below use the repo's placeholder Sonnet pricing, so real `gpt-4o-mini` cost is materially lower; and page coverage of lazily/dynamically-loaded content on very large sites was not exhaustively audited.

**Rubric score (from `eval/report.json`):** 70 / 70 auto (+ 30 manual)

Auto breakdown: widget_lights_up 15/15 · caching_correctness 20/20 · performance_sla 15/15 · logging_observability 10/10 · service_separation_contract 10/10.

## 1. Performance & cost (from `benchmark/bench.py`, clean cold→warm run)

| Metric | Result | SLA | Pass? |
|---|---|---|---|
| Cache hit p95 | 23.4 ms | ≤ 60 ms | ✅ |
| Cache miss p95 | 1299 ms | ≤ 3500 ms | ✅ |
| Cache hit rate | 75.0 % | ≥ 60 % | ✅ |
| Throughput | 703.5 req/s | ≥ 20 | ✅ |
| Error rate | 0.0 % | ≤ 1 % | ✅ |
| Cost per miss | $0.000157 | — | — |
| Monthly savings from cache | $58.95 | — | — |

**SLA gate: ✅ ALL SLAs MET.** Cache miss p50/p95 = 1070/1299 ms; cache hit p50/p95 = 4/23 ms (≈56× speedup).

> **Cost caveat:** `benchmark/sla.json` ships with **placeholder Anthropic `claude-sonnet-4-6` pricing ($3/$15 per Mtok)**. This product actually runs on OpenAI `gpt-4o-mini` (~$0.15/$0.60 per Mtok), so real cost is roughly **15–20× lower** than the numbers above — i.e. genuine monthly savings are larger in absolute cache-avoided calls but smaller in dollar terms. `sla.json` is on the do-not-edit list, so it was left unchanged; interpret the dollar figures as an upper bound.

## 2. Live-website test

- **Site tested:** https://www.homedepot.com (real, third-party, content-rich site)
- **Translated whole page?** Yes — loaded via the Chrome extension (Load unpacked → `extension/`) pointed at the production gateway `https://fde-translate-gw-aj.fly.dev`. Clicking **Translate page** flipped the visible page into Mexican Spanish with layout intact.
- **Coverage gaps:** Static page text translated cleanly. Lazily/dynamically-loaded content that renders after the translate pass (e.g. content revealed on scroll) and text baked into images are not covered — expected for a one-shot DOM pass.
- **Cache on re-translate:** Restore → Translate again returns instantly with `cached:true`. Verified directly against production: first call `cached:false` ~3.0 s, identical repeat `cached:true` 0 ms.
- **Resilience:** The **console-snippet** loader is blocked by Home Depot's strict Content-Security-Policy (expected, and documented in the brief) — the **Chrome extension** path is used instead and works, because it injects via the extension context and proxies through the gateway. No layout breakage; page remained usable.
- **Screenshots:** captured live by the student during the demo — attach before/after to the submission (also shown in the video).

### Sample translations (6–8) — real output from the deployed product

| Original (EN) | Translation (es-MX) | Numbers/prices/codes kept? | OK? |
|---|---|---|---|
| Add to Cart | Agregar al carrito | n/a | ✅ (es-MX "agregar", not Castilian "añadir") |
| Free delivery on orders over $45.00 | Envío gratis en pedidos mayores a $45.00 | $45.00 ✅ | ✅ |
| In stock at your store — 12 available (SKU 1001234567) | En stock en tu tienda — 12 disponibles (SKU 1001234567) | 12, SKU 1001234567 ✅ | ✅ (informal "tu" = es-MX) |
| Milwaukee M18 FUEL 18-Volt Cordless Drill, model 2904-20 — $199.00 | Taladro inalámbrico Milwaukee M18 FUEL de 18 voltios, modelo 2904-20 — $199.00 | model 2904-20, $199.00 ✅ | ✅ |
| Sign in for faster checkout and order tracking. | Inicia sesión para un pago más rápido y seguimiento de pedidos. | n/a | ✅ |
| 4.5 out of 5 stars (2,341 reviews) | 4.5 de 5 estrellas (2,341 reseñas) | 4.5, 5, 2,341 ✅ | ✅ |
| Buy 2, save 15% on select power tools. | Compra 2, ahorra 15% en herramientas eléctricas seleccionadas. | 2, 15% ✅ | ✅ |
| Estimated arrival: Tuesday, July 21 | Fecha estimada de llegada: martes 21 de julio | 21 ✅ | ✅ |

## 3. Dimension scorecard

| Dimension | Pass / Partial / Fail | Evidence |
|---|---|---|
| Translation accuracy | Pass | 8/8 samples fluent and correct; matches source meaning |
| Mexican-Spanish register (es-MX) | Pass | "agregar al carrito" (not Castilian "añadir"), informal "tu tienda"; prompt pins es-MX explicitly |
| Numbers / prices / codes preserved | Pass | $45.00, $199.00, model 2904-20, SKU 1001234567, 15%, 2,341 all preserved verbatim |
| Page coverage | Pass (with note) | Full static page translated on homedepot.com; dynamic/lazy content and image text not covered |
| Cache effectiveness | Pass | 75% hit rate, 56× speedup, survives restart (disk hit after reboot), production repeat = 0 ms |
| Latency vs SLA | Pass | All 5 SLA thresholds met; hit p95 23 ms, miss p95 1299 ms |
| Error handling (no silent English) | Pass | LLM errors propagate as HTTP 5xx (verified); no try/except returning source text |
| Resilience on a real site | Pass | Works via extension on strict-CSP site; console-injection CSP block handled by using the extension path |
| UX polish | Pass | Provided widget unmodified; backend URL configurable in extension popup; `/health` reports nested AI status |

## 4. Top fixes before shipping

1. **Correct the cost model** — update `benchmark/sla.json` `cost_model` to OpenAI `gpt-4o-mini` published rates so the reported dollar figures reflect the real provider (currently placeholder Sonnet pricing).
2. **Broaden dynamic-content coverage** — re-translate on DOM mutations (e.g. a `MutationObserver`) so content that loads after the initial pass (infinite scroll, tabs) is also translated.
3. **Production hardening (stretch goals)** — add rate limiting (429), a cache TTL + `POST /clear-cache` endpoint, and a GitHub Action for automated Fly deploys. Cache-miss latency (~1.3 s) could be masked with response streaming.

---

### Deployment

- **Public gateway:** https://fde-translate-gw-aj.fly.dev (HTTPS, 2 machines, HA)
- **AI service:** private on Fly's internal network (`fde-translate-ai-aj.internal:8000`), no public IP — the OpenAI key lives only as a Fly secret, never at the browser edge
- **Source:** https://github.com/amina-javaid/fde-live-translate
- Both services deploy from Docker (`Dockerfile.ai`, `Dockerfile.gateway`) via `fly.ai.toml` / `fly.gateway.toml`; SQLite cache persisted on a Fly volume.
