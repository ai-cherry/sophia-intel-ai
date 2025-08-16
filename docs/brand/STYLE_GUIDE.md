# SOPHIA Pay Ready Style Guide

## 🎨 Brand Identity

### Brand Name Standards
- **SOPHIA**: Always use "SOPHIA" (all caps) - never "Sofia" or "Sophia"
- **Pay Ready**: Always two words "Pay Ready" - never "PayReady" or "pay-ready"

### Logo Usage
The SOPHIA electrified octopus logo represents intelligence, connectivity, and energy. Use the appropriate version based on context:

- **Primary Logo**: `sophia-electrified-octopus-logo.png` - Full octopus with electrical effects
- **Logo with Wordmark**: `sophia-logo-with-wordmark.png` - Complete brand identity
- **Icon/Favicon**: `sophia-icon-favicon.png` - Simplified version for small sizes

---

## 🌈 Color Palette

### Primary Colors

| Color | Hex Code | Usage | Description |
|-------|----------|-------|-------------|
| **Azure** | `#4758F1` | Primary brand color | Main buttons, links, primary actions |
| **Cobalt** | `#2B31E5` | Primary dark variant | Hover states, emphasis, depth |
| **Sky** | `#E9F5F6` | Light background | Cards, panels, subtle backgrounds |
| **Mint** | `#86D0BE` | Accent color | Success states, highlights, secondary actions |
| **Indigo** | `#0D173A` | Dark base | Text, dark backgrounds, high contrast |

### Gradient
**Sunset Gradient**: `linear-gradient(135deg, #D3CADE 0%, #AC8AD8 100%)`
- Use for special elements, hero sections, and premium features
- Apply sparingly for maximum impact

### Semantic Colors

| Purpose | Color | Hex Code |
|---------|-------|----------|
| Success | Mint | `#86D0BE` |
| Warning | Orange | `#ED8936` |
| Error | Red | `#F56565` |
| Info | Azure | `#4758F1` |

---

## 📝 Typography

### Font Hierarchy

**Primary Font**: Inter (system fallback: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto)

| Element | Size | Weight | Line Height | Usage |
|---------|------|--------|-------------|-------|
| **H1** | 2.5rem (40px) | 700 | 1.2 | Page titles, hero headings |
| **H2** | 2rem (32px) | 600 | 1.3 | Section headings |
| **H3** | 1.5rem (24px) | 600 | 1.4 | Subsection headings |
| **H4** | 1.25rem (20px) | 500 | 1.4 | Card titles, component headings |
| **Body** | 1rem (16px) | 400 | 1.6 | Main content, descriptions |
| **Small** | 0.875rem (14px) | 400 | 1.5 | Captions, metadata |
| **Caption** | 0.75rem (12px) | 400 | 1.4 | Fine print, timestamps |

### Text Colors
- **Primary Text**: Indigo `#0D173A`
- **Secondary Text**: Gray `#4A5568`
- **Light Text**: Gray `#718096`
- **Text on Primary**: White `#FFFFFF`
- **Text on Accent**: Indigo `#0D173A`

---

## 🔲 Spacing & Layout

### Spacing Scale (Tailwind-based)
- **xs**: 0.25rem (4px)
- **sm**: 0.5rem (8px)
- **md**: 1rem (16px)
- **lg**: 1.5rem (24px)
- **xl**: 2rem (32px)
- **2xl**: 3rem (48px)
- **3xl**: 4rem (64px)

### Grid System
- **Container Max Width**: 1200px
- **Columns**: 12-column grid
- **Gutters**: 24px (lg spacing)
- **Breakpoints**:
  - Mobile: 0-768px
  - Tablet: 768-1024px
  - Desktop: 1024px+

### Border Radius
- **Small**: 4px (buttons, inputs)
- **Medium**: 8px (cards, panels)
- **Large**: 12px (modals, major components)
- **Full**: 50% (circular elements, avatars)

---

## 🎛️ Component Styles

### Buttons

#### Primary Button
```css
.btn-pay-ready-primary {
  background-color: #4758F1;
  color: #FFFFFF;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-pay-ready-primary:hover {
  background-color: #2B31E5;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(71, 88, 241, 0.3);
}
```

#### Secondary Button
```css
.btn-pay-ready-secondary {
  background-color: #86D0BE;
  color: #0D173A;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-pay-ready-secondary:hover {
  background-color: #6BC4A8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(134, 208, 190, 0.3);
}
```

### Cards
```css
.card-pay-ready {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(71, 88, 241, 0.1);
  transition: all 0.2s ease;
}

.card-pay-ready:hover {
  box-shadow: 0 8px 24px rgba(71, 88, 241, 0.2);
  transform: translateY(-2px);
}
```

### Voice Interface Elements

#### Voice Button
```css
.voice-button-pay-ready {
  background: #4758F1;
  border: 3px solid #E9F5F6;
  border-radius: 50%;
  width: 80px;
  height: 80px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(71, 88, 241, 0.3);
}

.voice-button-pay-ready:hover {
  background: #2B31E5;
  transform: scale(1.05);
}

.voice-button-pay-ready.recording {
  background: #86D0BE;
  animation: pulse-pay-ready 1.5s infinite;
}
```

---

## 📊 Data Visualization

### Chart Colors (in order of use)
1. Azure `#4758F1`
2. Mint `#86D0BE`
3. Sunset Start `#D3CADE`
4. Cobalt `#2B31E5`
5. Sunset End `#AC8AD8`

### Status Indicators
- **Online/Active**: Mint `#86D0BE`
- **Warning**: Orange `#ED8936`
- **Error/Offline**: Red `#F56565`
- **Processing**: Azure `#4758F1`

---

## 🎭 Voice Interface Design

### Voice States
- **Idle**: Light gray `#A0AEC0`
- **Listening**: Azure `#4758F1` with pulse animation
- **Processing**: Sunset gradient with rotation
- **Speaking**: Mint `#86D0BE` with wave animation

### Audio Visualizer
- **Primary Bars**: Azure `#4758F1`
- **Secondary Bars**: Mint `#86D0BE`
- **Background**: Sky `#E9F5F6`

---

## 📱 Mobile Considerations

### Touch Targets
- **Minimum Size**: 44px × 44px
- **Recommended**: 48px × 48px
- **Voice Button**: 80px × 80px (primary interaction)

### Mobile-Specific Colors
- **Safe Area**: Sky `#E9F5F6` background
- **Navigation**: Indigo `#0D173A` with white text
- **Active States**: Azure `#4758F1` with increased opacity

---

## ♿ Accessibility

### Contrast Ratios
- **Primary Text on White**: 14.8:1 (AAA)
- **Azure on White**: 4.8:1 (AA)
- **Mint on White**: 3.2:1 (AA Large)
- **White on Azure**: 4.8:1 (AA)

### Focus States
- **Focus Ring**: Azure `#4758F1` with 2px outline
- **Focus Background**: Sky `#E9F5F6` with 20% opacity

---

## 🚫 Don'ts

### Color Usage
- ❌ Don't use colors outside the defined palette
- ❌ Don't use Azure and Cobalt together without sufficient contrast
- ❌ Don't overuse the sunset gradient (max 1-2 elements per page)

### Typography
- ❌ Don't use more than 3 font weights on a single page
- ❌ Don't use font sizes smaller than 12px
- ❌ Don't use all caps except for "SOPHIA" brand name

### Logo Usage
- ❌ Don't modify the octopus logo colors
- ❌ Don't stretch or distort the logo
- ❌ Don't use the logo on backgrounds with insufficient contrast

---

## 📦 Implementation

### CSS Variables
Import the Pay Ready palette:
```css
@import url('./brand/colors/pay-ready-palette.css');
```

### Tailwind Configuration
Add Pay Ready colors to your Tailwind config:
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        'pay-ready': {
          azure: '#4758F1',
          cobalt: '#2B31E5',
          sky: '#E9F5F6',
          mint: '#86D0BE',
          indigo: '#0D173A',
        }
      }
    }
  }
}
```

### React Components
Use consistent className patterns:
```jsx
<button className="btn-pay-ready-primary">
  Primary Action
</button>

<div className="card-pay-ready">
  <h3 className="text-pay-ready-indigo">Card Title</h3>
</div>
```

---

## 🎯 Brand Personality

### Voice & Tone
- **Professional**: Business-focused, reliable
- **Intelligent**: Smart, insightful, data-driven
- **Friendly**: Approachable, helpful, warm
- **Energetic**: Dynamic, responsive, engaging

### Visual Personality
- **Modern**: Clean lines, contemporary design
- **Technological**: Circuit patterns, electrical motifs
- **Trustworthy**: Consistent, professional appearance
- **Innovative**: Forward-thinking, cutting-edge

---

*This style guide ensures consistent application of the Pay Ready brand across all SOPHIA interfaces and touchpoints.*

