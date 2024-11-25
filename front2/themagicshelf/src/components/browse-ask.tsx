'use client'

import { useState, useCallback, useEffect, useMemo } from 'react'
import { ChevronRight, ChevronDown, Folder, FileText, Send, Terminal, ExternalLink, X } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Input } from "@/components/ui/input"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb"
import ReactMarkdown from 'react-markdown'
import { Card, CardContent } from './ui/card'
import axios from 'axios'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { useLocalStorage } from '@/hooks/useLocalStorage'
import { useAuth } from '@/hooks/useAuth'

type Document = {
  id: string
  title: string
  tags?: string[]
  summary?: string
  formattedSummary?: string
  relatedDocuments?: string[]
  source_node_id?: string
}

type Category = {
  id: string
  name: string
  introduction?: string
  subcategories?: Category[]
  documents?: Document[]
}


function CategoryItem({
  category,
  level = 0,
  onSelect,
  path = [],
  activeTags,
  onDocumentSelect
}: {
  category: Category;
  level?: number;
  onSelect: (category: Category, path: any[]) => void;
  path?: any[]
  activeTags: string[];
  onDocumentSelect: (document: Document) => void;
}) {
  const hasVisibleContent = (cat: Category, tags: string[]): boolean => {
    if (cat.documents && cat.documents.some(doc => tags.length === 0 || doc.tags?.some(tag => tags.includes(tag)))) {
      return true
    }
    return cat.subcategories ? cat.subcategories.some(subcat => hasVisibleContent(subcat, tags)) : false
  }

  const hasSubcategories = category.subcategories && category.subcategories.length > 0
  const [isExpanded, setIsExpanded] = useState(hasSubcategories)

  const toggleExpand = () => {
    if (!hasSubcategories) {
      setIsExpanded(!isExpanded)
    }
    onSelect(category, [...path, { id: category.id, name: category.name, type: 'category' }])
  }

  const filteredDocuments = category.documents?.filter(doc =>
    activeTags.length === 0 || doc.tags?.some(tag => activeTags.includes(tag))
  )

  const visibleSubcategories = category.subcategories?.filter(subcat =>
    hasVisibleContent(subcat, activeTags)
  )

  if (!hasVisibleContent(category, activeTags)) {
    return null
  }

  return (
    <div>
      <Button
        variant="ghost"
        className="w-full justify-start px-2 py-1 h-auto text-emerald-400 hover:text-emerald-300 hover:bg-black/20"
        onClick={toggleExpand}
      >
        <span className="mr-2 opacity-70">
          {hasSubcategories ? (
            <ChevronDown className="h-4 w-4" />
          ) : isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </span>
        <Folder className="h-4 w-4 mr-2" />
        <span className="font-mono">{category.name}</span>
      </Button>
      {(isExpanded || hasSubcategories) && (
        <div className="ml-4">
          {category.subcategories?.map(subcategory => (
            <CategoryItem
              key={subcategory.id}
              category={subcategory}
              level={level + 1}
              onSelect={onSelect}
              path={[...path, { id: category.id, name: category.name, type: 'category' }]}
              activeTags={activeTags}
              onDocumentSelect={onDocumentSelect}
            />
          ))}
          {filteredDocuments?.map(document => (
            <Button
              key={document.id}
              variant="ghost"
              className="w-full justify-start px-2 py-1 h-auto text-emerald-400 hover:text-emerald-300 hover:bg-black/20"
              onClick={() => {
                onSelect(category, [...path, { id: category.id, name: category.name, type: 'category' }, { id: document.id, name: document.title, type: 'document' }])
                onDocumentSelect(document)
              }}
            >
              <FileText className="h-4 w-4 mr-2 ml-6" />
              <span className="font-mono">{document.title}</span>
            </Button>
          ))}
        </div>
      )}
    </div>
  )
}

// remove markdown formatting not handled by react-markdown
function formatSummary(summary: string): string {
  // remove text between two stars
  // remove sequence of == more that 2
  return summary.replace(/\*\*(.*)\*\*/g, '').replace(/==+/g, '')
}

function DocumentDetails({ document, onDocumentSelect, allDocuments, runId }: {
  document: Document,
  onDocumentSelect: (document: Document) => void,
  allDocuments: Document[],
  runId: string
}) {
  const [sourceNodeInfo, setSourceNodeInfo] = useState<any>(null)
  const [formattedSummary, setFormattedSummary] = useState<string | null>(null)
  const { token } = useAuth() as any

  useEffect(() => {
    setFormattedSummary(formatSummary(document.summary || ''))
  }, [document.summary])

  const fetchNodeInfo = async () => {
    try {
      const res = await axios.get(`http://localhost:5000/source_node_info`, { 
        params: { 
          run_id: runId, 
          node_id: document.source_node_id 
        },
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      setSourceNodeInfo(res.data.source_node_info)
    } catch (err) {
      console.log(err)
    }
  }

  useEffect(() => {
    fetchNodeInfo()
  }, [document.source_node_id, runId])

  const relatedDocs = document.relatedDocuments?.map(id => allDocuments.find(doc => doc.id === id)).filter(Boolean) as Document[]
  return (
    <div className="text-emerald-400 font-mono">
      <h2 className="text-2xl font-bold mb-4">{document.title}</h2>
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Summary</h3>
        <p>{formattedSummary}</p>
      </div>
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Tags</h3>
        <div className="flex flex-wrap gap-2">
          {document.tags?.map(tag => (
            <span key={tag} className="px-2 py-1 bg-emerald-900 text-emerald-300 rounded">
              {tag}
            </span>
          ))}
        </div>
      </div>
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Related Documents</h3>
        <div className="space-y-2">
          {relatedDocs?.map(relatedDoc => (
            <Button
              key={relatedDoc.id}
              variant="ghost"
              className="w-full justify-start px-2 py-1 h-auto text-emerald-400 hover:text-emerald-300 hover:bg-black/20"
              onClick={() => onDocumentSelect(relatedDoc)}
            >
              <FileText className="h-4 w-4 mr-2" />
              <span className="font-mono">{relatedDoc.title}</span>
            </Button>
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-lg font-semibold mb-2">Source</h3>
        {document.source_node_id && sourceNodeInfo && (
          <Dialog>
          <DialogTrigger asChild>
            <Button variant="link" className="text-emerald-300 hover:text-emerald-200 flex items-center p-0">
              View original source
              <ExternalLink className="ml-2 h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-black/90 border-emerald-900 text-emerald-400 font-mono max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{document.title} - Source Content</DialogTitle>
            </DialogHeader>
            <DialogDescription></DialogDescription>
            {sourceNodeInfo?.url && (
              <a
                href={sourceNodeInfo?.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-emerald-300 hover:text-emerald-200 flex items-center"
              >
                Source URL
                <ExternalLink className="ml-2 h-4 w-4" />
              </a>
            )}
            {sourceNodeInfo?.file_name && (
              <p className="text-emerald-300 hover:text-emerald-200 flex items-center">
                Source File: {sourceNodeInfo?.file_name}
              </p>
            )}
            {sourceNodeInfo && (
              <ReactMarkdown className="prose prose-invert prose-emerald max-w-none">
                {sourceNodeInfo?.text + (sourceNodeInfo?.text_is_truncated ? '...' : '')}
              </ReactMarkdown>
            )}
          </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  )
}

export default function BrowseAskComponent() {
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null)
  const [selectedCategorySummary, setSelectedCategorySummary] = useState<string | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [selectedPath, setSelectedPath] = useState<any[]>([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [activeTags, setActiveTags] = useState<string[]>([])
  const [store, setStore] = useState<any>(null)
  const [nodes, setNodes] = useState<any>(null)
  const [edges, setEdges] = useState<any>(null)
  const [runId, setRunId] = useState('0')
  const { token, apiKey } = useAuth() as any
  const [message, setMessage] = useState('')

  useEffect(() => {
    setSelectedCategorySummary(formatSummary(selectedCategory?.introduction || ''))
  }, [selectedCategory?.introduction])

  const basicFetch = async (type: string, runId: string) => {
    try {
      const res = await axios.get(`http://localhost:5000/${type}`, { 
        params: { run_id: runId },
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
      return res.data
    } catch (err) {
      console.log(err)
    }
  }

  const fetchStore = async (runId: string) => {
    try {
      const storeData = await basicFetch("store", runId)
      const treeData = await basicFetch("tree", runId)
      const categoryTree = await basicFetch("category_tree", runId)

      setStore(storeData?.store)
      setNodes(treeData?.nodes)
      setCategories(categoryTree?.category_tree ? [categoryTree?.category_tree] : [])
      setEdges(treeData?.edges)
    } catch (err) {
      console.log(err)
    }
  }

  useEffect(() => {
    fetchStore(runId)
  }, [])

  const handleCategorySelect = useCallback((category: Category, path: any[]) => {
    setSelectedCategory(category)
    setSelectedPath(path)
    setSelectedDocument(null)
  }, [])

  const handleDocumentSelect = useCallback((document: Document) => {
    setSelectedDocument(document)
  }, [])

  const handleQuestionSubmit = async () => {
    if (question.trim() === '') return

    const generateAnswer = (q: string, response: string) => {
      return `> Processing query: "${q}"\n\nResponse: ${response}`
    }

    const res = await axios.get("http://localhost:5000/ask_query", {
      params: { run_id: runId, query: question, api_key: apiKey },
      headers: {
        Authorization: `Bearer ${token}`
      }
    }).then((res: any) => {
      const response = res.data.answer
      const generatedAnswer = generateAnswer(question, response)
      setAnswer(generatedAnswer)
      setQuestion('')
    }).catch((error) => {
      if (error.response && error.response.status === 401) {
        setMessage('Credits exhausted or API key not valid')
      } else {
        setMessage('Ask query failed')
      }
    })
  }

  const allTags = useMemo(() => {
    const tags = new Set<string>()
    const addTags = (category: Category) => {
      category.documents?.forEach(doc => doc.tags?.forEach(tag => tags.add(tag)))
      category.subcategories?.forEach(addTags)
    }
    categories.forEach(addTags)
    return Array.from(tags)
  }, [categories])

  const allDocuments = useMemo(() => {
    const docs: Document[] = []
    const addDocs = (category: Category) => {
      if (category.documents) docs.push(...category.documents)
      category.subcategories?.forEach(addDocs)
    }
    categories.forEach(addDocs)
    return docs
  }, [categories])

  const toggleTag = (tag: string) => {
    setActiveTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    )
  }

  return (
    <div className="container px-4 md:px-6 py-8 md:py-12 mx-auto">
      <div className="relative mx-auto max-w-8xl">
        <Card className="relative border-green-900/20 bg-black/80 shadow-lg shadow-green-900/5">
          <CardContent className="p-6 text-green-400">
            <div className="text-center space-y-2">
              <h1 className="text-4xl font-bold mb-4 text-center">NAVIGATE OR ASK</h1>
            </div>
            <div className="relative flex flex-col h-full bg-black/80">
              {/* Top panel - Breadcrumb */}
              <div className="p-4 border-b border-emerald-900/50 bg-black/40">
                <Breadcrumb>
                  <BreadcrumbList className="text-emerald-400 font-mono text-sm">
                    {selectedPath.map((item, index) => (
                      <BreadcrumbItem key={item.id}>
                        {index === selectedPath.length - 1 ? (
                          <BreadcrumbPage className="text-emerald-300" key={`${item.id}-page`}>/ {item.name}</BreadcrumbPage>
                        ) : (
                          <>
                            <BreadcrumbLink href={`#${item.id}`} className="text-emerald-400 hover:text-emerald-300" key={`${item.id}-link`}>
                              / {item.name}
                            </BreadcrumbLink>
                          </>
                        )}
                      </BreadcrumbItem>
                    ))}
                  </BreadcrumbList>
                </Breadcrumb>

                <div className="mt-2 flex flex-wrap gap-2">
                  {allTags.map(tag => (
                    <Button
                      key={tag}
                      variant="outline"
                      size="sm"
                      className={`font-mono text-xs ${activeTags.includes(tag)
                          ? 'bg-emerald-900 text-emerald-300'
                          : 'bg-black/50 text-emerald-400 hover:bg-emerald-900/50'
                        }`}
                      onClick={() => toggleTag(tag)}
                    >
                      {tag}
                      {activeTags.includes(tag) && <X className="ml-1 h-3 w-3" />}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Main content area */}
              <div className="flex flex-1 min-h-0">
                {/* Left panel - Directory tree */}
                <ScrollArea className="w-1/3 p-4 border-r border-emerald-900/50">
                  <div className="space-y-2">
                    {categories.map(category => (
                      <CategoryItem
                        key={category.id}
                        category={category}
                        onSelect={handleCategorySelect}
                        activeTags={activeTags}
                        onDocumentSelect={handleDocumentSelect}
                      />
                    ))}
                  </div>
                </ScrollArea>

                {/* Right panel - Content display */}
                <div className="w-2/3 p-4 flex flex-col">
                  <ScrollArea className="flex-1">
                    {selectedDocument ? (
                      <DocumentDetails
                        document={selectedDocument}
                        onDocumentSelect={handleDocumentSelect}
                        allDocuments={allDocuments}
                        runId={runId} 
                      />
                    ) : selectedCategory ? (
                      <ReactMarkdown className="prose prose-invert prose-emerald max-w-none font-mono">
                        {selectedCategorySummary || 'No introduction available for this category.'}
                      </ReactMarkdown>
                    ) : (
                      <div className="text-emerald-400 font-mono">
                        <Terminal className="w-8 h-8 mb-2 animate-pulse" />
                        <p>Select a category or document to view its details.</p>
                      </div>
                    )}
                  </ScrollArea>
                </div>
              </div>

              {/* Bottom panel - Q&A Interface */}
              <div className="p-4 border-t border-emerald-900/50 bg-black/40">
                <div className="font-mono text-emerald-400 mb-2 flex items-center gap-2">
                  <Terminal className="w-4 h-4" />
                  <span>Query Interface</span>
                </div>
                <div className="flex space-x-2">
                  <Input
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Type your query here..."
                    onKeyPress={(e) => e.key === 'Enter' && handleQuestionSubmit()}
                    className="font-mono bg-black/50 border-emerald-900 text-emerald-400 placeholder:text-emerald-700"
                  />
                  <Button
                    onClick={handleQuestionSubmit}
                    className="bg-green-900/20 border border-green-500/20 hover:bg-green-900/40 text-green-400 shadow-lg shadow-green-900/10"
                  >
                    <Send className="h-4 w-4 mr-2" />
                    Ask
                  </Button>
                </div>
                {answer && (
                  <div className="mt-4 font-mono">
                    <pre className="text-emerald-400 bg-black/50 p-4 rounded-md border border-emerald-900 whitespace-pre-wrap">
                      {answer}
                    </pre>
                  </div>
                )}
                {message && (
                  <div className="mt-4 font-mono text-red-400">
                    {message}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
