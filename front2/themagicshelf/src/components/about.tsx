'use client'

import Link from 'next/link'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { BookOpen, FileInput, MessageSquare, Volume2, VolumeX } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from '@/components/ui/carousel'

export default function Component() {
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
      setMounted(true)
    }, [])

    if (!mounted) return null

    return (
        <div className="container px-4 md:px-6 py-8 md:py-12 mx-auto">
        <Card className="relative border-green-900/20 bg-black/80 shadow-lg shadow-green-900/5">
        <CardContent className="p-6 text-green-400">
        <div className="text-center space-y-2">
                  <h1 className="text-4xl font-bold mb-4 text-center">ABOUT</h1>
              </div>

        <Carousel className="w-full max-w-4xl mx-auto">
          <CarouselContent>
            {slides.map((slide, index) => (
              <CarouselItem key={index}>
                <DocumentationSlide {...slide} />
              </CarouselItem>
            ))}
          </CarouselContent>
          <CarouselPrevious className="bg-green-400 text-black hover:bg-green-300" />
          <CarouselNext className="bg-green-400 text-black hover:bg-green-300" />
        </Carousel>
        </CardContent>
      </Card>
      </div>
    )
}


function DocumentationSlide({ title, content, asciiArt }: { title: string; content: string; asciiArt: string }) {
    return (
        <>
          <h3 className="text-2xl font-semibold mb-4 text-green-400">{title}</h3>
          <p className="mb-6 text-green-200">{content}</p>
          <pre className="font-mono text-xs leading-tight overflow-x-auto p-4 bg-green-900/20 rounded-md text-green-400 animate-glow">
            {asciiArt}
          </pre>
        </>
    )
  }
  
  const slides = [
    {
      title: "1. A shelf and a RAG  ",
      content: "The Magic Shelf is a summarization and classification system for humans and a Retrieval-Augmented Generation system for LLM.",
      asciiArt: `

  ┌───────────────────────────────────────────┐        
  │             Document Collection           │        
  └──────────────────────┬────────────────────┘        
                         ↓                                                  
               ┌──────────────────┐                                         
               │       Text       │                                         
               │     Chunking     │                                         
               └─────────┬────────┘                                         
              ┌──────────┴────────┐                                         
              ↓                   ↓                                         
  ┌────────────────────┐ ┌────────────────────┐                             
  │     Embedding      │ │    Summarization   │                             
  │     Pipeline       │ │      Pipeline      │                             
  └────────┬───────────┘ └────────┬───────────┘                             
           │                      ↓                                         
           │             ┌────────────────────┐                               
           │             │  Classification    │                               
           │             │     Pipeline       │                     Human
           │             └────────┬───────────┘                     (o_o)      
           ↓                      ↓                                        
  ┌────────────────────┐ ┌────────────────────┐          ┌────────────┐  ┌─────────┐
  │       Vector       │ │    Hierarchical    │←─────────┤  Navigate  │  │   Ask   │
  │       Store        │ │      Index         │          └────────────┘  └─────────┘
  └────────┬───────────┘ └────────┬───────────┘                               │
           │                      │                                           │
  ┌────────┴───────────┐ ┌────────┴───────────┐                               │
  │      Semantic      │ │   Classification   │                               │
  │      Retrieval     │ │     Retrieval      │                               │
  └─────────┬──────────┘ └────────┬───────────┘                               │
            └──────────┬──────────┘                                           │
                       ↓                                                      ↓
          ┌────────────────────────┐                     ┌─────────────────────────┐
          │      Combined          │←────────────────────┤    Query Augmentation   │
          │      Retrieval         │                     │       with Context      │
          └────────────────────────┘                     └────────────┬────────────┘
                                                                      ↓   
                                                         ┌─────────────────────────┐
                                                         │      LLM Response       │
                                                         │      Generation         │
                                                         └─────────────────────────┘

  └──────────────────────┬────────────────────┘                      AI
                        RAG                                         (•_•)
      `,
    },
    {
      title: "Document Management",
      content: "Effortlessly add or remove documents from your shelf. Magic Shelf's advanced algorithms take care of organizing and classifying your files automatically.",
      asciiArt: `

                    
What is good for LLM is good for human, and vice versa
- Anonymous


      `,
    },
    {
      title: "Smart Classification",
      content: "Navigate through a futuristic hierarchy of your documents. Explore holographic tags and quantum summaries to instantly find the information you need.",
      asciiArt: `
     ______               _  __ _           _   _             
    / ____| |             (_)/ _(_)         | | (_)            
   | |    | | __ _ ___ ___ _| |_ _  ___ __ _| |_ _  ___  _ __  
   | |    | |/ _' / __/ __| |  _| |/ __/ _' | __| |/ _ \\| '_ \\ 
   | |____| | (_| \\__ \\__ \\ | | | | (_| (_| | |_| | (_) | | | |
    \\_____|_|\\__,_|___/___/_|_| |_|\\___\\__,_|\\__|_|\\___/|_| |_|
      `,
    },
    {
      title: "Intelligent Q&A",
      content: "Engage in a dialogue with the future. Ask questions about your documents and receive accurate answers from our AI-powered chatbot that understands the context of your entire library.",
      asciiArt: `
     ____    ___    
    / __ \\  / _ \\   
   | |  | |/ /_\\ \\  
   | |  | |  _  |   
   | |__| | | | |_  
    \\___\\_\\_| |_(_) 
      `,
    },
  ]
