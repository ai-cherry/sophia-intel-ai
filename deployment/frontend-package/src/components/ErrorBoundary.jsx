import { Component } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card.jsx";
import { Button } from "@/components/ui/button.jsx";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import {
  AlertTriangle,
  RefreshCw,
  Copy,
  ExternalLink,
  Bug,
  Clock,
  Info,
  X,
} from "lucide-react";

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      timestamp: null,
      dismissed: false,
    };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
    };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      errorInfo,
    });

    // Log error to console for development
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    // Send error to observability service if available
    this.reportError(error, errorInfo);
  }

  reportError = async (error, errorInfo) => {
    try {
      const errorReport = {
        error_id: this.state.errorId,
        message: error.message,
        stack: error.stack,
        component_stack: errorInfo.componentStack,
        timestamp: this.state.timestamp,
        user_agent: navigator.userAgent,
        url: window.location.href,
        props: this.props,
      };

      // Attempt to send to backend observability service
      if (this.props.apiBaseUrl) {
        await fetch(`${this.props.apiBaseUrl}/api/observability/errors`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(errorReport),
        });
      }
    } catch (reportingError) {
      console.error("Failed to report error:", reportingError);
    }
  };

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      timestamp: null,
      dismissed: false,
    });
  };

  handleDismiss = () => {
    this.setState({ dismissed: true });
  };

  copyErrorDetails = async () => {
    const errorDetails = {
      errorId: this.state.errorId,
      timestamp: this.state.timestamp,
      message: this.state.error?.message,
      stack: this.state.error?.stack,
      componentStack: this.state.errorInfo?.componentStack,
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    try {
      await navigator.clipboard.writeText(JSON.stringify(errorDetails, null, 2));
    } catch (err) {
      console.error("Failed to copy error details:", err);
    }
  };

  render() {
    if (this.state.hasError && !this.state.dismissed) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4"
             style={{ backgroundColor: 'var(--sophia-bg-primary)' }}>
          <Card className="max-w-2xl w-full" style={{ backgroundColor: 'var(--sophia-bg-secondary)' }}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-full bg-red-100 dark:bg-red-900/20">
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <CardTitle className="text-red-800 dark:text-red-200">
                      Application Error
                    </CardTitle>
                    <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                      Something went wrong in the SOPHIA Intel interface
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={this.handleDismiss}
                  className="p-2"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              
              {/* Error Summary */}
              <Alert variant="destructive">
                <Bug className="h-4 w-4" />
                <AlertTitle>Error Details</AlertTitle>
                <AlertDescription>
                  <div className="space-y-2 mt-2">
                    <p className="font-medium">{this.state.error?.message}</p>
                    <div className="flex items-center space-x-4 text-xs">
                      <div className="flex items-center space-x-1">
                        <Clock className="h-3 w-3" />
                        <span>{new Date(this.state.timestamp).toLocaleString()}</span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        ID: {this.state.errorId}
                      </Badge>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>

              {/* Error Actions */}
              <div className="flex items-center space-x-3">
                <Button onClick={this.handleRetry} className="flex items-center space-x-2">
                  <RefreshCw className="h-4 w-4" />
                  <span>Retry</span>
                </Button>
                
                <Button 
                  variant="outline" 
                  onClick={this.copyErrorDetails}
                  className="flex items-center space-x-2"
                >
                  <Copy className="h-4 w-4" />
                  <span>Copy Error Details</span>
                </Button>

                <Button 
                  variant="outline"
                  onClick={() => window.location.reload()}
                  className="flex items-center space-x-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>Reload Page</span>
                </Button>
              </div>

              {/* Technical Details (Collapsible) */}
              <details className="space-y-3">
                <summary className="cursor-pointer text-sm font-medium flex items-center space-x-2">
                  <Info className="h-4 w-4" />
                  <span>Technical Details</span>
                </summary>
                
                <div className="space-y-3 pl-6">
                  {this.state.error?.stack && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Stack Trace:</h4>
                      <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded overflow-x-auto">
                        {this.state.error.stack}
                      </pre>
                    </div>
                  )}

                  {this.state.errorInfo?.componentStack && (
                    <div>
                      <h4 className="text-sm font-medium mb-2">Component Stack:</h4>
                      <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded overflow-x-auto">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}

                  <div>
                    <h4 className="text-sm font-medium mb-2">Environment:</h4>
                    <div className="text-xs space-y-1" style={{ color: 'var(--sophia-text-secondary)' }}>
                      <p>URL: {window.location.href}</p>
                      <p>User Agent: {navigator.userAgent}</p>
                      <p>Timestamp: {this.state.timestamp}</p>
                    </div>
                  </div>
                </div>
              </details>

              {/* Help Information */}
              <Alert>
                <Info className="h-4 w-4" />
                <AlertTitle>Need Help?</AlertTitle>
                <AlertDescription>
                  <div className="space-y-2 mt-2">
                    <p>If this error persists, please:</p>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      <li>Copy the error details and share with support</li>
                      <li>Check your network connection</li>
                      <li>Try refreshing the page</li>
                      <li>Clear your browser cache and cookies</li>
                    </ul>
                  </div>
                </AlertDescription>
              </Alert>

            </CardContent>
          </Card>
        </div>
      );
    }

    if (this.state.hasError && this.state.dismissed) {
      // Show minimal error indicator
      return (
        <div className="fixed bottom-4 right-4 z-50">
          <Alert variant="destructive" className="max-w-sm">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>Error occurred</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={this.handleRetry}
                className="p-1 h-6 w-6"
              >
                <RefreshCw className="h-3 w-3" />
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

