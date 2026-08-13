# HITRAG Frontend — HIT Knowledge Assistant

**HITRAG** is the AI knowledge assistant frontend interface for the Harare Institute of Technology (HIT). It provides an authoritative, document-grounded chat and query experience with source citations and access-tier enforcement.

> [!IMPORTANT]
> **Frontend Only Notice**: This repository contains the Next.js UI frontend only. It calls a separate FastAPI backend for all retrieval and generation. No RAG logic, embeddings, or LLM calls belong in this app.

---

## 🛠️ Stack & Technologies

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom design tokens
- **Fonts**: Space Grotesk (`--font-display`), Inter (`--font-body`), IBM Plex Mono (`--font-mono`) via `next/font`

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher

### Installation & Development

```bash
# Install dependencies
npm install

# Run the local development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the living style guide homepage.

---

## 🎨 Design System Tokens & Namespace

Custom tokens defined under the `hit` namespace in `tailwind.config.ts`:

| Token | Hex / Definition | Usage |
| :--- | :--- | :--- |
| `hit.blue` | `#0B2E5C` | Primary brand color, headers, buttons |
| `hit.blue-dark` | `#071D3D` | Dark state, hover, high-contrast text |
| `hit.amber` | `#E8A33D` | Grounded status rule, citation highlight accent |
| `hit.bg` | `#F7F8FA` | Global background surface |
| `hit.surface` | `#FFFFFF` | Card surface, message bubble surface |
| `hit.border` | `#DDE3EA` | Border lines, dividers |
| `hit.text-primary` | `#16202B` | Body copy, heading text |
| `hit.text-secondary` | `#5B6B7A` | Metadata, timestamps, captions |
| `hit.success` | `#2F7D5E` | Verification badges, grounded status |
| `hit.warning` | `#B5482D` | Ungrounded/restricted status rule, alert state |

---

## 📂 Mapping Files to Future UI Screens

As development continues beyond this design foundation, map screens and components to the following proposed structure:

| Screen / Feature | Key Files / Paths | Description & Guidelines |
| :--- | :--- | :--- |
| **Living Style Guide** | [app/page.tsx](file:///Users/tinochan06/hitrag/app/page.tsx) | Homepage displaying tokens, font scale, and component samples |
| **Login / Authentication** | [app/login/page.tsx](file:///Users/tinochan06/hitrag/app/login/page.tsx), [components/ui/hitrag-wordmark.tsx](file:///Users/tinochan06/hitrag/components/ui/hitrag-wordmark.tsx) | Student/Staff HIT credential login interface with split navy desktop panel & trust strip |
| **Chat Interface** | [app/chat/page.tsx](file:///Users/tinochan06/hitrag/app/chat/page.tsx), [app/chat/[conversationId]/page.tsx](file:///Users/tinochan06/hitrag/app/chat/%5BconversationId%5D/page.tsx) | Primary student query canvas, grouped conversation sidebar, auto-growing input, ungrounded fallback state |
| **Citation Drawer / Panel** | [components/chat/citation-drawer.tsx](file:///Users/tinochan06/hitrag/components/chat/citation-drawer.tsx) | Side panel displaying full source document excerpts on click |
| **Restricted State** | [components/ui/grounding-rule.tsx](file:///Users/tinochan06/hitrag/components/ui/grounding-rule.tsx) | Ungrounded / restricted access banner when user lacks document tier |
| **Admin View** | `app/admin/page.tsx`, [components/ui/citation-tag.tsx](file:///Users/tinochan06/hitrag/components/ui/citation-tag.tsx) | Management dashboard for document tier permissions and ingestion status |
| **Empty State** | `components/chat/empty-state.tsx` | Initial prompt suggestions and welcome guide for new sessions |
# hitrag
