"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Loader2, Play, Sparkles, Code, CheckCircle } from "lucide-react";

export default function SwarmsPage() {
  const [task, setTask] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [currentPhase, setCurrentPhase] = useState<string>("");
  const [plan, setPlan] = useState("");
  const [code, setCode] = useState("");
  const [review, setReview] = useState("");

  const runPlatinumSwarm = async () => {
    if (!task.trim()) return;
    
    setIsRunning(true);
    setPlan("");
    setCode("");
    setReview("");
    
    try {
      const response = await fetch("/api/swarm/platinum/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${process.env.NEXT_PUBLIC_API_KEY || "dev-token"}`
        },
        body: JSON.stringify({ task })
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('event:')) {
              const eventType = line.slice(6).trim();
              
            } else if (line.startsWith('data:')) {
              const data = JSON.parse(line.slice(5).trim());
              
              if (data.phase) {
                setCurrentPhase(data.phase);
              } else if (data.content) {
                if (currentPhase === "planning" || eventType === "plan") {
                  setPlan(data.content);
                } else if (currentPhase === "coding" || eventType === "code") {
                  setCode(data.content);
                } else if (currentPhase === "review" || eventType === "review") {
                  setReview(data.content);
                }
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Swarm execution error:", error);
    } finally {
      setIsRunning(false);
      setCurrentPhase("");
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Platinum Swarm</h1>
        <p className="text-muted-foreground">
          Multi-agent system for planning, coding, and review
        </p>
      </div>

      {/* Input Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Task Description</CardTitle>
          <CardDescription>
            Describe what you want the swarm to build
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="e.g., Create a Python function that calculates fibonacci numbers with memoization"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            className="min-h-[100px] mb-4"
            disabled={isRunning}
          />
          <Button 
            onClick={runPlatinumSwarm}
            disabled={isRunning || !task.trim()}
            className="w-full sm:w-auto"
          >
            {isRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Running Swarm...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Run Platinum Swarm
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Planning Phase */}
        <Card className={currentPhase === "planning" ? "ring-2 ring-primary" : ""}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Planning
              </CardTitle>
              {plan && <Badge variant="success">Complete</Badge>}
              {currentPhase === "planning" && <Badge>Active</Badge>}
            </div>
            <CardDescription>Strategic task decomposition</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {currentPhase === "planning" && !plan && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Planning in progress...
                </div>
              )}
              {plan && (
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap text-xs">{plan}</pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Coding Phase */}
        <Card className={currentPhase === "coding" ? "ring-2 ring-primary" : ""}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Coding
              </CardTitle>
              {code && <Badge variant="success">Complete</Badge>}
              {currentPhase === "coding" && <Badge>Active</Badge>}
            </div>
            <CardDescription>Implementation generation</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {currentPhase === "coding" && !code && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating code...
                </div>
              )}
              {code && (
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap text-xs bg-muted p-2 rounded">
                    <code>{code}</code>
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Review Phase */}
        <Card className={currentPhase === "review" ? "ring-2 ring-primary" : ""}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                Review
              </CardTitle>
              {review && <Badge variant="success">Complete</Badge>}
              {currentPhase === "review" && <Badge>Active</Badge>}
            </div>
            <CardDescription>Quality assessment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {currentPhase === "review" && !review && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Reviewing implementation...
                </div>
              )}
              {review && (
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap text-xs">{review}</pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status Bar */}
      {isRunning && (
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              Current Phase: {currentPhase || "Initializing..."}
            </span>
            <Badge variant="outline">
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              Processing
            </Badge>
          </div>
        </div>
      )}
    </div>
  );
}