import { useState } from "react";
import { Button } from "@/components/ui/button.jsx";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card.jsx";
import { Input } from "@/components/ui/input.jsx";
import { Badge } from "@/components/ui/badge.jsx";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs.jsx";
import { ScrollArea } from "@/components/ui/scroll-area.jsx";
import { Alert, AlertDescription } from "@/components/ui/alert.jsx";
import { Textarea } from "@/components/ui/textarea.jsx";
import {
  Search,
  Globe,
  ExternalLink,
  Copy,
  MessageSquare,
  Loader2,
  AlertCircle,
  CheckCircle,
  FileText,
  Zap,
  Eye,
  Download,
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function WebResearchPanel({ onSendToChat }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [scrapeUrl, setScrapeUrl] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [scrapeResult, setScrapeResult] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("search");
  const [selectedStrategy, setSelectedStrategy] = useState("auto");

  const performSearch = async () => {
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/web/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: searchQuery.trim(),
          max_results: 10,
          strategy: selectedStrategy,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error("Search failed:", error);
      setError(error.message);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const performScrape = async () => {
    if (!scrapeUrl.trim() || isScraping) return;

    setIsScraping(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/web/scrape`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: scrapeUrl.trim(),
          strategy: selectedStrategy,
          extract_text: true,
          extract_links: true,
          extract_images: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setScrapeResult(data);
    } catch (error) {
      console.error("Scraping failed:", error);
      setError(error.message);
      setScrapeResult(null);
    } finally {
      setIsScraping(false);
    }
  };

  const performComprehensiveResearch = async () => {
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/research`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: searchQuery.trim(),
          strategy: "comprehensive",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error("Comprehensive research failed:", error);
      setError(error.message);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
    }
  };

  const sendToChat = (content, title = "") => {
    if (onSendToChat) {
      const message = title ? `${title}\\n\\n${content}` : content;
      onSendToChat(message);
    }
  };

  const handleKeyPress = (e, action) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      action();
    }
  };

  const formatUrl = (url) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname + urlObj.pathname;
    } catch {
      return url;
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Globe className="h-5 w-5" />
          <span>Web Research</span>
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex-1 flex flex-col"
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="search">Web Search</TabsTrigger>
            <TabsTrigger value="scrape">URL Scraper</TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent
            value="search"
            className="flex-1 flex flex-col space-y-4"
          >
            <div className="space-y-2">
              <div className="flex space-x-2">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => handleKeyPress(e, performSearch)}
                  placeholder="Enter search query..."
                  disabled={isSearching}
                  className="flex-1"
                />
                <Button
                  onClick={performSearch}
                  disabled={isSearching || !searchQuery.trim()}
                  size="icon"
                >
                  {isSearching ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>

              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={performComprehensiveResearch}
                  disabled={isSearching || !searchQuery.trim()}
                  className="flex items-center space-x-1"
                >
                  <Zap className="h-3 w-3" />
                  <span>Deep Research</span>
                </Button>

                <select
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value)}
                  className="px-2 py-1 text-sm border rounded"
                  disabled={isSearching}
                >
                  <option value="auto">Auto</option>
                  <option value="apify">Apify</option>
                  <option value="brightdata">Bright Data</option>
                </select>
              </div>
            </div>

            <ScrollArea className="flex-1">
              <div className="space-y-3">
                {searchResults.length === 0 && !isSearching && (
                  <div className="text-center text-muted-foreground py-8">
                    <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Enter a search query to find web content</p>
                    <p className="text-sm">
                      Use "Deep Research" for comprehensive analysis
                    </p>
                  </div>
                )}

                {searchResults.map((result, index) => (
                  <Card key={index} className="p-4">
                    <div className="space-y-2">
                      <div className="flex items-start justify-between">
                        <h3 className="font-medium text-sm line-clamp-2">
                          {result.title || "Untitled"}
                        </h3>
                        <div className="flex items-center space-x-1 ml-2">
                          {result.scrape_success && (
                            <Badge variant="secondary" className="text-xs">
                              <FileText className="h-3 w-3 mr-1" />
                              Scraped
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-xs">
                            {result.source}
                          </Badge>
                        </div>
                      </div>

                      <p className="text-xs text-muted-foreground">
                        {formatUrl(result.url)}
                      </p>

                      {result.snippet && (
                        <p className="text-sm text-gray-700 line-clamp-3">
                          {result.snippet}
                        </p>
                      )}

                      {result.scraped_content && (
                        <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                          <p className="font-medium mb-1">Extracted Content:</p>
                          <p className="line-clamp-4">
                            {result.scraped_content}
                          </p>
                        </div>
                      )}

                      <div className="flex items-center space-x-2 pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(result.url, "_blank")}
                          className="flex items-center space-x-1"
                        >
                          <ExternalLink className="h-3 w-3" />
                          <span>Visit</span>
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(result.url)}
                          className="flex items-center space-x-1"
                        >
                          <Copy className="h-3 w-3" />
                          <span>Copy URL</span>
                        </Button>

                        {onSendToChat && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              sendToChat(
                                result.scraped_content ||
                                  result.snippet ||
                                  result.url,
                                result.title,
                              )
                            }
                            className="flex items-center space-x-1"
                          >
                            <MessageSquare className="h-3 w-3" />
                            <span>Send to Chat</span>
                          </Button>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Scrape Tab */}
          <TabsContent
            value="scrape"
            className="flex-1 flex flex-col space-y-4"
          >
            <div className="space-y-2">
              <div className="flex space-x-2">
                <Input
                  value={scrapeUrl}
                  onChange={(e) => setScrapeUrl(e.target.value)}
                  onKeyPress={(e) => handleKeyPress(e, performScrape)}
                  placeholder="Enter URL to scrape..."
                  disabled={isScraping}
                  className="flex-1"
                />
                <Button
                  onClick={performScrape}
                  disabled={isScraping || !scrapeUrl.trim()}
                  size="icon"
                >
                  {isScraping ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                </Button>
              </div>

              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="px-2 py-1 text-sm border rounded w-full"
                disabled={isScraping}
              >
                <option value="auto">Auto Strategy</option>
                <option value="brightdata">Bright Data (JS Rendering)</option>
                <option value="zenrows">ZenRows (Anti-Bot)</option>
                <option value="apify">Apify (Custom Actors)</option>
              </select>
            </div>

            <ScrollArea className="flex-1">
              {!scrapeResult && !isScraping && (
                <div className="text-center text-muted-foreground py-8">
                  <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Enter a URL to extract content</p>
                  <p className="text-sm">
                    Supports JavaScript-heavy sites and anti-bot protection
                  </p>
                </div>
              )}

              {scrapeResult && (
                <Card className="p-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">
                        {scrapeResult.title || "Scraped Content"}
                      </h3>
                      <div className="flex items-center space-x-2">
                        {scrapeResult.success ? (
                          <Badge className="bg-green-100 text-green-800">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Success
                          </Badge>
                        ) : (
                          <Badge variant="destructive">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            Failed
                          </Badge>
                        )}
                        <Badge variant="outline" className="text-xs">
                          {scrapeResult.source}
                        </Badge>
                      </div>
                    </div>

                    <p className="text-xs text-muted-foreground">
                      {scrapeResult.url}
                    </p>

                    {scrapeResult.content && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-sm">Extracted Text:</p>
                          <div className="flex space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() =>
                                copyToClipboard(scrapeResult.content)
                              }
                            >
                              <Copy className="h-3 w-3 mr-1" />
                              Copy
                            </Button>
                            {onSendToChat && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  sendToChat(
                                    scrapeResult.content,
                                    scrapeResult.title,
                                  )
                                }
                              >
                                <MessageSquare className="h-3 w-3 mr-1" />
                                Send to Chat
                              </Button>
                            )}
                          </div>
                        </div>
                        <Textarea
                          value={scrapeResult.content}
                          readOnly
                          className="min-h-[200px] text-sm"
                        />
                      </div>
                    )}

                    {scrapeResult.links && scrapeResult.links.length > 0 && (
                      <div className="space-y-2">
                        <p className="font-medium text-sm">
                          Extracted Links ({scrapeResult.links.length}):
                        </p>
                        <div className="max-h-32 overflow-y-auto space-y-1">
                          {scrapeResult.links
                            .slice(0, 10)
                            .map((link, index) => (
                              <div
                                key={index}
                                className="flex items-center space-x-2 text-xs"
                              >
                                <ExternalLink className="h-3 w-3 text-muted-foreground" />
                                <a
                                  href={link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline truncate"
                                >
                                  {formatUrl(link)}
                                </a>
                              </div>
                            ))}
                          {scrapeResult.links.length > 10 && (
                            <p className="text-xs text-muted-foreground">
                              ... and {scrapeResult.links.length - 10} more
                              links
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    {scrapeResult.error && (
                      <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          {scrapeResult.error}
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </Card>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
