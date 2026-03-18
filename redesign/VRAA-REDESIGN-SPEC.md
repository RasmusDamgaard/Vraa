# vraa.org Redesign — Implementation Spec

## Overview

Redesign of **vraa.org**, a Danish family summer house (sommerhus) website. The site serves as a practical information hub for family members who share a holiday house on a Danish island. Current site is plain HTML with no styling or structure.

**Target users:** Family members arriving at or departing from the house, coordinating bookings, and sharing messages.

**Tech stack:** Single-page static HTML/CSS/JS. No build step. Google Fonts. localStorage for demo persistence — architecture should allow easy swap to a backend (Firebase/Supabase) later.

---

## Design System

### Aesthetic Direction
Warm Scandinavian minimalism. Think sommerhus, not SaaS. The site should feel like a *place*, not a document.

**Inspiration references:**
- scopecph.com — Danish minimalism, bold hero, quiet navigation, generous whitespace
- jakeknapp.com — clean personal site, centered content, "say enough then get out of the way"
- gwern.net — functional minimalism proving text-heavy content can be beautiful with good typography

### Color Palette
```css
--sand: #F5F1EB;          /* Page background */
--sand-dark: #EDE8DF;      /* Subtle surface */
--cream: #FDFCF9;          /* Card backgrounds */
--sage: #7A8B6F;           /* Primary accent */
--sage-light: #E8EDE4;     /* Light accent fill */
--sage-dark: #5C6B53;      /* Dark accent / hover */
--driftwood: #8B7D6B;      /* Muted text */
--driftwood-light: #C4B9AA; /* Borders, hints */
--charcoal: #2C2A26;       /* Primary text */
--charcoal-soft: #4A4740;  /* Secondary text */
--ocean: #6B8A9E;          /* Info / links */
--ocean-light: #E3ECF1;    /* Info fill */
--coral-accent: #C4826E;   /* Warning / departure */
--coral-light: #F3E4DE;    /* Warning fill */
```

No pure black-on-white. Use off-white (`--sand`) backgrounds and `--charcoal` text for warmth.

### Typography
- **Headings:** DM Serif Display (serif, warm, editorial)
- **Body:** DM Sans (clean sans-serif, weight 300 for body, 400/500 for emphasis)
- **Line height:** 1.65 body, 1.15 headings
- **Load from:** `https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300;1,9..40,400`

### Components
- **Cards:** `background: var(--cream)`, `border: 1px solid var(--border)`, `border-radius: 12px`, subtle box-shadow
- **Buttons primary:** `background: var(--sage)`, white text, 8px radius
- **Buttons outline:** transparent bg, 1px border, hover fills sand
- **Callout boxes:** Sage-light bg for info, `#FBF3E4` for warnings
- **Transitions:** `0.25s cubic-bezier(0.4, 0, 0.2, 1)` globally

---

## Site Structure & Navigation

### Layout
- Max content width: **900px**, centered
- Padding: 1.5rem sides (1rem on mobile)
- All content in a single scrollable page with section anchors

### Hero Section
- Full-width, 75vh height (60vh mobile)
- Background: photo of the house/island (placeholder gradient for now)
- Dark gradient overlay at bottom for text legibility
- Content: "Velkommen til Vraa" heading, short subtitle
- Subtle CSS grid pattern overlay at low opacity as placeholder texture

### Quick Actions (4 tiles below hero)
Sits overlapping the hero bottom with negative margin. Grid of 4 equal cards:

| Tile | Icon | Label | Links to |
|------|------|-------|----------|
| Ankomst | ↗ | "Ankomst" / "Nøgler & velkomst" | #ankomst |
| Booking | 📅 | "Booking" / "Kalender & reserver" | #booking |
| Beskeder | 💬 | "Beskeder" / "Opslagstavle" | #opslagstavle |
| Afrejse | ↙ | "Afrejse" / "Tjekliste" | #afrejse |

On mobile: 2×2 grid, hide sublabels on very small screens.

### Sticky Navigation Bar
- Sticky top, blurred sand-colored background (`backdrop-filter: blur(16px)`)
- Horizontally scrollable on mobile
- Items: **Praktisk · Ankomst · Booking · Opslagstavle · Afrejse · Rejse · Regnskab · Kontakt**
- Active state: underline in sage color, tracked via IntersectionObserver scroll spy
- Opslagstavle link shows a small coral badge with message count

---

## Sections (in order)

### 1. Praktisk Info (`#praktisk`)
Grid of 4 info cards (2 columns, 1 on mobile):

| Card | Icon bg | Content |
|------|---------|---------|
| Nøgler | sage | Contact Troels, key locations in chatol drawer |
| Affald | ocean | Sort spand = mixed, Grøn = compost, paper in fireplace |
| Den blå ringordner | coral | On the chatol, contains phone numbers + house info |
| Sæsonstart | sand | First users get rent discount for deep cleaning |

### 2. Ankomst (`#ankomst`)
- Expandable `<details>` sections: "Adgang til huset", "Gæster og besøgende"
- First item open by default
- Callout box: reminder about den blå ringordner

### 3. Booking & Kalender (`#booking`) — NEW
**Calendar component:**
- Month grid, Monday-start, Danish day/month names
- Navigation: ← → arrows + "I dag" button
- Days show colored booking dots per person
- Click a day → pre-fills the booking form with that date + 7 days
- Past days styled muted
- Today gets a dark circle on the day number
- Color legend below calendar showing name → color mapping

**Booking colors:** Auto-assigned per person name via hash. 5 color slots:
```
sage (#7A8B6F), ocean (#6B8A9E), coral (#C4826E), purple (#9B8BB4), driftwood (#8B7D6B)
```

**Upcoming bookings list:**
- Cards with a colored left bar, name, date range, guest count, optional note
- Delete button (×) with confirmation dialog

**Booking form:**
- Fields: Navn (text), Antal gæster (number, default 2), Ankomst (date), Afrejse (date), Bemærkning (optional text)
- Overlap detection: warns if dates conflict with existing booking, asks to confirm
- On submit: saves to storage, remembers user name for reuse

**Default demo data (3 bookings in current year's July/August).**

### 4. Opslagstavle (`#opslagstavle`) — NEW
**Compose box (top):**
- Textarea placeholder: "Skriv en besked til de andre..."
- Bottom bar: name input (140px) + "Slå op" button
- Name is remembered across sessions

**Post cards:**
- Avatar circle (initials, color-coded by name hash)
- Author name (bold), optional "📌 Fastgjort" label, relative timestamp
- Post body (pre-wrap whitespace)
- Action buttons: "Fastgør" / "Frigør" toggle, "Slet" with confirmation

**Sorting:** Pinned posts always on top, then reverse chronological.

**Timestamps in Danish:** "Lige nu", "5 min siden", "3t siden", "I går", "4 dage siden", "2 uger siden", then "15. mar" format.

**Default demo data:** 2 posts (one pinned from Troels about painted table, one from Mette about beach toys in the shed).

### 5. Afrejse (`#afrejse`)
- Warning callout about afregningsskema
- Interactive checklist (10 items) with custom-styled checkboxes
- Checked items: strikethrough + reduced opacity
- State persists in localStorage
- Reset button clears all

**Checklist items:**
1. Fej og støvsug overalt
2. Vask gulve
3. Tøm køleskab og fryser
4. Opvask — sæt på plads
5. Tøm alle skraldespande
6. Rengør badeværelse og toilet
7. Alle vinduer lukket og låst
8. Sluk lys og apparater
9. Lås hoveddør og skur
10. Udfyld afregningsskema

### 6. Rejse (`#rejse`)
Two expandable `<details>`: Færge og transport, Kørsel og parkering.

### 7. Regnskab (`#regnskab`)
Warning callout + sage-colored button linking to afregningsskema (placeholder href).

### 8. Kontakt (`#kontakt`)
Contact card for Troels: avatar circle with "T", name, role description, phone link.

---

## Data Architecture

### Storage Abstraction
All data access goes through a `STORAGE` helper:
```js
const STORAGE = {
  get(key, fallback) { /* reads localStorage('vraa-' + key) */ },
  set(key, val)      { /* writes localStorage('vraa-' + key) */ }
};
```

**Keys used:**
- `vraa-bookings` — array of `{ id, name, start, end, guests, note }`
- `vraa-posts` — array of `{ id, author, body, date, pinned }`
- `vraa-checklist` — array of booleans
- `vraa-username` — last used name (shared between booking + posts)

### Production Upgrade Path
Replace `STORAGE.get/set` with `fetch()` calls to a backend. No UI changes needed. Options: Firebase Realtime DB, Supabase, or a static JSON API on the hosting server.

---

## Responsive Behavior

| Breakpoint | Changes |
|------------|---------|
| > 700px | Full layout, 4-column quick actions, 2-col card grids |
| ≤ 700px | 2-col quick actions, 1-col card grids, single-col forms, smaller calendar cells |
| ≤ 440px | Quick action sublabels hidden |

Navigation bar: horizontally scrollable with hidden scrollbar on all sizes.

---

## Key UX Principles

1. **Task-oriented:** The two primary moments are "I just arrived" and "I'm leaving" — these get top-level quick action tiles
2. **Mobile-first:** Guests arrive with phone in hand on the ferry. Everything must be tappable and readable without zoom
3. **Scannable:** Collapsible sections, card-based layout, no walls of text
4. **Zero-auth:** No login. Name is self-reported and remembered locally. This is a family trust model
5. **All Danish:** UI labels, months, days, timestamps — everything in Danish

---

## Files to Produce

Single self-contained `index.html` with:
- Inline `<style>` block (all CSS)
- Inline `<script>` block (all JS)
- Google Fonts loaded via `<link>`
- No external dependencies, no build step
- Ready to deploy to any static hosting

---

## What to Replace Before Going Live

1. Hero background: swap CSS gradient for a real `background-image: url(...)` photo
2. Troels's phone number in the contact card
3. Afregningsskema link (currently `href="#"`)
4. Adjust default booking demo data or remove it
5. Adjust default message board posts or remove them
6. Consider adding a backend for shared persistence across devices
