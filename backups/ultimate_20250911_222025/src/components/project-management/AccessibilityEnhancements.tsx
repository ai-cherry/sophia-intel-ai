import React, { useState, useRef, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Eye, EyeOff, Volume2, VolumeX, Keyboard, Mouse,
  Settings, CheckCircle, AlertTriangle, Info,
  Contrast, Type, Zap, Focus, Navigation, ArrowKeys
} from 'lucide-react';

// ==================== ACCESSIBILITY-ENHANCED COMPONENTS ====================

interface AccessibilityPreferences {
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  reducedMotion: boolean;
  screenReaderMode: boolean;
  keyboardNavigation: boolean;
  focusIndicators: 'standard' | 'enhanced' | 'high-visibility';
  colorBlindSupport: boolean;
  audioDescriptions: boolean;
}

interface A11yViolation {
  id: string;
  severity: 'critical' | 'major' | 'minor';
  rule: string;
  element: string;
  description: string;
  impact: string;
  solution: string;
  wcagLevel: 'A' | 'AA' | 'AAA';
}

// ==================== ACCESSIBILITY ENHANCEMENT COMPONENT ====================

const AccessibilityEnhancements: React.FC = () => {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>({
    highContrast: false,
    fontSize: 'medium',
    reducedMotion: false,
    screenReaderMode: false,
    keyboardNavigation: true,
    focusIndicators: 'standard',
    colorBlindSupport: false,
    audioDescriptions: false
  });

  const [announcements, setAnnouncements] = useState<string[]>([]);
  const [focusedElement, setFocusedElement] = useState<string>('');
  const ariaLiveRef = useRef<HTMLDivElement>(null);

  // Mock A11y audit results
  const mockViolations: A11yViolation[] = [
    {
      id: 'contrast-1',
      severity: 'critical',
      rule: 'color-contrast',
      element: 'Button.secondary',
      description: 'Insufficient color contrast ratio (2.8:1)',
      impact: 'Users with low vision may not be able to read button text',
      solution: 'Increase contrast to meet WCAG AA standard (4.5:1)',
      wcagLevel: 'AA'
    },
    {
      id: 'aria-1',
      severity: 'major',
      rule: 'aria-label',
      element: 'IconButton',
      description: 'Interactive elements missing accessible names',
      impact: 'Screen reader users cannot understand button purpose',
      solution: 'Add aria-label or aria-labelledby attributes',
      wcagLevel: 'A'
    },
    {
      id: 'keyboard-1',
      severity: 'major',
      rule: 'keyboard-navigation',
      element: 'CustomDropdown',
      description: 'Custom dropdown not keyboard accessible',
      impact: 'Keyboard users cannot access dropdown options',
      solution: 'Implement proper keyboard event handlers and ARIA states',
      wcagLevel: 'A'
    },
    {
      id: 'focus-1',
      severity: 'minor',
      rule: 'focus-visible',
      element: 'Card components',
      description: 'Focus indicators not visible in high contrast mode',
      impact: 'Users may lose track of keyboard focus',
      solution: 'Enhance focus ring visibility with outline and box-shadow',
      wcagLevel: 'AA'
    }
  ];

  // Accessibility utilities
  const announceToScreenReader = (message: string) => {
    setAnnouncements(prev => [...prev, message]);
    setTimeout(() => {
      setAnnouncements(prev => prev.slice(1));
    }, 3000);
  };

  const handleKeyboardNavigation = (event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
      announceToScreenReader('Action activated');
    }
  };

  const updatePreference = (key: keyof AccessibilityPreferences, value: any) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
    announceToScreenReader(`${key} setting updated to ${value}`);
  };

  // Apply accessibility preferences to DOM
  useEffect(() => {
    const root = document.documentElement;

    // High contrast mode
    if (preferences.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Font size
    root.style.setProperty('--font-scale', {
      'small': '0.875',
      'medium': '1',
      'large': '1.125',
      'extra-large': '1.25'
    }[preferences.fontSize]);

    // Reduced motion
    if (preferences.reducedMotion) {
      root.style.setProperty('--animation-duration', '0ms');
      root.style.setProperty('--transition-duration', '0ms');
    } else {
      root.style.removeProperty('--animation-duration');
      root.style.removeProperty('--transition-duration');
    }

    // Enhanced focus indicators
    root.setAttribute('data-focus-style', preferences.focusIndicators);

  }, [preferences]);

  const getSeverityColor = (severity: string) => {
    const colors = {
      critical: 'text-red-600 bg-red-50 border-red-200',
      major: 'text-orange-600 bg-orange-50 border-orange-200',
      minor: 'text-yellow-600 bg-yellow-50 border-yellow-200'
    };
    return colors[severity as keyof typeof colors] || colors.minor;
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'major': return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      default: return <Info className="w-4 h-4 text-yellow-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Screen Reader Announcements */}
      <div
        ref={ariaLiveRef}
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {announcements.map((announcement, idx) => (
          <div key={idx}>{announcement}</div>
        ))}
      </div>

      {/* ==================== ACCESSIBILITY PREFERENCES ==================== */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="w-5 h-5" />
            <span>Accessibility Preferences</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Visual Preferences */}
          <div>
            <h4 className="font-medium mb-3 flex items-center">
              <Eye className="w-4 h-4 mr-2" />
              Visual Preferences
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="flex items-center justify-between">
                  <span className="text-sm font-medium">High Contrast Mode</span>
                  <button
                    role="switch"
                    aria-checked={preferences.highContrast}
                    onClick={() => updatePreference('highContrast', !preferences.highContrast)}
                    onKeyDown={(e) => handleKeyboardNavigation(e, () => updatePreference('highContrast', !preferences.highContrast))}
                    className={`relative w-11 h-6 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      preferences.highContrast ? 'bg-blue-600' : 'bg-gray-300'
                    }`}
                  >
                    <span className="sr-only">Toggle high contrast mode</span>
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      preferences.highContrast ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </label>
                <p className="text-xs text-gray-600">Increases color contrast for better readability</p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="font-size-select">
                  Font Size
                </label>
                <select
                  id="font-size-select"
                  value={preferences.fontSize}
                  onChange={(e) => updatePreference('fontSize', e.target.value)}
                  className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                  aria-describedby="font-size-help"
                >
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                  <option value="extra-large">Extra Large</option>
                </select>
                <p id="font-size-help" className="text-xs text-gray-600">Adjusts text size across the interface</p>
              </div>
            </div>
          </div>

          {/* Motion & Animation */}
          <div>
            <h4 className="font-medium mb-3 flex items-center">
              <Zap className="w-4 h-4 mr-2" />
              Motion & Animation
            </h4>
            <div className="space-y-2">
              <label className="flex items-center justify-between">
                <span className="text-sm font-medium">Reduce Motion</span>
                <button
                  role="switch"
                  aria-checked={preferences.reducedMotion}
                  onClick={() => updatePreference('reducedMotion', !preferences.reducedMotion)}
                  className={`relative w-11 h-6 rounded-full transition-colors focus:ring-2 focus:ring-blue-500 ${
                    preferences.reducedMotion ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                >
                  <span className="sr-only">Toggle reduced motion</span>
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                    preferences.reducedMotion ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </label>
              <p className="text-xs text-gray-600">Reduces or eliminates animations that may cause discomfort</p>
            </div>
          </div>

          {/* Navigation & Focus */}
          <div>
            <h4 className="font-medium mb-3 flex items-center">
              <Navigation className="w-4 h-4 mr-2" />
              Navigation & Focus
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="focus-indicators-select">
                  Focus Indicators
                </label>
                <select
                  id="focus-indicators-select"
                  value={preferences.focusIndicators}
                  onChange={(e) => updatePreference('focusIndicators', e.target.value)}
                  className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                >
                  <option value="standard">Standard</option>
                  <option value="enhanced">Enhanced</option>
                  <option value="high-visibility">High Visibility</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="flex items-center justify-between">
                  <span className="text-sm font-medium">Keyboard Navigation</span>
                  <button
                    role="switch"
                    aria-checked={preferences.keyboardNavigation}
                    onClick={() => updatePreference('keyboardNavigation', !preferences.keyboardNavigation)}
                    className={`relative w-11 h-6 rounded-full transition-colors focus:ring-2 focus:ring-blue-500 ${
                      preferences.keyboardNavigation ? 'bg-blue-600' : 'bg-gray-300'
                    }`}
                  >
                    <span className="sr-only">Toggle keyboard navigation</span>
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      preferences.keyboardNavigation ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </label>
              </div>
            </div>
          </div>

          {/* Assistive Technology */}
          <div>
            <h4 className="font-medium mb-3 flex items-center">
              <Volume2 className="w-4 h-4 mr-2" />
              Assistive Technology
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="flex items-center justify-between">
                  <span className="text-sm font-medium">Screen Reader Mode</span>
                  <button
                    role="switch"
                    aria-checked={preferences.screenReaderMode}
                    onClick={() => updatePreference('screenReaderMode', !preferences.screenReaderMode)}
                    className={`relative w-11 h-6 rounded-full transition-colors focus:ring-2 focus:ring-blue-500 ${
                      preferences.screenReaderMode ? 'bg-blue-600' : 'bg-gray-300'
                    }`}
                  >
                    <span className="sr-only">Toggle screen reader optimizations</span>
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      preferences.screenReaderMode ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </label>
              </div>

              <div className="space-y-2">
                <label className="flex items-center justify-between">
                  <span className="text-sm font-medium">Audio Descriptions</span>
                  <button
                    role="switch"
                    aria-checked={preferences.audioDescriptions}
                    onClick={() => updatePreference('audioDescriptions', !preferences.audioDescriptions)}
                    className={`relative w-11 h-6 rounded-full transition-colors focus:ring-2 focus:ring-blue-500 ${
                      preferences.audioDescriptions ? 'bg-blue-600' : 'bg-gray-300'
                    }`}
                  >
                    <span className="sr-only">Toggle audio descriptions</span>
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      preferences.audioDescriptions ? 'translate-x-6' : 'translate-x-1'
                    }`} />
                  </button>
                </label>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ==================== ACCESSIBILITY AUDIT RESULTS ==================== */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span>Accessibility Audit Results</span>
            </div>
            <div className="flex space-x-2">
              <Badge variant="destructive">{mockViolations.filter(v => v.severity === 'critical').length} Critical</Badge>
              <Badge variant="default">{mockViolations.filter(v => v.severity === 'major').length} Major</Badge>
              <Badge variant="secondary">{mockViolations.filter(v => v.severity === 'minor').length} Minor</Badge>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Compliance Overview */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-red-600">68%</div>
              <div className="text-sm text-gray-600">WCAG 2.1 A</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">45%</div>
              <div className="text-sm text-gray-600">WCAG 2.1 AA</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">12%</div>
              <div className="text-sm text-gray-600">WCAG 2.1 AAA</div>
            </div>
          </div>

          {/* Violation Details */}
          <div className="space-y-3">
            {mockViolations.map((violation) => (
              <div key={violation.id} className={`border rounded-lg p-4 ${getSeverityColor(violation.severity)}`}>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getSeverityIcon(violation.severity)}
                    <span className="font-medium text-sm">{violation.rule}</span>
                    <Badge variant="outline" className="text-xs">
                      WCAG {violation.wcagLevel}
                    </Badge>
                  </div>
                  <Badge variant={violation.severity === 'critical' ? 'destructive' : 'secondary'}>
                    {violation.severity.toUpperCase()}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <p className="text-sm"><strong>Element:</strong> {violation.element}</p>
                  <p className="text-sm"><strong>Issue:</strong> {violation.description}</p>
                  <p className="text-sm"><strong>Impact:</strong> {violation.impact}</p>
                  <div className="bg-white bg-opacity-50 p-2 rounded text-sm">
                    <strong>Solution:</strong> {violation.solution}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ==================== KEYBOARD SHORTCUTS REFERENCE ==================== */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Keyboard className="w-5 h-5" />
            <span>Keyboard Shortcuts</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h5 className="font-medium mb-2">Navigation</h5>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Tab</span>
                  <span className="text-gray-600">Next element</span>
                </div>
                <div className="flex justify-between">
                  <span>Shift + Tab</span>
                  <span className="text-gray-600">Previous element</span>
                </div>
                <div className="flex justify-between">
                  <span>Enter</span>
                  <span className="text-gray-600">Activate element</span>
                </div>
                <div className="flex justify-between">
                  <span>Escape</span>
                  <span className="text-gray-600">Close modal/menu</span>
                </div>
              </div>
            </div>

            <div>
              <h5 className="font-medium mb-2">Project Management</h5>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Ctrl + N</span>
                  <span className="text-gray-600">New project</span>
                </div>
                <div className="flex justify-between">
                  <span>Ctrl + F</span>
                  <span className="text-gray-600">Search projects</span>
                </div>
                <div className="flex justify-between">
                  <span>Ctrl + R</span>
                  <span className="text-gray-600">Refresh data</span>
                </div>
                <div className="flex justify-between">
                  <span>Alt + A</span>
                  <span className="text-gray-600">View alerts</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ==================== IMPLEMENTATION GUIDELINES ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>Implementation Guidelines</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Semantic HTML:</strong> Use proper heading hierarchy (h1-h6), landmark elements (nav, main, aside),
              and form labels to ensure screen reader compatibility.
            </AlertDescription>
          </Alert>

          <Alert>
            <Focus className="h-4 w-4" />
            <AlertDescription>
              <strong>Focus Management:</strong> Implement visible focus indicators, manage focus flow in modals/dropdowns,
              and provide skip links for keyboard navigation.
            </AlertDescription>
          </Alert>

          <Alert>
            <Contrast className="h-4 w-4" />
            <AlertDescription>
              <strong>Color & Contrast:</strong> Ensure 4.5:1 contrast ratio for normal text, 3:1 for large text,
              and don't rely solely on color to convey information.
            </AlertDescription>
          </Alert>

          <Alert>
            <Type className="h-4 w-4" />
            <AlertDescription>
              <strong>Text & Content:</strong> Use clear, simple language, provide text alternatives for images,
              and ensure content is readable and understandable.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
};

export default AccessibilityEnhancements;
