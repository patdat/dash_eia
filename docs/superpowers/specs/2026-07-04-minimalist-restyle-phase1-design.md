# Minimalist Restyle — Phase 1: Design-System Foundation + Navbar

**Date:** 2026-07-04
**Status:** Design (awaiting approval)
**Repo:** `dash_eia`
**Reference:** `quant_dash` (`/Users/patrickmarable/Documents/GitHub/quant_dash`)

---

## Goal

Adopt `quant_dash`'s minimalist, low-color visual language in `dash_eia`, and
begin simplifying the codebase — starting with the design-system foundation and
the sidebar/navbar, since every page shares the CSS, the color module, and the
shell. All work happens in a dedicated git worktree.

This is **Phase 1 of a 4-phase program** (see *Program Context* below). It is
independently shippable: after Phase 1 the whole app already reads as the new
minimalist system, even though page bodies are cleaned up in later phases.

## Program Context (decomposition)

The user requested a full restyle (chrome **and** charts) plus a deep structural
refactor of the 49-page / 5-module codebase. That is too large for one spec, so
it is sequenced into four sub-projects, each with its own design → plan → build,
all landing in one shared worktree:

1. **Phase 1 (this spec)** — Design tokens, navbar rewrite, chart palette, base
   CSS reskin.
2. **Phase 2** — Chrome & inline-style cleanup: remove gradient hero / dark
   tabs, standardize page shells, migrate the ~19 pages that hardcode hex onto
   the new tokens.
3. **Phase 3** — Page-pattern consolidation: collapse the duplicated WPS
   (`page2_*`), DPR (`page3_*`), and CLI (`page5_*`) pages onto shared
   `create_layout` / `create_callbacks` modules.
4. **Phase 4** — Routing & module simplification: replace the 38-branch routing
   chain with a registry; remove dead code.

Phases 2–4 are out of scope for this spec and get their own specs later.

---

## Design Decisions (confirmed)

- **Restyle depth:** chrome **and** charts.
- **Cleanup depth:** deep refactor overall; Phase 1 carries the low-risk cleanup
  that naturally accompanies the token/navbar work.
- **Multi-year chart palette:** *accent + grays* — current/most-recent year in
  the blue accent, prior years in progressively lighter grays, 5-year band in a
  shaded gray.

---

## Current State (what we are replacing)

- **Fonts:** `Montserrat` + 8 other families loaded twice — once via 9
  `external_stylesheets` CDN entries in `src/app.py`, again via `@import` at the
  top of `assets/styles.css`. FontAwesome loaded via CDN `@import`.
- **Palette:** six bright brand colors (`RED #EC002B`, `BLUE #00ADEF`, `GREEN`,
  `ORANGE`, `PURPLE`) centralized in `src/utils/colors.py`, consumed by the graph
  modules and (Phase 2's problem) hardcoded inline in ~19 pages.
- **Chrome:** heavy shadows (`--shadow-soft/-hover`), hover-lift
  (`translateY(-4px)`), large radii (12–18px), radial-gradient `.page-hero`,
  dark tab bars.
- **Sidebar:** ~200 lines of hand-written inline `html.Div` markup in
  `src/index.py`; dark background (`#4C4D4E`); 46px white brand name; no icons;
  **five near-identical collapse callbacks** (`toggle_collapse_page_2..6`); one
  nav-link with an inline color override.

## Target State (quant_dash idioms)

- **Fonts:** local `Inter` variable font via `@font-face`; base 13px; local
  FontAwesome. No font CDN calls.
- **Palette:** neutral surfaces + a single muted-blue accent (`#0072ab`); bright
  `#00ADEF` retained only as `--brand-blue` for the logo; muted semantic tones.
- **Chrome:** flat (no shadows, no hover-lift), small radii (6–8px), bordered
  surfaces, no gradient hero.
- **Sidebar:** light background, brand lockup (small logo + 15px name), section
  icons + chevrons, active-link left accent border; driven by a declarative
  config through one reusable builder and **one** pattern-matching collapse
  callback.

---

## Scope of Work

### A. Design tokens & base CSS — `assets/styles.css`

1. Replace the `:root` block with quant_dash's token set (neutrals, `--accent
   #0072ab`, `--accent-hover`, `--accent-soft`, `--brand-blue #00ADEF`, muted
   `--positive/--negative/--warning`, `--radius-lg 8px`, `--radius-md 6px`,
   `--sidebar-width 15rem`). No `--shadow-*` tokens.
2. Remove the 9 Google-font `@import` lines and the FontAwesome CDN `@import`.
   Add an `@font-face` for local Inter and reference local FontAwesome CSS.
3. `body` → Inter, 13px, `--text`, antialiased.
4. Reskin the shared component rules (`.metric-card`, `.feature-card`,
   `.surface-card`, `.page-hero`, `.page-title/eyebrow/summary`, alerts,
   buttons, tabs) to flat/bordered/no-shadow/no-lift, matching quant_dash.
5. **Keep** the EIA-specific layout rules (`.eia-weekly-graph-container`,
   `.eia-dpr-graph-container`, `.graph-container`, date-picker, AG-Grid theme,
   WPS/DPR tab layouts) but reskin: remove heavy `box-shadow`, soften/neutralize
   colors, align radii to tokens. Preserve grid dimensions and behavior.
6. Delete `assets/styles.css.bak`.

### B. Fonts & external stylesheets — `src/app.py`

1. Remove the 9 Google-font entries from `external_stylesheets` (keep
   `dbc.themes.BOOTSTRAP`).
2. Copy local assets from quant_dash into `dash_eia/assets/`:
   - `fonts/InterVariable.woff2`
   - `fontawesome/css/all.min.css` + `fontawesome/webfonts/*`
3. Fonts/icons load via `assets/styles.css` (`@font-face`, local FA import) —
   Dash auto-serves the `assets/` folder.

### C. Navbar rewrite — new files + `src/index.py`

1. **New `src/config/navigation.py`** — `BRAND` dict + `NAV_SECTIONS` list
   describing the existing six groups with their **existing hrefs unchanged**:
   - Home (`/home`)
   - EIA Weekly → Headline, Graphing, Stats Table, PADD Analysis, Cushing
     Analysis, Runs Analysis, Balance Analysis, Advanced Time Series
   - EIA DPR → DPR Charts, DPR Table, Efficiency Heatmap, DUC Analysis,
     Productivity Matrix Analysis, Performance Radar Analysis
   - EIA STEO → six TBD links (`/steo/tbd1..6`)
   - EIA CLI → Market Overview … Market Alerts (10 links)
   - EIA PSM → six TBD links (`/psm/tbd1..6`)

   Each section gets `id`, `label`, a FontAwesome `icon`, `initial_open: True`,
   and its `links`.
2. **New `src/components/shell.py`** — port `build_sidebar(brand, nav_sections)`
   and `_nav_link()` from quant_dash (same class names the CSS targets:
   `brand-lockup`, `brand-logo`, `brand-name`, `nav-section-left`,
   `nav-section-icon/-label/-chevron`, `sidebar-button page-button open/closed`,
   `nav-link`, `nav-link-child`, `nav-icon`). Toggle IDs use the
   pattern-matching form `{"type": "nav-toggle", "index": section_id}` and
   collapses `{"type": "nav-collapse", "index": section_id}`.
3. **`src/index.py`:**
   - Replace the inline `sidebar = html.Div([...])` with
     `build_sidebar(BRAND, NAV_SECTIONS)`.
   - Delete the five `toggle_collapse_page_2..6` callbacks and add **one**
     pattern-matching callback (ported from quant_dash) that flips
     `is_open`/className for the triggered section.
   - **Do not touch** `display_page` (routing) or the page imports — routes stay
     identical. The `data-store` `dcc.Store` stays in `app.layout`.
4. Drop the inline logo/brand styles and the inline nav-link color override —
   styling now lives entirely in CSS.

### D. Chart palette — `src/utils/colors.py` + graph modules

1. Retune `colors.py` to the muted scheme while **keeping the same public names**
   (`YEAR_COLORS`, `MA_COLORS`, `EVOLUTION_COLORS`, `CHART_SEQUENCE`,
   `POSITIVE`, `NEGATIVE`, colorscales) so importers keep working:
   - Accent blue `#0072ab`; grays `#5c6b7f`, `#8b97a6`, `#b8c0cb`; muted red
     `#c8102e`; muted green `#1a7f42`; band gray from `--hover`/`--border`.
   - `YEAR_COLORS` → `[accent, gray1, gray2, gray3, gray4]` (current year = accent,
     priors graying out).
   - `MA_COLORS`, `EVOLUTION_COLORS`, `CHART_SEQUENCE` → accent + grays with a
     single muted red/green only where semantics demand it.
   - Keep colorscale *names* but prefer neutral-friendly ones; leave
     `COLORSCALE_EFFICIENCY` as-is unless it clashes (Phase 2 can revisit).
2. Update plotly **layout chrome** in `graph_line.py`, `graph_seag.py`,
   `chart_dpr.py`, `graph_optionality.py`: white `paper_bgcolor`/`plot_bgcolor`,
   light gridlines (`--border`), Inter font, muted axis/legend text. These
   modules already import `colors.py`, so series colors inherit automatically.
3. Pages that hardcode hex are **Phase 2** — not touched here beyond what
   `colors.py` propagates.

---

## Out of Scope (Phase 1)

- The 38-branch `display_page` routing chain (Phase 4).
- Migrating the ~19 pages with inline hex onto tokens (Phase 2).
- Page-pattern consolidation of `page2_*` / `page3_*` / `page5_*` (Phase 3).
- Any change to data loading, downloads, or page logic/behavior.

---

## Risks & Mitigations

- **Navbar regression** (collapse/active states): mitigated by porting
  quant_dash's proven builder + single callback verbatim and keeping all hrefs
  identical; verify collapse + active highlight on load.
- **Chart legibility** with accent+grays when many years overlap: mitigated by
  reserving the accent for the current year and keeping the legend; revisit
  shade steps during verification if two priors are hard to tell apart.
- **FontAwesome icon names**: the ported builder uses `fa-solid` classes;
  confirm local FA `all.min.css` includes the chosen section icons.
- **Double font loading leftover**: ensure both `app.py` CDN entries **and** the
  CSS `@import`s are removed, or fonts silently keep loading from CDN.

## Verification

1. Create worktree, install deps if needed, run `python run.py` (port 8052).
2. Load `/home` and at least one page per section (Weekly, DPR, STEO, CLI, PSM).
3. Confirm: light sidebar renders with icons + chevrons; each section collapses
   independently; the active link shows the accent border; no console 404s for
   fonts/FA; charts render with accent+gray palette on white backgrounds.
4. Grep to confirm no remaining Google-font CDN references in `app.py` or
   `styles.css`.

## Definition of Done (Phase 1)

- App runs; all existing routes reachable from the restyled sidebar.
- No CDN font/icon dependencies; local Inter + FA in `assets/`.
- `styles.css` reskinned to flat minimalist tokens; `.bak` deleted.
- Sidebar built from `navigation.py` + `shell.py` via one collapse callback.
- `colors.py` + four graph modules render the muted accent+gray palette.
- Changes committed on the worktree branch.
