'use client'

import { useState, useEffect } from 'react'
import { Plus, Trash2, Upload, Search, Link, Import, Play, CheckCircle2, AlertCircle } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Card, CardContent } from './ui/card'
import { DialogDescription } from '@radix-ui/react-dialog'
import axios from 'axios'

const PREPROCESSED_CULTURE_URLS = [
  "https://text.npr.org/g-s1-29121",
  "https://text.npr.org/nx-s1-5185232",
  "https://text.npr.org/nx-s1-5181907",
]

const PREPROCESSED_NEWS_URLS = [
  "https://neuters.de/business/healthcare-pharmaceuticals/british-columbia-detects-first-presumptive-human-h5-bird-flu-case-canada-2024-11-10/",
  "https://neuters.de/business/environment/who-are-key-voices-cop29-climate-summit-baku-2024-11-09/",
  "https://neuters.de/sustainability/climate-energy/brazil-announces-new-climate-change-pledge-ahead-cop29-summit-2024-11-09/",
]

type Document = {
  id: string
  title: string
  type: 'pdf' | 'web' | 'url' | 'preprocessed'
  processed: boolean
  file?: File
  preprocessedType?: string
  url?: string
}

export default function InputComponent() {
  const [runId, setRunId] = useState(0)
  const [documents, setDocuments] = useState<Document[]>([])
  const [url, setUrl] = useState('')
  const [preprocessedType, setPreprocessedType] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [terminalText, setTerminalText] = useState('Welcome to the Magic Shelf!\nAwaiting your command...')
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [fetching, setFetching] = useState(false);
  const [fetchedLogs, setFetchedLogs] = useState<string[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [newLogs, setNewLogs] = useState<string[]>([]);
  const [intervalId, setIntervalId] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const newLogLines = fetchedLogs.filter((line) => !logs.includes(line))
    setNewLogs(newLogLines)
    setLogs(fetchedLogs)
  }, [fetchedLogs])

  useEffect(() => {
    if (newLogs.length > 0) {
      updateTerminal(newLogs.join("\n> "))
    }
  }, [newLogs])

  const fetchInputs = async () => {
    const res = await axios.get("http://localhost:5000/document_sources", {
      params: { run_id: runId }
    });
    console.log('fetchInputs', res.data);
    setDocuments(res.data.document_sources.map((doc: any) => ({
      ...doc,
      title: shortenAStringByRemovingCharsInTheMiddle(doc.title, 80),
    })))
  }

  useEffect(() => {
    fetchInputs()
  }, [])

  const fetchProcessingLogs = async () => {
    try {
      const res = await axios.get("http://localhost:5000/processing_logs");
      console.log('fetchProcessingLogs', res.data);

      setFetchedLogs(res?.data?.logs || []);

      if (res?.data?.status == "completed" || res?.data?.status == "failed") {
        setFetching(false);
        if (intervalId) {
          clearInterval(intervalId);
        }
        setDocuments(prevDocs => prevDocs.map(doc => ({ ...doc, processed: true })))
        setIsProcessing(false)
      }
    } catch (err: any) {
      setFetchedLogs([
        ...logs,
        "Error fetching results: " + err.message,
      ]);
      setFetching(false);
      if (intervalId) {
        clearInterval(intervalId);
      }
      console.error('Error processing documents:', err);
      setIsProcessing(false);
    }
  };

  // loop to fetch processing pipeline logs
  useEffect(() => {
    if (fetching === true) {
      const intervalId = setInterval(() => {
        fetchProcessingLogs();
      }, 1000);
      setIntervalId(intervalId);

      return () => clearInterval(intervalId);
    }
  }, [fetching]);

  const addNotification = (message: string, type: 'success' | 'error') => {
    const id = Date.now().toString() + "-" + Math.random().toString(36).substring(2, 15)
    setNotifications(prev => [...prev, new Notification(message, { body: message, icon: type === 'success' ? '🟢' : '🔴', data: { id, type, body: message } })])
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.data.id !== id))
    }, 3000)
  }

  const shortenAStringByRemovingCharsInTheMiddle = (str: string, maxLength: number) => {
    if (str.length <= maxLength) return str;
    const halfLength = Math.floor((maxLength - 3) / 2);
    return str.substring(0, halfLength) + '...' + str.substring(str.length - halfLength);
  }

  const updateTerminal = (text: string) => {
    setTerminalText(prev => `${prev}\n> ${text}`)
  }

  const addDocument = (newDoc: Document) => {
    setDocuments([...documents, newDoc])
    updateTerminal(`Added document: ${newDoc.title}`)
    addNotification(`${newDoc.title} added.`, 'success')
  }

  const addDocuments = (newDocs: Document[]) => {
    const notDuplicateDocs = newDocs.filter((doc) => !documents.some((existingDoc) => existingDoc.id === doc.id)) 
    setDocuments([...documents, ...notDuplicateDocs])
    updateTerminal(`Added ${notDuplicateDocs.length} documents.`)
    addNotification(`${notDuplicateDocs.length} documents added.`, 'success')
  }

  const removeDocument = async (id: string) => {
    const doc = documents.find(d => d.id === id)
    console.log("removing doc :", doc)

    if (doc?.type === 'pdf') {
      const response = await axios.post("http://localhost:5000/remove_uploaded_file", null, {
        params: { 
          run_id: runId,
          file_name: doc.title,
        },
      });
      console.log("removeDocument response :", response)
    }

    setDocuments(documents.filter(doc => doc.id !== id))
    updateTerminal(`Removed document: ${doc?.title}`)
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type === 'application/pdf') {
      addDocument({
        id: Date.now().toString(),
        title: file.name,
        type: 'pdf',
        processed: false,
        file: file
      })
    } else {
      updateTerminal('ERROR: Please upload a PDF file')
    }
  }

  const handleUrlImport = () => {
    if (url) {
      addDocument({
        id: Date.now().toString(),
        title: `URL: ${shortenAStringByRemovingCharsInTheMiddle(url, 80)}`,
        type: 'url',
        processed: false,
        url: url
      })
      setUrl('')
    }
  }

  const handlePreprocessedImport = () => {
    if (preprocessedType) {
      if (preprocessedType === "culture") {
        addDocuments(PREPROCESSED_CULTURE_URLS.map((url, index) => ({
            id: url,
            title: `URL: ${shortenAStringByRemovingCharsInTheMiddle(url, 80)}`,
            type: 'preprocessed',
            preprocessedType: preprocessedType,
            processed: false,
            url: url
          }))
        )
      } else if (preprocessedType === "news") {
        addDocuments(PREPROCESSED_NEWS_URLS.map((url, index) => ({
            id: url,
            title: `URL: ${shortenAStringByRemovingCharsInTheMiddle(url, 80)}`,
            type: 'preprocessed',
            preprocessedType: preprocessedType,
            processed: false,
            url: url
          }))
        )
      }
      setPreprocessedType('')
    }
  }

  const processFiles = async () => {
    console.log("processFiles")
    const formData = new FormData();
    documents.forEach((doc, index) => {
      if (doc.file) {
        formData.append('files', doc.file, doc.title);
      }
    });
    const responseForFiles = await axios.post("http://localhost:5000/upload-files", formData, {
      params: { 
        run_id: runId,
      },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    console.log("responseForFiles :", responseForFiles)
  }

  const processUrls = async () => {
    console.log("processUrls")
    const formData = new FormData();
    formData.append("urls", documents.filter((doc) => doc.type === 'url' || doc.type === 'preprocessed').map((doc) => doc.url).join(","));
    formData.append("max_document_size", "100000");
    const response = await axios.post("http://localhost:5000/add-urls", formData, {
      params: {
        run_id: runId,
      },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    console.log("responseForUrls :", response)
  }

  const processDocuments = async () => {
    console.log("processDocuments", documents)
    setIsProcessing(true)
    updateTerminal('Initiating document processing sequence...')

    try {
      await processFiles()
      await processUrls()

      const res = await axios.get("http://localhost:5000/launch_run", {
        params: { 
          run_id: runId, 
        },
      });
      console.log("res :", res)
      setLogs([])
      setFetching(true)

    } catch (error) {
      console.error('Error processing documents:', error);
      setIsProcessing(false);
      updateTerminal('An error occurred while processing documents.');
    }
  }

  return (
    <div className="container px-4 md:px-6 py-8 md:py-12 mx-auto">
      <div className="relative mx-auto max-w-8xl">

        <Card className="relative border-green-900/20 bg-black/80 shadow-lg shadow-green-900/5">
          <CardContent className="p-6 text-green-400">

            <h1 className="text-4xl font-bold mb-4 text-center">INPUT DOCUMENTS</h1>

            <div className="flex space-x-2 mb-4">
              <Dialog>
                <DialogDescription></DialogDescription>
                <DialogTrigger asChild>
                  <Button className="bg-green-900 hover:bg-green-800 text-green-400 border border-green-400">
                    <Plus className="mr-2 h-4 w-4" /> Add document source
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-[#0a0a0a] border-green-400 text-green-400">
                  <DialogHeader>
                    <DialogTitle>ADD SOURCE</DialogTitle>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label className="text-right">Add PDF</Label>
                      <Input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileUpload}
                        className="col-span-3 bg-[#1a1a1a] border-green-400 text-green-400"
                      />
                    </div>
                    <br />

                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label htmlFor="url" className="text-right">
                        Webpage URL
                      </Label>
                      <Input
                        id="url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://example.com"
                        className="col-span-3"
                      />
                    </div>
                    <Button onClick={handleUrlImport} disabled={!url}>
                      <Link className="mr-2 h-4 w-4" /> Add Webpage
                    </Button>
                    <br />

                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label htmlFor="preprocessed" className="text-right">
                        Preprocessed
                      </Label>
                      <Select onValueChange={setPreprocessedType} value={preprocessedType}>
                        <SelectTrigger className="col-span-3">
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="culture">Culture</SelectItem>
                          <SelectItem value="news">News</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button onClick={handlePreprocessedImport} disabled={!preprocessedType}>
                      <Import className="mr-2 h-4 w-4" /> Add Preprocessed
                    </Button>
                  </div>

                  {notifications.length > 0 && (
                    <div className="mb-4 space-y-2">
                      {notifications.map((notification) => (
                        <div
                          key={notification.data.id}
                          className={`flex items-center p-2 rounded-md ${
                            notification.data.type === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          }`}
                        >
                          {notification.data.type === 'success' ? (
                            <CheckCircle2 className="w-4 h-4 mr-2" />
                          ) : (
                            <AlertCircle className="w-4 h-4 mr-2" />
                          )}
                          <span className="text-sm">{notification.data.body}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </DialogContent>
              </Dialog>
              <Button
                onClick={processDocuments}
                disabled={isProcessing || documents.length === 0}
                className="bg-green-900 hover:bg-green-800 text-green-400 border border-green-400 disabled:opacity-50"
              >
                <Play className="mr-2 h-4 w-4" /> Process
              </Button>
            </div>
            <div className="border border-green-400 rounded-lg overflow-hidden mb-4">
              <table className="min-w-full divide-y divide-green-400">
                <thead className="bg-green-900 bg-opacity-20">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Title</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-green-400">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="bg-[#0a0a0a]">
                      <td className="px-6 py-4 whitespace-nowrap">{doc.title}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{doc.type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${doc.processed
                            ? 'bg-green-900 text-green-400'
                            : 'bg-yellow-900 text-yellow-400'
                          }`}>
                          {doc.processed ? 'PROCESSED' : 'PENDING'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => removeDocument(doc.id)}
                          className="bg-red-900 hover:bg-red-800 text-red-400 border border-red-400"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="border border-green-400 rounded-lg p-4 bg-[#0a0a0a] font-mono">
              <div className="text-sm whitespace-pre-wrap">
                {terminalText.split('\n').map((line, i) => (
                  <div key={i} className={i === terminalText.split('\n').length - 1 ? 'animate-pulse' : ''}>
                    {line}
                  </div>
                ))}
              </div>
            </div>


          </CardContent>
        </Card>

      </div>
    </div>
  )
}