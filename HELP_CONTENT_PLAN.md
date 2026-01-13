# Help Content Surface-Awareness Plan

**Status: APPROVED** - Implementing Option C+ (Dynamic + Web Features Summary)

## Current State
The Help page at `terryann-ui/src/pages/Help.tsx` contains 21 FAQ items. Several are web-UI specific and would confuse CLI users.

## Analysis by Section

### Universal (Works for both Web & CLI)
These FAQs apply to both surfaces with no changes needed:

1. **What is TerryAnn?** ✅
2. **What information do I need to start?** ✅
3. **How long does journey generation take?** ✅
4. **What happens after I submit?** ✅
5. **What am I looking at in the journey map?** ✅
6. **What do the different stages mean?** ✅
7. **What are touchpoints?** ✅
8. **Why does TerryAnn make specific recommendations?** ✅
9. **What does "evidence-based" mean?** ✅
10. **What does the Market Profile show?** ✅
11. **What are behavioral scores?** ✅

### Web-Only (Builder Features)
These are exclusively web UI features - CLI doesn't have them:

12. **Can I modify the journey?** ⚠️ Web-only (Builder mode)
13. **How do I add nodes?** ⚠️ Web-only (right-click canvas)
14. **How do I remove nodes?** ⚠️ Web-only
15. **How do I move nodes around?** ⚠️ Web-only (unlock/drag)
16. **What are the layout options?** ⚠️ Web-only (horizontal/vertical toggle)
17. **What is the Impact Analysis panel?** ⚠️ Web-only
18. **How does version tracking work?** ⚠️ Web-only

### Needs Adaptation
These need surface-specific instructions:

19. **How do I create my first project?**
    - Web: "Click 'New Project' in the navigation..."
    - CLI: "Just describe what you want: 'Create an AEP journey for Miami'"

---

## Proposed Solution: Surface-Aware Sections

### Option A: Separate Sections
Reorganize into sections with clear headers:

```
## Getting Started
(universal content)

## Understanding Your Journey
(universal content)

## Using the Web Builder
(web-only content with clear "Web UI only" label)

## CLI Commands
(CLI-specific content)
```

### Option B: Inline Surface Tags
Add badges/tags to individual FAQs:

```
Can I modify the journey? [Web UI]
Yes. The Builder lets you add, remove, or modify touchpoints...

Note: CLI users can view journeys at terryann.ai to use the Builder.
```

### Option C: Dynamic Content (Recommended)
Pass a `surface` query param and conditionally render:

```
/help?surface=cli  → Shows CLI-relevant FAQs only
/help?surface=web  → Shows all FAQs
/help              → Shows all with surface badges
```

---

## Recommended Changes

### 1. Add Surface Parameter Support
```tsx
// Help.tsx
const searchParams = new URLSearchParams(window.location.search);
const surface = searchParams.get('surface'); // 'cli' | 'web' | null
```

### 2. Tag Each FAQ with Surface Applicability
```tsx
const faqs = [
  { id: 'what-is-terryann', surfaces: ['web', 'cli'], ... },
  { id: 'modify-journey', surfaces: ['web'], ... },
  { id: 'cli-commands', surfaces: ['cli'], ... },
];
```

### 3. Filter and Badge
- If `surface=cli`: Only show FAQs with `cli` in surfaces array
- If `surface=web`: Only show FAQs with `web` in surfaces array
- If no param: Show all, with `[Web UI]` or `[CLI]` badges on surface-specific items

### 4. Add CLI-Specific FAQs
New FAQs to add:
- **How do I use the CLI?** (installation, login, basic commands)
- **What commands are available?** (/help, /new, /clear, etc.)
- **Can I edit journeys from the CLI?** → "View and edit at terryann.ai"

### 5. Update Web-Only FAQs
Add note to Builder-related FAQs:
> "This feature is available in the web UI at terryann.ai. CLI users can create journeys and then open them in the web Builder for editing."

---

## Implementation Steps

1. **Refactor Help.tsx** to use a data-driven FAQ array with surface tags
2. **Add surface query param handling**
3. **Add CLI-specific FAQs**
4. **Update CLI's _fetch_help_content()** to pass `?surface=cli`
5. **Add visual badges** for surface-specific content when viewing all

---

## Questions for Adam

1. **Option preference**: Separate sections (A), inline tags (B), or dynamic filtering (C)?
2. **CLI FAQ depth**: How detailed should CLI-specific help be? Just commands, or full tutorials?
3. **Cross-surface callouts**: Should web-only FAQs say "open at terryann.ai" or just hide from CLI?
