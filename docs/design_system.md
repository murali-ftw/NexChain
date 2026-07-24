# NEXTCHAIN Design System

This document is the canonical design specification for the frontend.

Every screen, component, page, and interaction must follow this document unless explicitly instructed otherwise.

Priorities:

1. Consistency over novelty.
2. Enterprise usability.
3. Accessibility.
4. Responsive layouts.
5. Reusable components.
6. Production-quality implementation.

1. Overall Visual Direction
"Aetheria Glass & Cyber-Tactile Accent"
Theme: Soft, luminous light-wash glassmorphism paired with tactile, high-contrast micro-interactive controls.
Vibe: Modern enterprise AI co-pilot—clean, spatial, breathable, and highly legible.
Core Concept: Semi-transparent frosted glass containers float over a subtle ambient pastel mesh background. High-impact primary controls (running SQL queries, adding context) feature dark, glossy, tactile textures with glowing spectrum borders.
2. Color Palette
Token Category	Hex / Value	Usage Description
Ambient Mesh BG	linear-gradient(135deg, #EBF1FF 0%, #F5ECFF 45%, #F8FAF9 100%)	Main app background behind glass panels
Glass Surface (Primary)	rgba(255, 255, 255, 0.65)	Nav dock, chat canvas, background panels
Glass Surface (Card)	rgba(255, 255, 255, 0.82)	Active chat cards, query history cards, input bar
Glass Highlight Border	rgba(255, 255, 255, 0.8) / rgba(200, 210, 230, 0.35)	Top and left subtle edge light reflection
Iridescent Accent Dark	#0F1117	Primary action button fill
Spectrum Glow Accent	linear-gradient(90deg, #FF007A, #00F0FF, #FFE600)	Border aura ring for primary execution button
Text Primary	#0F172A (Slate 900)	High-contrast body text, headings
Text Secondary	#475569 (Slate 600)	Descriptions, timestamps, metadata
Text Muted	#94A3B8 (Slate 400)	Placeholders, inactive state icons
Status: SLA Breached	#EF4444 (Bg: rgba(239,68,68,0.1))	SLA breach warnings, delete actions
Status: Connected/OK	#10B981 (Bg: rgba(16,185,129,0.1))	Backend status indicator, in-stock tag
3. Typography
Sans-Serif Font: Inter, -apple-system, BlinkMacSystemFont, sans-serif
Monospace Font (SQL/Logs): JetBrains Mono, Fira Code, monospace
Type Scale
Display Title (Hero / Welcome): 28px / 1.3 line-height | Weight: 700 (Bold)
Section Heading (Page Titles): 22px / 1.3 line-height | Weight: 600 (SemiBold)
Card / Table Header: 15px / 1.4 line-height | Weight: 600 (SemiBold)
Body Regular: 14px / 1.5 line-height | Weight: 400 (Regular) / 500 (Medium)
Caption / Metadata: 12px / 1.4 line-height | Weight: 500 (Medium)
Code / SQL Output: 13px / 1.6 line-height | Weight: 400 (Regular)
4. Spacing System
Based on an 8pt primary grid (with 4pt micro-steps):
3XS: 2px | 2XS: 4px | XS: 8px
SM: 12px | MD: 16px | LG: 24px
XL: 32px | 2XL: 48px | 3XL: 64px
5. Grid Layout & Shell Structure
+-----------------------------------------------------------------------------------+
|  [Left Navigation]   |              [Center Canvas Area]            | [Right Dock] |
|  240px Fixed         |              Flex 1fr (Min 600px)           | 320px Fixed  |
|                      |                                              |              |
|  * Supply Chain Logo |  Chat Header / Page Title                    |  Suggested   |
|  * Chat Nav Item     |  ------------------------------------------  |  Questions   |
|  * History Nav Item  |  Glass Chat Message Stream / Audit Table     |  Category 1  |
|  * Audit Nav Item    |                                              |  Category 2  |
|                      |  ------------------------------------------  |              |
|  [User Profile Pill] |  [ ( + Context ) [ Ask Question... ] (Send) ]|              |
+-----------------------------------------------------------------------------------+
6. Border Radius & Elevation
Border Radius
Badges / Tags / Chips: 8px
Inputs / Buttons / Table Rows: 12px
Cards / Floating Panels: 20px
Main App Shell Containers: 28px
Tactile Buttons / Spherical Actions: 9999px (Full Circle / Pill)
Shadows & Depth
Glass Elevation 1 (Quiet Cards):
0 8px 32px 0 rgba(31, 38, 135, 0.05), inset 0 1px 1px 0 rgba(255, 255, 255, 0.8)
Glass Elevation 2 (Floating Input / Active Cards):
0 12px 40px -8px rgba(15, 23, 42, 0.08), 0 0 0 1px rgba(255, 255, 255, 0.6)
Tactile 3D Gloss (Context '+' Button):
0 8px 20px -4px rgba(0, 0, 0, 0.25), inset 0 2px 3px rgba(255, 255, 255, 0.5)
Iridescent Primary Glow (Send Action):
0 0 20px 2px rgba(138, 43, 226, 0.35)
7. Core Component Specifications
A. Navigation Design (Left Dock)
Container: Floating glass sidebar (240px), backdrop-filter: blur(20px).
Active Navigation Item: Light translucent fill (rgba(59, 130, 246, 0.12)), sharp blue pill indicator (3px width) on left border, text color #2563EB.
Inactive Nav Item: Text color #64748B, smooth transition to soft white glass highlight (rgba(255, 255, 255, 0.5)) on hover.
Bottom Profile Section: Frosted glass capsule displaying username, green status LED indicator (#10B981 with subtle pulse animation), and logout text.
B. Suggested Questions & History Cards
Suggested Question Card (Right Panel):
Background: rgba(255, 255, 255, 0.75)
Border: 1px solid rgba(226, 232, 240, 0.7)
Hover: Subtle upward translation (translateY(-2px)), blue edge glow, background brightens to rgba(255, 255, 255, 0.95).
Query History Card:
Displays user prompt in bold title text, response summary snippet below, timestamp in muted Slate 400.
Right utility controls (Restore, Delete) styled as minimal glass buttons.
C. Tables (Audit Log View)
Table Wrapper: Large rounded glass card (20px radius) with backdrop-filter: blur(16px).
Header: Soft slate backdrop (rgba(241, 245, 249, 0.6)), uppercase 11px letter-spaced text (letter-spacing: 0.05em).
Rows: 1px solid rgba(226, 232, 240, 0.5) bottom border. Row hover effect applies subtle white highlight (rgba(255, 255, 255, 0.4)).
Badges (SLA Result):
Breached: Background rgba(239, 68, 68, 0.12), text #DC2626.
N/A: Background rgba(148, 163, 184, 0.12), text #64748B.
D. Buttons (Hierarchy & Styles)
Primary Action (Send / Execute Query):
Visual Inspiration: Dark Iridescent Style
Fill: Dark Charcoal/Black (#0F1117).
Border Ring: Multi-color rainbow iridescent halo glow (#FF007A, #00F0FF, #FFE600).
Text/Icon: Clean white.
Context / Tool Addition Button (+):
Visual Inspiration: Tactile Spherical Gloss Style
Shape: 40px x 40px rounded circle.
Texture: Dark glass gradient with top rim highlight and inset shadow giving a 3D spherical button effect.
Secondary Actions (Filter, Search, Refresh, Restore):
Light translucent glass pill (rgba(255, 255, 255, 0.8)), subtle slate border, dark text.
E. Forms & Inputs
Main Prompt Box (Bottom Chat Bar):
Fixed bottom floating glass pod (backdrop-filter: blur(16px)).
Houses the tactile + context button on the left, seamless borderless text area in center, and dark iridescent send button on the right.
Filter Dropdowns & Date Pickers:
White translucent glass surface, Slate 800 text, 3px light blue outline ring on focus state (#3B82F6).
F. Empty & Loading States
Zero State (New Chat):
Centered hero heading: "Ask a supply chain question"
Floating 3D frosted glass avatar/illustration companion.
Clean starter action cards positioned below header.
Loading / SQL Generation State:
Animated pulsing halo around the iridescent button.
Shimmer skeleton loaders over table responses and message text.
8. Animation Principles
Easing Curve: cubic-bezier(0.16, 1, 0.3, 1) (Fluid spring bounce).
Durations:
Button Hover / Active Press: 150ms
Card Hover / Focus Shift: 200ms
Glass Modal Fade-In / Expansion: 300ms
9. Design Tokens (JSON Specification)
JSON
{
  "color": {
    "bg": {
      "mesh": "linear-gradient(135deg, #EBF1FF 0%, #F5ECFF 45%, #F8FAF9 100%)",
      "glass-canvas": "rgba(255, 255, 255, 0.65)",
      "glass-card": "rgba(255, 255, 255, 0.82)",
      "glass-input": "rgba(255, 255, 255, 0.9)"
    },
    "border": {
      "glass-light": "rgba(255, 255, 255, 0.8)",
      "glass-subtle": "rgba(200, 210, 230, 0.35)",
      "focus-ring": "#3B82F6"
    },
    "text": {
      "primary": "#0F172A",
      "secondary": "#475569",
      "muted": "#94A3B8",
      "accent": "#2563EB"
    },
    "button": {
      "primary-dark": "#0F1117",
      "tactile-gray": "#333A42"
    }
  },
  "blur": {
    "sm": "8px",
    "md": "12px",
    "lg": "20px"
  },
  "radius": {
    "sm": "8px",
    "md": "12px",
    "lg": "20px",
    "xl": "28px",
    "full": "9999px"
  },
  "shadow": {
    "glass-panel": "0 8px 32px 0 rgba(31, 38, 135, 0.05), inset 0 1px 1px 0 rgba(255, 255, 255, 0.8)",
    "tactile-3d": "0 8px 20px -4px rgba(0, 0, 0, 0.25), inset 0 2px 3px rgba(255, 255, 255, 0.5)",
    "iridescent-aura": "0 0 20px 2px rgba(138, 43, 226, 0.35)"
  },
  "typography": {
    "font-sans": "'Inter', sans-serif",
    "font-mono": "'JetBrains Mono', monospace"
  }
}