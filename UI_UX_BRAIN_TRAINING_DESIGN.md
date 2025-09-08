# Sophia Brain Training UI/UX Design Specification

## Design Philosophy

**"Conversational Intelligence Amplification"** - A unified chat experience that naturally extends Sophia's capabilities through seamless file ingestion and knowledge synthesis.

## 1. Unified Chat Experience

### 1.1 Chat Interface Architecture

```typescript
interface UnifiedChatLayout {
  // Main conversation area remains primary focus
  chatContainer: {
    width: "100%";
    maxWidth: "1400px";
    layout: "adaptive-columns"; // 1-3 columns based on content

    mainColumn: {
      flex: "1 1 70%";
      minWidth: "400px";
      elements: {
        messageThread: ConversationThread;
        inputArea: EnhancedInput;
        contextBar: ActiveContextIndicator;
      };
    };

    sidePanel: {
      flex: "0 1 30%";
      minWidth: "300px";
      collapsible: true;
      tabs: ["Processing", "Knowledge", "Services"];
    };
  };
}
```

### 1.2 Enhanced Message Components

```typescript
// Message types with rich interactions
type MessageEnhancement = {
  standard: BasicMessage;
  fileProcessing: {
    preview: ThumbnailGrid | DocumentPreview;
    status: ProcessingIndicator;
    actions: ["pause", "cancel", "prioritize"];
    metadata: FileMetadata;
  };
  knowledgeExtraction: {
    entities: InteractiveEntityList;
    relationships: MiniGraph;
    confidence: ConfidenceScore;
    source: SourceAttribution;
  };
  clarification: {
    type: "ambiguity" | "confirmation" | "selection";
    options: InteractiveChoices;
    context: RelatedKnowledge;
  };
};
```

### 1.3 Real-time Processing Indicators

```css
/* Elegant processing states */
.processing-indicator {
  /* Subtle pulsing dot for background processing */
  &.background {
    width: 8px;
    height: 8px;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    animation: pulse 2s ease-in-out infinite;
  }

  /* Inline progress for active file processing */
  &.active-file {
    display: flex;
    align-items: center;
    gap: 12px;

    .file-icon {
      animation: float 3s ease-in-out infinite;
    }

    .progress-ring {
      stroke-dasharray: 283;
      stroke-dashoffset: calc(283 - (283 * var(--progress) / 100));
      transition: stroke-dashoffset 0.5s ease;
    }
  }

  /* Multi-file batch indicator */
  &.batch-processing {
    .file-stack {
      position: relative;

      .file-card {
        position: absolute;
        transform: translateY(calc(var(--index) * -2px));
        opacity: calc(1 - (var(--index) * 0.2));
      }
    }
  }
}
```

## 2. Universal File Upload System

### 2.1 Drag-Drop Zone Design

```typescript
interface SmartDropZone {
  // Invisible full-screen drop target
  fullScreenDropLayer: {
    position: "fixed",
    inset: 0,
    zIndex: 9999,
    pointerEvents: "none", // Until drag detected

    onDragEnter: () => {
      // Elegant overlay animation
      showDropOverlay({
        animation: "fadeScale",
        duration: 200,
        preview: intelligentPreview()
      })
    }
  },

  // Context-aware drop zones
  smartZones: [
    {
      id: "chat-input",
      accepts: "*",
      enhanced: true,
      message: "Drop to analyze and discuss"
    },
    {
      id: "knowledge-graph",
      accepts: ["structured", "documents"],
      message: "Drop to add to knowledge base"
    },
    {
      id: "service-sync",
      accepts: ["calendar", "email", "documents"],
      message: "Drop to sync with {detected_service}"
    }
  ]
}
```

### 2.2 File Processing Pipeline UI

```typescript
// Visual pipeline representation
interface ProcessingPipeline {
  stages: [
    {
      name: "Detection";
      icon: "🔍";
      duration: "instant";
      ui: MinimalSpinner;
    },
    {
      name: "Extraction";
      icon: "📊";
      duration: "1-5s";
      ui: ProgressBar;
      preview: ExtractedDataPreview;
    },
    {
      name: "Understanding";
      icon: "🧠";
      duration: "2-10s";
      ui: NeuralNetworkAnimation;
      insights: RealTimeInsights;
    },
    {
      name: "Integration";
      icon: "🔗";
      duration: "1-3s";
      ui: ConnectionVisualization;
    },
  ];

  batchMode: {
    layout: "compact-grid";
    maxVisible: 6;
    overflow: "virtual-scroll";
    grouping: "by-type" | "by-status";
  };
}
```

### 2.3 Smart File Preview

```css
/* Adaptive preview system */
.file-preview-container {
  /* Document preview with smart extraction */
  &.document {
    .preview-pane {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 20px;

      .document-view {
        /* Original with highlights */
        mark.extracted {
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(59, 130, 246, 0.1) 10%,
            rgba(59, 130, 246, 0.1) 90%,
            transparent 100%
          );
          border-left: 2px solid #3b82f6;
        }
      }

      .extraction-panel {
        /* Key information cards */
        .info-card {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 16px;

          &.key-entity {
            border-color: #3b82f6;
          }
        }
      }
    }
  }

  /* Image preview with object detection */
  &.image {
    .detection-overlay {
      position: absolute;
      inset: 0;

      .detection-box {
        position: absolute;
        border: 2px solid #10b981;
        border-radius: 4px;

        .label {
          position: absolute;
          top: -24px;
          left: 0;
          background: #10b981;
          color: white;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
        }
      }
    }
  }
}
```

## 3. Service Integration Dashboard

### 3.1 Service Status Grid

```typescript
interface ServiceDashboard {
  layout: "adaptive-grid";

  serviceCard: {
    size: "compact" | "expanded";

    visualIndicators: {
      connectionStatus: PulsingDot;
      lastSync: RelativeTime;
      dataVolume: MiniChart;
      health: HealthScore;
    };

    quickActions: [
      { icon: "🔄"; action: "sync"; shortcut: "cmd+s" },
      { icon: "🔍"; action: "search"; shortcut: "/" },
      { icon: "⚙️"; action: "settings"; shortcut: "cmd+," },
    ];

    expandedView: {
      recentActivity: ActivityFeed;
      dataBreakdown: DonutChart;
      syncSchedule: Timeline;
    };
  };
}
```

### 3.2 Cross-Service Search Interface

```css
/* Unified search with service filtering */
.cross-service-search {
  position: relative;

  .search-input {
    padding: 12px 48px 12px 16px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;

    &:focus {
      background: rgba(255, 255, 255, 0.08);
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }

  .service-filters {
    display: flex;
    gap: 8px;
    margin-top: 8px;

    .filter-chip {
      padding: 4px 12px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.2s;

      &.active {
        background: rgba(59, 130, 246, 0.1);
        border-color: #3b82f6;

        .service-icon {
          animation: rotate 0.5s ease;
        }
      }
    }
  }

  .search-results {
    .result-group {
      margin-bottom: 24px;

      .group-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;

        .service-badge {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
        }
      }

      .result-item {
        padding: 12px;
        margin-bottom: 8px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
        border-left: 3px solid transparent;

        &:hover {
          background: rgba(255, 255, 255, 0.05);
          border-left-color: var(--service-color);
        }
      }
    }
  }
}
```

## 4. Knowledge Visualization

### 4.1 Interactive Knowledge Graph

```typescript
interface KnowledgeGraph {
  visualization: {
    engine: "force-directed" | "hierarchical" | "radial";

    nodeTypes: {
      entity: {
        size: "by-importance";
        color: "by-category";
        icon: "dynamic";
        interactions: ["hover", "click", "drag"];
      };
      document: {
        shape: "rectangle";
        preview: "thumbnail";
        metadata: "on-hover";
      };
      service: {
        shape: "hexagon";
        animation: "pulse-on-update";
        badge: "data-count";
      };
    };

    edgeTypes: {
      relationship: {
        style: "solid";
        weight: "by-strength";
        label: "on-hover";
      };
      inference: {
        style: "dashed";
        color: "gradient";
        animation: "flow";
      };
    };

    controls: {
      zoom: PinchZoom | ScrollWheel;
      filter: CategoryFilter;
      search: GraphSearch;
      layout: LayoutSelector;
      timeline: TemporalSlider;
    };
  };
}
```

### 4.2 Graph Interaction Patterns

```css
/* Smooth graph interactions */
.knowledge-graph {
  .node {
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      transform: scale(1.1);
      filter: drop-shadow(0 4px 12px rgba(59, 130, 246, 0.3));

      & ~ .edge {
        opacity: 0.3;
      }

      &.connected ~ .edge {
        opacity: 1;
        stroke-width: 2;
      }
    }

    &.selected {
      transform: scale(1.2);

      &::before {
        content: "";
        position: absolute;
        inset: -8px;
        border: 2px solid #3b82f6;
        border-radius: 50%;
        animation: pulse 2s infinite;
      }
    }

    &.clustering {
      .cluster-indicator {
        position: absolute;
        top: -8px;
        right: -8px;
        background: #8b5cf6;
        color: white;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: bold;
      }
    }
  }

  .edge {
    pointer-events: none;

    &.highlighting {
      stroke: url(#gradient-highlight);
      stroke-width: 3;
      animation: flow 2s linear infinite;
    }
  }
}

@keyframes flow {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: -100;
  }
}
```

## 5. Smart Features

### 5.1 Auto-Suggestion System

```typescript
interface SmartSuggestions {
  triggers: {
    fileUpload: {
      analyze: ContentTypeDetector;
      suggest: [
        "Extract key insights",
        "Compare with existing knowledge",
        "Generate summary",
        "Find related documents",
        "Create action items",
      ];
    };

    conversation: {
      monitor: ContextAnalyzer;
      suggest: {
        files: "Relevant documents in your system";
        services: "Data from connected services";
        actions: "Next logical steps";
      };
    };
  };

  ui: {
    position: "inline" | "floating";
    style: "chips" | "list" | "cards";
    animation: "slideIn" | "fade";
    dismissible: true;

    chip: {
      icon: "auto-detect";
      text: "suggestion";
      action: "one-click";
      preview: "on-hover";
    };
  };
}
```

### 5.2 Learning Progress Tracker

```css
/* Visual learning progress */
.learning-tracker {
  position: fixed;
  bottom: 24px;
  right: 24px;

  .progress-orb {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: conic-gradient(
      from 0deg,
      #3b82f6 0deg,
      #3b82f6 calc(var(--progress) * 3.6deg),
      rgba(59, 130, 246, 0.1) calc(var(--progress) * 3.6deg)
    );
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: transform 0.3s ease;

    &:hover {
      transform: scale(1.1);

      .tooltip {
        opacity: 1;
        transform: translateY(-8px);
      }
    }

    .brain-icon {
      width: 32px;
      height: 32px;

      path {
        fill: url(#brain-gradient);
        animation: pulse 3s ease-in-out infinite;
      }
    }

    .level-badge {
      position: absolute;
      top: -4px;
      right: -4px;
      background: linear-gradient(135deg, #10b981, #3b82f6);
      color: white;
      padding: 2px 6px;
      border-radius: 12px;
      font-size: 10px;
      font-weight: bold;
    }
  }

  .expanded-view {
    position: absolute;
    bottom: 80px;
    right: 0;
    width: 320px;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;

    .stat-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;

      .stat-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 12px;
        border-radius: 8px;

        .label {
          font-size: 11px;
          opacity: 0.7;
          margin-bottom: 4px;
        }

        .value {
          font-size: 20px;
          font-weight: bold;
          background: linear-gradient(135deg, #3b82f6, #8b5cf6);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
      }
    }
  }
}
```

## 6. Component Interactions

### 6.1 Micro-Interactions

```typescript
interface MicroInteractions {
  fileUpload: {
    onDragEnter: "ripple-effect";
    onDrop: "success-burst";
    onProcess: "neural-pulse";
    onComplete: "checkmark-draw";
  };

  chat: {
    onType: "subtle-glow";
    onSend: "message-whoosh";
    onReceive: "soft-pop";
    onThinking: "gradient-wave";
  };

  knowledge: {
    onNodeHover: "connections-highlight";
    onNodeClick: "radial-expansion";
    onLinkCreate: "lightning-draw";
    onCluster: "magnetic-pull";
  };
}
```

### 6.2 Responsive Breakpoints

```css
/* Adaptive layout system */
@media (max-width: 768px) {
  .unified-chat {
    .side-panel {
      position: fixed;
      inset: 0;
      transform: translateX(100%);
      transition: transform 0.3s ease;

      &.open {
        transform: translateX(0);
      }
    }

    .knowledge-graph {
      height: 300px;
      touch-action: pan-x pan-y;
    }
  }
}

@media (min-width: 1920px) {
  .unified-chat {
    .chat-container {
      max-width: 1800px;

      .third-column {
        display: block;
        flex: 0 1 400px;
        /* Persistent knowledge view */
      }
    }
  }
}
```

## 7. Visual Design System

### 7.1 Color Palette

```css
:root {
  /* Primary */
  --primary-blue: #3b82f6;
  --primary-purple: #8b5cf6;

  /* Semantic */
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #06b6d4;

  /* Neutrals */
  --bg-primary: #0a0a0a;
  --bg-secondary: rgba(255, 255, 255, 0.02);
  --bg-elevated: rgba(255, 255, 255, 0.05);

  /* Gradients */
  --gradient-primary: linear-gradient(
    135deg,
    var(--primary-blue),
    var(--primary-purple)
  );
  --gradient-glow: radial-gradient(
    circle,
    rgba(59, 130, 246, 0.1),
    transparent 70%
  );
}
```

### 7.2 Typography

```css
.typography {
  /* Headers */
  h1 {
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.02em;
  }
  h2 {
    font-size: 24px;
    font-weight: 600;
    letter-spacing: -0.01em;
  }
  h3 {
    font-size: 18px;
    font-weight: 600;
  }

  /* Body */
  .body-large {
    font-size: 16px;
    line-height: 1.6;
  }
  .body-regular {
    font-size: 14px;
    line-height: 1.5;
  }
  .body-small {
    font-size: 12px;
    line-height: 1.4;
  }

  /* Special */
  .mono {
    font-family: "JetBrains Mono", monospace;
  }
  .gradient-text {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
}
```

## 8. Accessibility Features

```typescript
interface AccessibilityEnhancements {
  keyboard: {
    navigation: "full-support";
    shortcuts: CustomizableShortcuts;
    focus: VisibleFocusIndicators;
  };

  screen_readers: {
    aria: CompleteAriaLabels;
    announcements: LiveRegions;
    descriptions: ContextualDescriptions;
  };

  visual: {
    contrast: "WCAG-AAA";
    fontSize: ScalableText;
    animations: ReducedMotionSupport;
    themes: ["light", "dark", "high-contrast"];
  };
}
```

## Implementation Priority

### Phase 1: Core Experience

1. Unified chat with file drop
2. Basic processing indicators
3. Simple knowledge preview

### Phase 2: Intelligence Layer

1. Smart suggestions
2. Service integration
3. Advanced file processing

### Phase 3: Visualization

1. Knowledge graph
2. Learning progress
3. Cross-service search

### Phase 4: Polish

1. Micro-interactions
2. Advanced animations
3. Accessibility refinement

## Success Metrics

- **File Processing Speed**: <2s for 90% of files
- **UI Response Time**: <100ms for all interactions
- **Learning Curve**: <5 min to understand core features
- **User Satisfaction**: >4.5/5 rating
- **Accessibility Score**: 100% WCAG compliance

---

_This design creates a powerful yet approachable interface that makes Sophia's brain training feel like a natural conversation with visual intelligence._
