# Website & Design System: Quickie Frontend

**Product:** Quickie — Ultra-minimal track organizer for DJs  
**Design Approach:** Playful minimalism with music-industry credibility  
**Platform:** Web (desktop-first, mobile-responsive)  
**Framework:** React 18 + TypeScript + Tailwind CSS  
**Design Tool:** Figma  

---

## Part 1: Design System & Brand Identity

### 1.1 Design Philosophy

Quickie's design must embody three things:
1. **Playful:** Approachable, fun, not corporate
2. **Minimal:** Ultra-clean, only essentials visible
3. **Credible:** Speaks DJ language, professional enough for serious gigs

**Visual Direction:**
- Clean lines, generous whitespace
- Subtle playfulness in micro-interactions (not animations everywhere)
- Bold typography that carries personality
- Direct, confident messaging
- Music/audio-inspired visual metaphors (waveforms, beats, etc.)

**Avoid:**
- ❌ Generic SaaS aesthetic (gradient cards, soft shadows everywhere)
- ❌ Over-animation (fades, slides on every element)
- ❌ Corporate tone (formal language, jargon)
- ❌ Dark mode as default (light, clean, modern)
- ❌ Skeuomorphism (fake turntables, vinyl records)

---

### 1.2 Color Palette

**Core Identity Colors**

| Name | Hex | Usage | RGB |
|------|-----|-------|-----|
| **Black** | `#000000` | Text, UI borders, high contrast | 0, 0, 0 |
| **White** | `#FFFFFF` | Background, clean spaces | 255, 255, 255 |
| **Accent** | `#FF6B35` | CTAs, highlights, energy | 255, 107, 53 |
| **Warm Gray** | `#F8F7F5` | Subtle backgrounds | 248, 247, 245 |
| **Neutral** | `#6B7280` | Secondary text, disabled | 107, 114, 128 |

**Extended Palette (Semantic)**

```
Status Colors:
  Success:  #10B981 (Green)    - Processing complete, file valid
  Error:    #EF4444 (Red)      - Upload failed, processing error
  Warning:  #F59E0B (Amber)    - Large file, slow connection
  Info:     #3B82F6 (Blue)     - Tips, help text

Neutral Scale (for gradients, hover states):
  50:   #FAFAFA
  100:  #F3F3F3
  200:  #E5E5E5
  300:  #D4D4D4
  400:  #A3A3A3
  500:  #737373
  600:  #525252
  700:  #404040
  800:  #262626
  900:  #171717
```

**Why This Palette:**
- **#FF6B35** (Accent): Warm, energetic, musical (like vinyl, vinyl records)
- **Black/White:** High contrast = credibility + clarity
- **Warm Gray:** Not pure white (too clinical), slightly warm
- **Minimalist:** Only 5 core colors (no rainbow)

---

### 1.3 Typography

**Font Stack**

```css
Primary (Display & Headlines): 
  Font: "Inter" (Google Fonts) or "Helvetica Neue"
  Fallback: -apple-system, BlinkMacSystemFont, sans-serif
  Character: Modern, geometric, approachable
  
Secondary (Body Text):
  Font: "Inter" (same as primary for unity)
  Lighter weight for reading comfort
  
Monospace (Code, Tags, BPM Display):
  Font: "Inconsolata" or "Monaco"
  Used for: Track details, BPM/Key, technical info
```

**Type Scale & Sizing**

```
Display (Hero, Page Titles):
  Size: 48px (desktop) / 32px (mobile)
  Weight: 700 (Bold)
  Line Height: 1.1
  Letter Spacing: -0.02em (tight for impact)
  Example: "Let's do it quick."

Heading 1 (Section Titles):
  Size: 32px / 24px (mobile)
  Weight: 700
  Line Height: 1.2
  Letter Spacing: -0.01em

Heading 2 (Subsection Titles):
  Size: 24px / 20px (mobile)
  Weight: 600
  Line Height: 1.3
  Letter Spacing: 0

Body (Default):
  Size: 16px
  Weight: 400
  Line Height: 1.6
  Letter Spacing: 0
  Max line length: 65 characters (optimal readability)

Small (Labels, Meta):
  Size: 14px
  Weight: 500
  Line Height: 1.5
  Letter Spacing: 0.02em (slight tracking for clarity)

Tiny (Helper Text, Timestamps):
  Size: 12px
  Weight: 400
  Line Height: 1.4
  Letter Spacing: 0.01em
```

**Usage Rules:**
- Headings always uppercase-first (not ALL CAPS)
- Max 2 weights per page (700 bold for headings, 400 for body)
- Monospace only for technical data (BPM: 128, Key: Am)
- Never center-align body text (left-align for scannability)

---

### 1.4 Spacing & Layout System

**8px Grid System**

All spacing follows 8px increments for consistency:

```
Micro:    4px  (tight spacing within elements)
XS:       8px  (padding inside buttons, small gaps)
S:       16px  (padding around text, card gaps)
M:       24px  (section spacing)
L:       32px  (major spacing between sections)
XL:      48px  (hero section, large breathing room)
2XL:     64px  (max spacing between sections)
```

**Container & Layout**

```css
Max Content Width: 1200px
Padding (desktop):  40px (sides)
Padding (tablet):   24px (sides)
Padding (mobile):   16px (sides)

Grid Columns: 12-column (follows Bootstrap standard)
  Desktop: 12 equal columns
  Tablet:  6 columns
  Mobile:  1 column (full width)
```

**Breathing Room**

- Content never touches screen edges (min 16px padding)
- White space between sections = 1.5x the content height
- Cards have 24px internal padding (S spacing)

---

## Part 2: Component Library

### 2.1 Button System

**Primary Button (CTA)**
```
State: Default
  Background: #FF6B35 (Accent)
  Text: White, 16px, weight 600
  Padding: 12px 24px (vertical, horizontal)
  Border radius: 6px
  Box shadow: None (flat design)
  Cursor: pointer

State: Hover
  Background: #E55A24 (Darker shade)
  Transform: scale(1.02) (subtle scale, not translate)

State: Active/Pressed
  Background: #CC4A1C (Even darker)
  Box shadow: inset 0 2px 4px rgba(0,0,0,0.2)

State: Disabled
  Background: #D4D4D4 (Neutral 300)
  Text: #6B7280 (Neutral)
  Cursor: not-allowed
  Opacity: 0.6

Size Variants:
  Small: 10px 16px, 14px font
  Medium: 12px 24px, 16px font (default)
  Large: 16px 32px, 18px font
```

**Secondary Button (Alternative)**
```
State: Default
  Background: transparent
  Border: 2px solid #000000
  Text: Black, 16px, weight 600
  Padding: 10px 22px (account for border)

State: Hover
  Background: #F8F7F5 (Warm Gray)
  Border: 2px solid #000000

State: Active
  Background: #E5E5E5
```

**Tertiary Button (Subtle)**
```
State: Default
  Background: transparent
  Text: #FF6B35 (Accent), 16px, weight 600
  Border: none
  Text decoration: underline

State: Hover
  Text: #E55A24 (Darker accent)
  Background: #F8F7F5 (Light wash)
```

**Implementation (React + Tailwind)**
```typescript
// components/Button.tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'tertiary';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}

export function Button({ 
  variant = 'primary', 
  size = 'medium', 
  disabled = false,
  onClick,
  children 
}: ButtonProps) {
  const baseStyles = 'font-semibold rounded-md transition-all duration-200 font-inter';
  
  const variants = {
    primary: 'bg-orange-600 text-white hover:bg-orange-700 active:bg-orange-800 disabled:bg-gray-300 disabled:text-gray-600',
    secondary: 'border-2 border-black text-black hover:bg-warm-gray-50 active:bg-gray-200',
    tertiary: 'text-orange-600 underline hover:bg-warm-gray-50 hover:text-orange-700'
  };
  
  const sizes = {
    small: 'px-4 py-2 text-sm',
    medium: 'px-6 py-3 text-base',
    large: 'px-8 py-4 text-lg'
  };
  
  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${disabled ? 'cursor-not-allowed opacity-60' : ''}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
```

---

### 2.2 Input Fields

**Text Input (Upload, Search, Manual Entry)**

```
State: Default (Empty)
  Border: 1px solid #E5E5E5
  Background: #FFFFFF
  Padding: 12px 16px
  Font: 16px (prevents zoom on mobile)
  Border radius: 6px
  Placeholder text: #A3A3A3 (Neutral 400)

State: Focused
  Border: 2px solid #FF6B35
  Outline: none
  Box shadow: 0 0 0 3px rgba(255, 107, 53, 0.1)

State: Filled (Has Value)
  Border: 1px solid #FF6B35
  Text color: #000000

State: Error
  Border: 2px solid #EF4444
  Background: rgba(239, 68, 68, 0.05)
  Helper text: "This field is required"

State: Disabled
  Background: #F3F3F3
  Text color: #A3A3A3
  Cursor: not-allowed
```

**File Input (Drag-Drop Zone)**

```
Container:
  Border: 2px dashed #D4D4D4
  Background: #F8F7F5
  Border radius: 12px
  Padding: 40px 24px
  Text align: center
  Min height: 200px
  Cursor: pointer

State: Hover
  Border: 2px dashed #FF6B35
  Background: rgba(255, 107, 53, 0.05)

State: Drag Over
  Border: 2px solid #FF6B35
  Background: rgba(255, 107, 53, 0.1)
  Box shadow: 0 4px 12px rgba(255, 107, 53, 0.1)

Content:
  Icon: Cloud upload icon (or waveform)
  Heading: "Drag your tracks here"
  Secondary: "or click to browse"
  Small: "Up to 2GB • MP3, WAV, FLAC"
```

---

### 2.3 Cards & Containers

**Track Card (Preview)**

```
Width: Full-width (on mobile), 1/3 width (on desktop in grid)
Background: #FFFFFF
Border: 1px solid #E5E5E5
Border radius: 8px
Padding: 16px
Box shadow: 0 1px 3px rgba(0, 0, 0, 0.05)

Content Layout:
  Header: Filename (16px bold)
  Meta: "3:45 • 128 BPM • House"
  Action: Remove button (small, ghost)

State: Hover (Desktop)
  Box shadow: 0 4px 12px rgba(0, 0, 0, 0.1)
  Transform: translateY(-2px)
  
State: Selected (Processing)
  Border: 2px solid #FF6B35
  Background: rgba(255, 107, 53, 0.02)
```

**Status Badge**

```
Small pill-shaped element

Variant: Success
  Background: #10B981
  Text: White, 12px, weight 600
  Padding: 4px 12px
  Border radius: 12px
  Example: "✓ Processed"

Variant: Processing
  Background: #3B82F6
  Text: White
  Example: "⟳ Processing"

Variant: Error
  Background: #EF4444
  Text: White
  Example: "✗ Failed"
```

---

### 2.4 Modals & Overlays

**Modal (Settings, Confirm, Error)**

```
Overlay:
  Background: rgba(0, 0, 0, 0.5)
  Blur: 4px backdrop filter (optional)

Modal Box:
  Background: #FFFFFF
  Border radius: 12px
  Padding: 32px
  Max width: 500px
  Box shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1)
  Position: Centered on screen

Content:
  Title: 24px, weight 700
  Description: 16px, weight 400, color #6B7280
  Buttons: Usually 2 (Primary + Secondary)

Close Button (X):
  Position: top-right
  Size: 24px
  Color: #A3A3A3
  Hover: #000000
```

---

### 2.5 Progress Indicators

**Linear Progress Bar (Processing)**

```
Container:
  Height: 4px
  Width: 100%
  Background: #E5E5E5
  Border radius: 2px
  Margin: 16px 0

Progress Fill:
  Background: #FF6B35
  Height: 4px
  Animation: smooth width transition (0.3s ease-out)
  Border radius: 2px
```

**Circular Progress (Mini-Game Loading)**

```
SVG Circle:
  Radius: 40px
  Stroke width: 4px
  Background stroke: #E5E5E5
  Progress stroke: #FF6B35 (gradient optional)
  
Center Text:
  Percentage or icon
  Font: 18px, weight 700

Animation:
  Rotation: Smooth, continuous
  Progress fill: Smooth transition
```

---

## Part 3: Page Architecture

### 3.1 Landing Page Structure

**Full-Page Layout Flow (Top to Bottom)**

```
┌─────────────────────────────────────────┐
│ HEADER / NAVIGATION (fixed or sticky)   │
├─────────────────────────────────────────┤
│ HERO SECTION                            │
│ • Tagline + Logo                        │
│ • Main CTA (drag-drop demo)             │
├─────────────────────────────────────────┤
│ HOW IT WORKS (3 Steps)                  │
│ • Visual process flow                   │
├─────────────────────────────────────────┤
│ UPLOAD INTERFACE (Live Demo)            │
│ • Actual drag-drop component            │
├─────────────────────────────────────────┤
│ FEATURES SECTION                        │
│ • 4-5 key features with icons           │
├─────────────────────────────────────────┤
│ PRICING SECTION                         │
│ • Free tier vs Pro tier                 │
│ • FAQ accordion                         │
├─────────────────────────────────────────┤
│ FOOTER                                  │
│ • Links, email, legal                   │
└─────────────────────────────────────────┘
```

---

### 3.2 Header & Navigation

**Desktop Header**

```
Layout: Sticky at top, 80px height

Left: Logo/Brand
  "quickie." text (bold, 24px)
  Color: #000000
  Click: Return to top

Center: Navigation (Optional - Minimal)
  Hidden or very subtle links to:
  - How it works
  - Pricing
  - FAQ

Right: CTA Button
  "Sign up" or "Go Pro"
  Primary button variant
  Opens sign-up modal or form
```

**Mobile Header**

```
Simplified: Logo + Mobile menu icon
  Logo: "quickie."
  Menu: Hamburger icon (3 lines)
  Tap menu → Slide-in sidebar (right side)
  
Mobile Menu Contents:
  - How it works
  - Pricing
  - FAQ
  - Go Pro (prominent CTA)
```

**Navigation Implementation**
```typescript
// components/Header.tsx
export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 h-20">
      <div className="max-w-6xl mx-auto px-6 h-full flex items-center justify-between">
        {/* Logo */}
        <div className="text-2xl font-bold text-black">quickie.</div>
        
        {/* Desktop Nav */}
        <nav className="hidden md:flex gap-8">
          <a href="#how" className="text-gray-600 hover:text-black text-base">How it works</a>
          <a href="#pricing" className="text-gray-600 hover:text-black text-base">Pricing</a>
          <a href="#faq" className="text-gray-600 hover:text-black text-base">FAQ</a>
        </nav>
        
        {/* CTA + Mobile Menu */}
        <div className="flex gap-4 items-center">
          <Button variant="primary" size="medium">Go Pro</Button>
          
          <button 
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <MenuIcon />
          </button>
        </div>
      </div>
      
      {/* Mobile Menu (conditional render) */}
      {mobileMenuOpen && <MobileMenu />}
    </header>
  );
}
```

---

### 3.3 Hero Section

**Desktop Hero**

```
Layout: Full viewport height (minimum 600px)
Background: Gradient (subtle, optional)
  From: #FFFFFF
  To: #F8F7F5

Content: Centered column

┌────────────────────────────────┐
│                                │
│  Tagline (small, uppercase):   │
│  "ultra-minimal track          │
│   organizer for DJs"           │
│                                │
│  Headline (48px, bold):        │
│  "Let's do it quick."          │
│                                │
│  Subheading (18px, gray):      │
│  "Drop your audio files.       │
│   quickie cleans the messy     │
│   names, builds playlists,     │
│   and sorts your library —     │
│   fast."                       │
│                                │
│  [  Drag tracks or click  ]    │
│  (CTA to upload zone)          │
│                                │
└────────────────────────────────┘

Spacing:
  Vertical centering: min 100px top/bottom
  Tagline to headline: 16px
  Headline to subheading: 24px
  Subheading to CTA: 32px
```

**Mobile Hero**

```
Simplified: Full width, shorter height (350px minimum)

Tagline: 12px
Headline: 32px
Subheading: 16px (2-line max)
CTA: Full width button
```

**Implementation**
```typescript
// components/Hero.tsx
export function Hero() {
  return (
    <section className="min-h-screen flex items-center justify-center bg-gradient-to-b from-white to-warm-gray-50 px-6 py-20">
      <div className="max-w-2xl text-center">
        <p className="text-sm uppercase tracking-widest text-gray-600 mb-4">
          Ultra-minimal track organizer for DJs
        </p>
        
        <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
          Let's do it quick.
        </h1>
        
        <p className="text-lg md:text-xl text-gray-600 mb-12 leading-relaxed">
          Drop your audio files. quickie cleans the messy names, builds playlists, 
          and sorts your library — fast.
        </p>
        
        <Button variant="primary" size="large">
          Upload Your Tracks
        </Button>
      </div>
    </section>
  );
}
```

---

### 3.4 How It Works Section

**Visual Process: 3 Steps**

```
Layout: 3 equal columns on desktop, stacked on mobile

┌──────────┐  ┌──────────┐  ┌──────────┐
│ Step 1   │  │ Step 2   │  │ Step 3   │
│          │  │          │  │          │
│ Icon     │  │ Icon     │  │ Icon     │
│ (visual) │  │ (visual) │  │ (visual) │
│          │  │          │  │          │
│ "Drop    │  │ "Let     │  │ "Export  │
│  your    │  │  quickie │  │  & spin" │
│  tracks" │  │  sort    │  │          │
│          │  │  them"   │  │          │
│ Desc:    │  │ Desc:    │  │ Desc:    │
│ Drag any │  │ AI cleans│  │ One clean│
│ folder   │  │ names,   │  │ ZIP with │
│ onto app.│  │ detects  │  │ tagged   │
│          │  │ BPM...   │  │ files &  │
│          │  │          │  │ playlists│
└──────────┘  └──────────┘  └──────────┘
```

**Content:**

Step 1: Drop Your Tracks
- Icon: Cloud upload or folder icon (SVG, 64px)
- Description: "Drag any folder of audio files onto the app. No accounts, no waiting."
- Focus: Zero friction entry point

Step 2: Let Quickie Sort Them
- Icon: Waveform or AI spark (SVG, 64px)
- Description: "AI cleans messy names, detects BPM & key, and splits by genre in seconds."
- Focus: Automation value

Step 3: Export & Spin
- Icon: Download or play icon (SVG, 64px)
- Description: "One clean ZIP with tagged files and .m3u8 playlists — drop into Rekordbox."
- Focus: Ready-to-use output

---

### 3.5 Live Upload Demo Section

This is the actual app interface embedded in the landing page!

**"Try It Free" Area**

```
Section Title: "Try it free"
Subtitle: "Upload up to 25 tracks"

┌────────────────────────────────┐
│ [  Drag & Drop Zone  ]          │
│  or click to browse             │
│                                │
│  Supported: MP3, WAV, FLAC...  │
│  Max: 2GB per upload           │
└────────────────────────────────┘

[After upload, show:]
  File list with preview
  Processing progress
  Download ZIP when done
```

**This should be a functional component that:**
- Accepts file uploads (client-side validation only for MVP)
- Shows real-time processing
- Returns downloadable ZIP
- Limit to 25 tracks for free

---

### 3.6 Features Section

**5 Feature Cards (or fewer)**

Each card shows:
- Icon (SVG, 48px, accent color)
- Title (20px, bold)
- Description (16px, gray)
- Optional: Small visual (waveform animation, etc.)

**Features to Highlight:**

1. **AI-Powered Cleanup**
   Icon: Sparkles
   "Automatically cleans messy filenames and detects track metadata"

2. **BPM & Key Detection**
   Icon: Metronome or tempo indicator
   "Instantly identifies BPM and musical key for seamless mixing"

3. **Genre-Based Organization**
   Icon: Folder or tags
   "Automatically sort tracks by genre and create playlists"

4. **Rekordbox Ready**
   Icon: Download or DJ icon
   "Export as .m3u8 playlists and tagged files — compatible with Pioneer Rekordbox"

5. **No Signup Required**
   Icon: User with checkmark
   "Upload and process tracks instantly. No accounts, no friction."

---

### 3.7 Pricing Section

**Clean, Direct Pricing Table**

```
Section Title: "One plan. Everything unlocked."
Subtitle: "Try free above (up to 25 tracks). Ready for real gigs? Grab Pro."

┌─────────────────────────────────────┐
│           QUICKIE PRO               │
│                                     │
│ $4/month (billed annually)          │
│                                     │
│ ✓ Unlimited track uploads           │
│ ✓ Unlimited ZIP exports             │
│ ✓ AI cleanup & detection            │
│ ✓ Genre splitting                   │
│ ✓ Rekordbox-ready exports           │
│ ✓ Cancel anytime                    │
│                                     │
│  [ Sign up to go Pro ]              │
└─────────────────────────────────────┘

Optional: Toggle between Monthly/Yearly
  Monthly:  $4/month
  Yearly:   $48/year (SAVE 20%)
```

**Pricing Page Implementation**
```typescript
// components/Pricing.tsx
export function Pricing() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('yearly');
  
  const price = billingPeriod === 'yearly' ? 48 : 4;
  const period = billingPeriod === 'yearly' ? '/year' : '/month';
  
  return (
    <section id="pricing" className="py-20 px-6 bg-warm-gray-50">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-4">One plan. Everything unlocked.</h2>
        <p className="text-center text-gray-600 mb-12">
          Try free above (up to 25 tracks). Ready for real gigs? Grab Pro.
        </p>
        
        {/* Billing Toggle */}
        <div className="flex justify-center gap-4 mb-12">
          <button 
            onClick={() => setBillingPeriod('monthly')}
            className={billingPeriod === 'monthly' ? 'font-bold text-black' : 'text-gray-600'}
          >
            Monthly
          </button>
          <span className="text-gray-600">|</span>
          <button 
            onClick={() => setBillingPeriod('yearly')}
            className={billingPeriod === 'yearly' ? 'font-bold text-black' : 'text-gray-600'}
          >
            Yearly <span className="text-orange-600 text-sm">SAVE 20%</span>
          </button>
        </div>
        
        {/* Pricing Card */}
        <div className="bg-white border-2 border-black rounded-lg p-8 max-w-md mx-auto">
          <h3 className="text-2xl font-bold mb-2">Quickie Pro</h3>
          <p className="text-sm text-gray-600 mb-6">Best value — save 20%</p>
          
          <div className="mb-8">
            <span className="text-5xl font-bold">${price}</span>
            <span className="text-gray-600">{period}</span>
          </div>
          
          <ul className="space-y-4 mb-8">
            {[
              'Unlimited track uploads',
              'Unlimited ZIP exports',
              'AI cleanup, BPM & key detection',
              'Split by genre, sort by folders, build playlists',
              'Rekordbox-ready .m3u8 exports',
              'Cancel anytime'
            ].map((feature, idx) => (
              <li key={idx} className="flex gap-3">
                <CheckIcon className="w-5 h-5 text-orange-600 flex-shrink-0" />
                <span className="text-gray-700">{feature}</span>
              </li>
            ))}
          </ul>
          
          <Button variant="primary" size="large" className="w-full">
            Sign up to go Pro
          </Button>
        </div>
      </div>
    </section>
  );
}
```

---

### 3.8 FAQ Section

**Accordion Component (Collapsible)**

```
Questions & Answers in expandable accordion

Q: Do you store my music?
A: No. Files are processed temporarily and deleted after export. 
   We never keep your music on our servers.

Q: What formats work?
A: MP3, WAV, FLAC, OGG, AAC, and more. 
   Check the full list in our docs.

Q: Can I cancel anytime?
A: Yes. Pro subscription can be cancelled anytime 
   with no penalties or hidden fees.

Q: How accurate is the BPM/key detection?
A: Our AI reaches 85-90% accuracy for most electronic music. 
   You can always manually adjust if needed.

Q: Does this work offline?
A: No, quickie requires internet for AI processing. 
   But once exported, you can use your files offline.

Q: Can I import my old playlists?
A: Not yet, but we're working on it. 
   Stay tuned for updates!
```

**Accordion Implementation**
```typescript
// components/FAQ.tsx
export function FAQ() {
  const faqs = [
    {
      question: "Do you store my music?",
      answer: "No. Files are processed temporarily and deleted after export. We never keep your music on our servers."
    },
    // ... more FAQs
  ];
  
  return (
    <section id="faq" className="py-20 px-6 max-w-2xl mx-auto">
      <h2 className="text-4xl font-bold mb-12">Questions, answered.</h2>
      
      <div className="space-y-4">
        {faqs.map((faq, idx) => (
          <FAQAccordion key={idx} question={faq.question} answer={faq.answer} />
        ))}
      </div>
    </section>
  );
}

function FAQAccordion({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);
  
  return (
    <div className="border-b border-gray-200 py-4">
      <button 
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center text-left"
      >
        <h3 className="text-lg font-semibold text-black">{question}</h3>
        <span className="text-2xl text-orange-600">{open ? '−' : '+'}</span>
      </button>
      
      {open && (
        <p className="mt-4 text-gray-600 leading-relaxed">{answer}</p>
      )}
    </div>
  );
}
```

---

### 3.9 Footer

**Simple Footer**

```
┌─────────────────────────────────────┐
│         quickie.                    │
│                                     │
│  Product                            │
│  • How it works                     │
│  • Pricing                          │
│  • FAQ                              │
│                                     │
│  Legal                              │
│  • Privacy Policy                   │
│  • Terms of Service                 │
│  • Cookie Policy                    │
│                                     │
│  Contact: hello@quickie.app         │
│                                     │
│  © 2026 Quickie. All rights         │
│  reserved.                          │
│                                     │
│  [GitHub] [Twitter] [Email]         │
└─────────────────────────────────────┘
```

**Footer Code**
```typescript
// components/Footer.tsx
export function Footer() {
  return (
    <footer className="bg-black text-white py-16 px-6">
      <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-12">
        <div>
          <h3 className="text-2xl font-bold mb-6">quickie.</h3>
          <p className="text-gray-400">
            Ultra-minimal track organizer for DJs. 
            Drop, sort, export — before your set starts.
          </p>
        </div>
        
        <div>
          <h4 className="font-semibold mb-4">Product</h4>
          <ul className="space-y-2 text-gray-400">
            <li><a href="#how" className="hover:text-white">How it works</a></li>
            <li><a href="#pricing" className="hover:text-white">Pricing</a></li>
            <li><a href="#faq" className="hover:text-white">FAQ</a></li>
          </ul>
        </div>
        
        <div>
          <h4 className="font-semibold mb-4">Legal</h4>
          <ul className="space-y-2 text-gray-400">
            <li><a href="/privacy" className="hover:text-white">Privacy Policy</a></li>
            <li><a href="/terms" className="hover:text-white">Terms of Service</a></li>
          </ul>
        </div>
      </div>
      
      <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-500">
        <p>© 2026 Quickie. All rights reserved.</p>
        <p className="text-sm mt-2">hello@quickie.app</p>
      </div>
    </footer>
  );
}
```

---

## Part 4: Responsive Design

### 4.1 Breakpoints

```
Mobile:   < 640px  (phones)
Tablet:   640px - 1024px  (iPad, small tablets)
Desktop:  > 1024px  (laptops, desktops)

Tailwind Prefixes:
  sm:  640px
  md:  768px
  lg:  1024px
  xl:  1280px
  2xl: 1536px
```

### 4.2 Mobile-First Strategy

Build for mobile first, then enhance for larger screens.

**Example: Hero Section**
```typescript
<h1 className="text-3xl md:text-5xl lg:text-6xl font-bold">
  Let's do it quick.
</h1>

// Explanation:
// Base (mobile): 32px
// md (tablet): 48px
// lg (desktop): 64px
```

**Example: Grid Layout**
```typescript
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Single column on mobile, 2 on tablet, 3 on desktop */}
</div>
```

### 4.3 Touch-Friendly Sizes

On mobile, ensure:
- Buttons: Min 44px height (finger-friendly)
- Tap targets: Min 48x48px
- Spacing: At least 8px between tap targets

```typescript
// Touch-friendly button
<button className="py-3 px-6 md:py-2 md:px-4">
  Tap me
</button>
```

---

## Part 5: Accessibility (WCAG 2.1 AA)

### 5.1 Color Contrast

**Required:** 4.5:1 for normal text, 3:1 for large text

**Our Palette:**
- Black (#000) on White (#FFF): 21:1 ✅ (Perfect)
- Accent (#FF6B35) on White: 5.2:1 ✅ (Good for headings)
- Gray (#6B7280) on White: 4.8:1 ✅ (Body text OK)

**Avoid:** Gray text on Warm Gray background (contrast too low)

### 5.2 Keyboard Navigation

- All buttons, links: `Tab` focusable
- Focus indicator: 2px colored outline
- Escape key: Close modals
- Enter key: Submit forms

```css
/* Focus styles */
button:focus-visible,
a:focus-visible {
  outline: 2px solid #FF6B35;
  outline-offset: 2px;
}
```

### 5.3 Screen Reader Support

```typescript
// Alt text for images
<img src="logo.svg" alt="Quickie logo" />

// Semantic HTML
<button aria-label="Upload tracks">
  <UploadIcon />
</button>

// Form labels
<label htmlFor="filename">File name</label>
<input id="filename" type="text" />

// Skip to main content
<a href="#main-content" className="sr-only">
  Skip to main content
</a>
```

### 5.4 Reduce Motion

Respect user's motion preferences:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Part 6: UX Copy & Messaging

### 6.1 Voice & Tone

**Brand Voice:**
- Direct: Say exactly what happens
- Playful: Use casual language ("one quickie before my live set")
- Confident: No apologizing or hedging
- DJ-fluent: Use music/audio terminology appropriately

**What NOT to do:**
- ❌ "Please upload your files" (too formal)
- ❌ "An error has occurred" (vague, apologetic)
- ❌ "Leverage our AI-powered solution" (corporate jargon)
- ❌ "Your audio has been successfully processed" (robotic)

### 6.2 Key Copy Moments

**Upload Zone:**
- ✅ "Drag your tracks here" (direct, action-oriented)
- ✅ "or click to browse" (alternative path)
- ✅ "Up to 2GB • MP3, WAV, FLAC" (specifics)

**Processing State:**
- ✅ "Processing your tracks..." (ongoing status)
- ✅ "BPM detected: 128" (live feedback)
- ❌ "Please wait..." (passive)

**Success State:**
- ✅ "All done. Download your ZIP." (celebratory)
- ✅ "Ready to import into Rekordbox" (helpful)
- ❌ "Files have been successfully processed" (corporate)

**Error State:**
- ✅ "File too large (2.5GB). Max: 2GB." (explain issue + solution)
- ✅ "MP4 not supported. Try MP3, WAV, or FLAC." (specific alternatives)
- ❌ "Error 400: Invalid file format" (technical, unhelpful)

**CTA Buttons:**
- ✅ "Upload Tracks" (specific action)
- ✅ "Download ZIP" (clear result)
- ✅ "Go Pro" (clear benefit)
- ❌ "Submit" (generic)
- ❌ "Continue" (vague)

---

### 6.3 Empty States

**First Time Using:**
```
Icon: Empty upload zone (cloud icon)
Heading: "Upload your first tracks"
Description: "Drag music files here or click to browse. 
              We'll clean them up and prepare for your set."
CTA: "Choose Files"
```

**All Tracks Processed:**
```
Icon: Checkmark with music note
Heading: "All set to spin"
Description: "Your tracks are ready. Download the ZIP 
              and import into Rekordbox."
CTA: "Download ZIP"
Secondary: "Process more tracks"
```

---

## Part 7: Figma Design System Setup

### 7.1 Figma File Structure

```
Quickie Design System
├── 📄 Overview & Guidelines
│   ├── Brand Book
│   ├── Design Principles
│   └── Color Palette
│
├── 🎨 Components
│   ├── Buttons
│   │   ├── Primary (default, hover, active, disabled)
│   │   ├── Secondary
│   │   └── Tertiary
│   ├── Inputs
│   │   ├── Text Input (states)
│   │   └── File Upload (states)
│   ├── Cards
│   ├── Modals
│   ├── Progress Indicators
│   └── Navigation
│
├── 📱 Pages
│   ├── Landing Page (Desktop)
│   ├── Landing Page (Mobile)
│   ├── Upload Interface (Desktop)
│   └── Upload Interface (Mobile)
│
└── 🖼️ Icons & Assets
    ├── Icons (24px, 32px, 48px, 64px)
    ├── Illustrations
    └── Animations (prototype reference)
```

### 7.2 Figma Best Practices

1. **Use Components:** Every button, input, card as a component
2. **Variants:** Create variants for states (hover, active, disabled)
3. **Variables:** Define color tokens as Figma variables
4. **Constraints:** Use auto-layout for responsive behavior
5. **Naming:** Consistent naming convention (Component/Variant/State)

**Example Component Naming:**
```
Button/Primary/Default
Button/Primary/Hover
Button/Primary/Active
Button/Primary/Disabled
Button/Primary/Sizes/Small
Button/Primary/Sizes/Medium
Button/Primary/Sizes/Large
```

---

## Part 8: Frontend Implementation

### 8.1 Project Structure

```
quickie-frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Layout.tsx
│   │   ├── sections/
│   │   │   ├── Hero.tsx
│   │   │   ├── HowItWorks.tsx
│   │   │   ├── Features.tsx
│   │   │   ├── UploadDemo.tsx
│   │   │   ├── Pricing.tsx
│   │   │   └── FAQ.tsx
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── Badge.tsx
│   │   └── common/
│   │       ├── UploadZone.tsx
│   │       ├── TrackList.tsx
│   │       ├── ProcessingStatus.tsx
│   │       └── ExportButton.tsx
│   ├── hooks/
│   │   ├── useUpload.ts
│   │   ├── useProcessing.ts
│   │   └── useAuth.ts (Phase 2)
│   ├── services/
│   │   ├── api.ts
│   │   └── storage.ts
│   ├── styles/
│   │   ├── globals.css
│   │   ├── tailwind.config.js
│   │   └── animations.css
│   ├── App.tsx
│   └── main.tsx
│
├── public/
│   ├── images/
│   ├── icons/
│   └── fonts/
│
├── tailwind.config.js
├── vite.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

### 8.2 Tailwind Configuration

```javascript
// tailwind.config.js
export default {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        orange: {
          600: '#FF6B35',
          700: '#E55A24',
          800: '#CC4A1C',
        },
        'warm-gray': {
          50: '#F8F7F5',
          100: '#F3F3F3',
        },
      },
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        mono: ['Inconsolata', 'monospace'],
      },
      fontSize: {
        xs: ['12px', { lineHeight: '1.4' }],
        sm: ['14px', { lineHeight: '1.5' }],
        base: ['16px', { lineHeight: '1.6' }],
        lg: ['18px', { lineHeight: '1.6' }],
        xl: ['20px', { lineHeight: '1.4' }],
        '2xl': ['24px', { lineHeight: '1.3' }],
        '3xl': ['32px', { lineHeight: '1.2' }],
        '4xl': ['48px', { lineHeight: '1.1' }],
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        base: '16px',
        md: '24px',
        lg: '32px',
        xl: '48px',
        '2xl': '64px',
      },
      borderRadius: {
        none: '0',
        sm: '4px',
        base: '6px',
        md: '8px',
        lg: '12px',
      },
      boxShadow: {
        sm: '0 1px 3px rgba(0, 0, 0, 0.05)',
        base: '0 4px 12px rgba(0, 0, 0, 0.1)',
        lg: '0 20px 25px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  plugins: [],
};
```

### 8.3 Global Styles

```css
/* src/styles/globals.css */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
  font-size: 16px;
}

body {
  font-family: 'Inter', sans-serif;
  background-color: #ffffff;
  color: #000000;
  line-height: 1.6;
}

/* Focus styles for accessibility */
:focus-visible {
  outline: 2px solid #FF6B35;
  outline-offset: 2px;
}

/* Smooth transitions */
button, a, input {
  transition: all 0.2s ease-out;
}

/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 8.4 Key Component Examples

#### Button Component
```typescript
// src/components/ui/Button.tsx
import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'tertiary';
  size?: 'small' | 'medium' | 'large';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    variant = 'primary', 
    size = 'medium', 
    isLoading = false,
    disabled,
    children,
    className,
    ...props 
  }, ref) => {
    const baseStyles = 'font-semibold rounded-md transition-all duration-200 font-inter font-semibold cursor-pointer';
    
    const variants = {
      primary: 'bg-orange-600 text-white hover:bg-orange-700 active:bg-orange-800 disabled:bg-gray-300 disabled:text-gray-600 disabled:cursor-not-allowed',
      secondary: 'border-2 border-black text-black bg-transparent hover:bg-warm-gray-50 active:bg-gray-200 disabled:border-gray-300 disabled:text-gray-400',
      tertiary: 'text-orange-600 underline bg-transparent hover:bg-warm-gray-50 hover:text-orange-700 disabled:text-gray-400 disabled:cursor-not-allowed'
    };
    
    const sizes = {
      small: 'px-4 py-2 text-sm',
      medium: 'px-6 py-3 text-base',
      large: 'px-8 py-4 text-lg'
    };
    
    return (
      <button 
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${isLoading ? 'opacity-50 pointer-events-none' : ''} ${className}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? '⟳ Processing...' : children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

#### Upload Zone Component
```typescript
// src/components/common/UploadZone.tsx
import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  maxSize?: number; // in bytes
  maxFiles?: number;
}

export function UploadZone({ 
  onFilesSelected, 
  maxSize = 2 * 1024 * 1024 * 1024, // 2GB
  maxFiles = 25 
}: UploadZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > maxFiles) {
      alert(`Maximum ${maxFiles} files at a time`);
      return;
    }
    onFilesSelected(acceptedFiles);
  }, [maxFiles, onFilesSelected]);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.flac', '.ogg', '.aac']
    },
    maxSize
  });
  
  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-200 ${
        isDragActive 
          ? 'border-orange-600 bg-orange-50' 
          : 'border-gray-300 bg-warm-gray-50 hover:border-orange-600'
      }`}
    >
      <input {...getInputProps()} />
      
      <div className="text-5xl mb-4">☁️</div>
      
      <h3 className="text-xl font-bold mb-2">Drag your tracks here</h3>
      <p className="text-gray-600 mb-4">or click to browse</p>
      
      <p className="text-sm text-gray-500">
        Up to 2GB • MP3, WAV, FLAC, OGG, AAC
      </p>
    </div>
  );
}
```

---

## Part 9: Animations & Micro-Interactions

### 9.1 Principles

- Animations serve a purpose (not decoration)
- Fast: 200-300ms for most interactions
- Smooth: Use ease-out timing
- Subtle: Don't distract from content

### 9.2 Key Animations

**Button Hover:**
```css
.button {
  transition: all 0.2s ease-out;
}

.button:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
```

**Drag-Drop Feedback:**
```css
.upload-zone {
  transition: all 0.2s ease-out;
}

.upload-zone.drag-active {
  border-color: #FF6B35;
  background-color: rgba(255, 107, 53, 0.05);
  transform: scale(1.01);
}
```

**Processing Animation (Pulsing):**
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.processing {
  animation: pulse 2s infinite;
}
```

**Fade In (Page Load):**
```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

section {
  animation: fadeIn 0.5s ease-out;
}
```

---

## Part 10: Deployment & Performance

### 10.1 Build Optimization

```bash
# Production build
npm run build

# Outputs optimized bundles
# dist/
#   ├── index.html
#   ├── assets/
#   │   ├── main.{hash}.js
#   │   ├── styles.{hash}.css
#   └── ...
```

### 10.2 Performance Targets

- **Lighthouse Score:** 90+
- **Core Web Vitals:**
  - LCP (Largest Contentful Paint): < 2.5s
  - CLS (Cumulative Layout Shift): < 0.1
  - FID (First Input Delay): < 100ms

### 10.3 Image Optimization

- Use WebP format where possible
- Compress SVGs
- Lazy load images below the fold
- Use responsive images (srcset)

```typescript
// Optimized image example
<img 
  src="hero-desktop.webp" 
  srcSet="hero-mobile.webp 640w, hero-tablet.webp 1024w, hero-desktop.webp 1920w"
  alt="Quickie hero section"
  loading="lazy"
/>
```

---

## Part 11: Testing Checklist

### Functionality
- [ ] Upload works (drag-drop + click)
- [ ] File validation works (size, format)
- [ ] Processing displays progress
- [ ] ZIP downloads correctly
- [ ] Links navigate properly

### Responsive
- [ ] Mobile (375px): All elements visible, readable
- [ ] Tablet (768px): Layout adapts, no overflow
- [ ] Desktop (1440px): Proper spacing, centered content
- [ ] Touch targets are 48px minimum (mobile)

### Accessibility
- [ ] Tab navigation works through all interactive elements
- [ ] Color contrast meets WCAG AA (4.5:1 for text)
- [ ] Keyboard focus visible everywhere
- [ ] Screen reader can read all content
- [ ] Modals can be closed with Escape key
- [ ] Forms have proper labels

### Browser Support
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

### Performance
- [ ] Lighthouse score > 90
- [ ] Page loads < 3s (3G)
- [ ] No layout shifts during load
- [ ] Animations smooth (60fps)

---

## Part 12: Design Handoff to Development

When you're ready to code, use these deliverables:

### Files to Export from Figma:
1. **Design System Guide** (PDF or link)
2. **Component Specs** (dimensions, spacing, states)
3. **Illustrations & Icons** (SVG format, optimized)
4. **Design Tokens** (colors, typography, spacing)
5. **Responsive Breakpoints** (mobile, tablet, desktop specs)

### Handoff Document Should Include:
- Color palette (hex codes)
- Typography scale (sizes, weights, line heights)
- Spacing values (margin, padding)
- Component variants (all states)
- Animation specifications (duration, easing)
- Accessibility requirements (contrast, focus states)

---

## Part 13: Quick Setup Guide

### Start Building Right Now:

```bash
# 1. Create Vite project
npm create vite@latest quickie-frontend -- --template react-ts

# 2. Install dependencies
cd quickie-frontend
npm install
npm install tailwindcss postcss autoprefixer react-dropzone axios zustand

# 3. Configure Tailwind
npx tailwindcss init -p

# 4. Start dev server
npm run dev

# 5. Open browser
# Visit http://localhost:5173
```

### File to create first:
1. `tailwind.config.js` (from section 8.2)
2. `src/styles/globals.css` (from section 8.3)
3. `src/components/ui/Button.tsx` (from section 8.4)
4. `src/components/Hero.tsx` (build this first)
5. `src/App.tsx` (wire sections together)

---

## Conclusion

This design system gives you:
✅ Cohesive visual identity (playful + credible)
✅ Reusable components (faster development)
✅ Accessibility built-in (WCAG AA compliant)
✅ Responsive by default (mobile-first)
✅ Clear copy strategy (DJ-focused messaging)
✅ Figma to code pipeline (designer → developer)

**With Claude Code, you can build this entire frontend in 2-3 weeks.**

Next steps:
1. Create Figma file (or skip straight to code)
2. Build components one at a time
3. Test on mobile + accessibility
4. Deploy to Vercel

Ready to start? I can help you build the first component!
