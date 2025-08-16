import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { 
  Search, 
  Database, 
  ExternalLink, 
  Copy, 
  MessageSquare, 
  Loader2,
  AlertCircle,
  CheckCircle,
  FileText,
  BookOpen,
  Brain,
  Plus,
  Save,
  Eye,
  Star,
  Clock,
  Tag
} from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function KnowledgePanel({ onSendToChat }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [notionResults, setNotionResults] = useState([])
  const [pendingPrinciples, setPendingPrinciples] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [isLoadingPrinciples, setIsLoadingPrinciples] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('search')
  
  // Create new knowledge form
  const [newKnowledgeTitle, setNewKnowledgeTitle] = useState('')
  const [newKnowledgeContent, setNewKnowledgeContent] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  
  // Load pending principles on component mount
  useEffect(() => {
    loadPendingPrinciples()
  }, [])
  
  const performUniversalSearch = async () => {
    if (!searchQuery.trim() || isSearching) return
    
    setIsSearching(true)
    setError(null)
    
    try {
      // Search both MCP services and Notion in parallel
      const [mcpResponse, notionResponse] = await Promise.allSettled([
        // MCP multi-service search
        fetch(`${API_BASE_URL}/context/search_multi_service?query=${encodeURIComponent(searchQuery.trim())}&services=rag,vector,notion&limit=10`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        }),
        
        // Notion search
        fetch(`${API_BASE_URL}/api/notion/search`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: searchQuery.trim(),
            max_results: 10
          })
        })
      ])
      
      // Process MCP results
      if (mcpResponse.status === 'fulfilled' && mcpResponse.value.ok) {
        const mcpData = await mcpResponse.value.json()
        setSearchResults(mcpData.results || [])
      } else {
        setSearchResults([])
      }
      
      // Process Notion results
      if (notionResponse.status === 'fulfilled' && notionResponse.value.ok) {
        const notionData = await notionResponse.value.json()
        setNotionResults(notionData.results || [])
      } else {
        setNotionResults([])
      }
      
    } catch (error) {
      console.error('Universal search failed:', error)
      setError(error.message)
      setSearchResults([])
      setNotionResults([])
    } finally {
      setIsSearching(false)
    }
  }
  
  const loadPendingPrinciples = async () => {
    setIsLoadingPrinciples(true)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/notion/principles/pending`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setPendingPrinciples(data.principles || [])
      }
      
    } catch (error) {
      console.error('Failed to load pending principles:', error)
    } finally {
      setIsLoadingPrinciples(false)
    }
  }
  
  const approvePrinciple = async (principleId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/notion/principles/${principleId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      if (response.ok) {
        // Remove from pending list
        setPendingPrinciples(prev => prev.filter(p => p.id !== principleId))
      }
      
    } catch (error) {
      console.error('Failed to approve principle:', error)
      setError('Failed to approve principle')
    }
  }
  
  const createKnowledgePage = async () => {
    if (!newKnowledgeTitle.trim() || !newKnowledgeContent.trim() || isCreating) return
    
    setIsCreating(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/notion/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          database_id: '', // Will use default knowledge database
          title: newKnowledgeTitle.trim(),
          content: newKnowledgeContent.trim(),
          properties: {
            "Source": {
              "select": {
                "name": "SOPHIA Dashboard"
              }
            }
          }
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        
        // Clear form
        setNewKnowledgeTitle('')
        setNewKnowledgeContent('')
        
        // Show success (could add a toast notification here)
        setError(null)
        
        // Optionally refresh search results
        if (searchQuery.trim()) {
          performUniversalSearch()
        }
        
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
    } catch (error) {
      console.error('Failed to create knowledge page:', error)
      setError(error.message)
    } finally {
      setIsCreating(false)
    }
  }
  
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
    } catch (error) {
      console.error('Failed to copy to clipboard:', error)
    }
  }
  
  const sendToChat = (content, title = '') => {
    if (onSendToChat) {
      const message = title ? `${title}\\n\\n${content}` : content
      onSendToChat(message)
    }
  }
  
  const handleKeyPress = (e, action) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      action()
    }
  }
  
  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleDateString()
    } catch {
      return timestamp
    }
  }
  
  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Database className="h-5 w-5" />
          <span>Knowledge Base</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="search">Universal Search</TabsTrigger>
            <TabsTrigger value="principles">Principles</TabsTrigger>
            <TabsTrigger value="create">Create Knowledge</TabsTrigger>
          </TabsList>
          
          {/* Universal Search Tab */}
          <TabsContent value="search" className="flex-1 flex flex-col space-y-4">
            <div className="space-y-2">
              <div className="flex space-x-2">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => handleKeyPress(e, performUniversalSearch)}
                  placeholder="Search across all knowledge sources..."
                  disabled={isSearching}
                  className="flex-1"
                />
                <Button
                  onClick={performUniversalSearch}
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
              
              <p className="text-xs text-muted-foreground">
                Searches MCP services, vector databases, and Notion knowledge base
              </p>
            </div>
            
            <ScrollArea className="flex-1">
              <div className="space-y-4">
                {searchResults.length === 0 && notionResults.length === 0 && !isSearching && (
                  <div className="text-center text-muted-foreground py-8">
                    <Brain className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Search the unified knowledge base</p>
                    <p className="text-sm">Includes memory, documents, and Notion pages</p>
                  </div>
                )}
                
                {/* MCP Service Results */}
                {searchResults.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-medium text-sm flex items-center space-x-2">
                      <Brain className="h-4 w-4" />
                      <span>Memory & Vector Results ({searchResults.length})</span>
                    </h3>
                    
                    {searchResults.map((result, index) => (
                      <Card key={`mcp-${index}`} className="p-3">
                        <div className="space-y-2">
                          <div className="flex items-start justify-between">
                            <h4 className="font-medium text-sm line-clamp-2">
                              {result.title || result.content?.substring(0, 50) + '...' || 'Memory Item'}
                            </h4>
                            <Badge variant="outline" className="text-xs ml-2">
                              {result.source || 'MCP'}
                            </Badge>
                          </div>
                          
                          {result.content && (
                            <p className="text-sm text-gray-700 line-clamp-3">
                              {result.content}
                            </p>
                          )}
                          
                          <div className="flex items-center space-x-2 pt-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => copyToClipboard(result.content || result.title || '')}
                              className="flex items-center space-x-1"
                            >
                              <Copy className="h-3 w-3" />
                              <span>Copy</span>
                            </Button>
                            
                            {onSendToChat && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => sendToChat(result.content || '', result.title)}
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
                )}
                
                {/* Notion Results */}
                {notionResults.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-medium text-sm flex items-center space-x-2">
                      <BookOpen className="h-4 w-4" />
                      <span>Notion Knowledge ({notionResults.length})</span>
                    </h3>
                    
                    {notionResults.map((result, index) => (
                      <Card key={`notion-${index}`} className="p-3">
                        <div className="space-y-2">
                          <div className="flex items-start justify-between">
                            <h4 className="font-medium text-sm line-clamp-2">
                              {result.title || 'Untitled Page'}
                            </h4>
                            <div className="flex items-center space-x-1 ml-2">
                              <Badge variant="secondary" className="text-xs">
                                Notion
                              </Badge>
                              {result.tags && result.tags.map((tag, tagIndex) => (
                                <Badge key={tagIndex} variant="outline" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          
                          {result.content && (
                            <p className="text-sm text-gray-700 line-clamp-3">
                              {result.content}
                            </p>
                          )}
                          
                          {result.created_time && (
                            <p className="text-xs text-muted-foreground">
                              Created: {formatTimestamp(result.created_time)}
                            </p>
                          )}
                          
                          <div className="flex items-center space-x-2 pt-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => window.open(result.url, '_blank')}
                              className="flex items-center space-x-1"
                            >
                              <ExternalLink className="h-3 w-3" />
                              <span>Open in Notion</span>
                            </Button>
                            
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => copyToClipboard(result.content || result.title || '')}
                              className="flex items-center space-x-1"
                            >
                              <Copy className="h-3 w-3" />
                              <span>Copy</span>
                            </Button>
                            
                            {onSendToChat && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => sendToChat(result.content || '', result.title)}
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
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          
          {/* Principles Tab */}
          <TabsContent value="principles" className="flex-1 flex flex-col space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">Pending Canonical Principles</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={loadPendingPrinciples}
                disabled={isLoadingPrinciples}
              >
                {isLoadingPrinciples ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            
            <ScrollArea className="flex-1">
              <div className="space-y-3">
                {pendingPrinciples.length === 0 && !isLoadingPrinciples && (
                  <div className="text-center text-muted-foreground py-8">
                    <Star className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No pending principles</p>
                    <p className="text-sm">All canonical principles have been reviewed</p>
                  </div>
                )}
                
                {pendingPrinciples.map((principle, index) => (
                  <Card key={index} className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-start justify-between">
                        <h4 className="font-medium text-sm">
                          {principle.title}
                        </h4>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-xs">
                            {principle.category}
                          </Badge>
                          <Badge className="bg-yellow-100 text-yellow-800 text-xs">
                            Pending
                          </Badge>
                        </div>
                      </div>
                      
                      {principle.description && (
                        <p className="text-sm text-gray-700">
                          {principle.description}
                        </p>
                      )}
                      
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Created: {formatTimestamp(principle.created_time)}</span>
                      </div>
                      
                      <div className="flex items-center space-x-2 pt-2">
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => approvePrinciple(principle.id)}
                          className="flex items-center space-x-1"
                        >
                          <CheckCircle className="h-3 w-3" />
                          <span>Approve</span>
                        </Button>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(principle.url, '_blank')}
                          className="flex items-center space-x-1"
                        >
                          <ExternalLink className="h-3 w-3" />
                          <span>View in Notion</span>
                        </Button>
                        
                        {onSendToChat && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => sendToChat(principle.description || '', principle.title)}
                            className="flex items-center space-x-1"
                          >
                            <MessageSquare className="h-3 w-3" />
                            <span>Discuss</span>
                          </Button>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
          
          {/* Create Knowledge Tab */}
          <TabsContent value="create" className="flex-1 flex flex-col space-y-4">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Title</label>
                <Input
                  value={newKnowledgeTitle}
                  onChange={(e) => setNewKnowledgeTitle(e.target.value)}
                  placeholder="Enter knowledge title..."
                  disabled={isCreating}
                />
              </div>
              
              <div className="flex-1 flex flex-col">
                <label className="text-sm font-medium mb-2 block">Content</label>
                <Textarea
                  value={newKnowledgeContent}
                  onChange={(e) => setNewKnowledgeContent(e.target.value)}
                  placeholder="Enter knowledge content..."
                  disabled={isCreating}
                  className="flex-1 min-h-[200px]"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Button
                  onClick={createKnowledgePage}
                  disabled={isCreating || !newKnowledgeTitle.trim() || !newKnowledgeContent.trim()}
                  className="flex items-center space-x-2"
                >
                  {isCreating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  <span>Save to Notion</span>
                </Button>
                
                <Button
                  variant="outline"
                  onClick={() => {
                    setNewKnowledgeTitle('')
                    setNewKnowledgeContent('')
                  }}
                  disabled={isCreating}
                >
                  Clear
                </Button>
              </div>
              
              <div className="text-xs text-muted-foreground">
                <p>Knowledge will be saved to the SOPHIA knowledge base in Notion.</p>
                <p>Use this to capture insights, procedures, or important information.</p>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

