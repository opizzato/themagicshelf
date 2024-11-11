'use client'

import Link from 'next/link'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { BookOpen, FileInput, MessageSquare, Quote, Volume2, VolumeX } from "lucide-react"
import { useEffect, useRef, useState } from "react"

export default function Component() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (isPlaying && audioRef.current) {
      audioRef.current.play();
    }
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    };
  }, [isPlaying]);

  const toggleAudio = () => {
    setIsPlaying(!isPlaying);
  };

  return (
        <div className="container px-4 md:px-6 py-8 md:py-12 mx-auto">
          <audio ref={audioRef}>
            <source src="/intro.mp3" type="audio/mpeg" />
            Your browser does not support the audio element.
          </audio>

          <div className="relative mx-auto max-w-8xl">
            <Card className="relative border-green-900/20 bg-black/80 shadow-lg shadow-green-900/5">
              <CardContent className="p-6 text-green-400">
                <div className="space-y-8">
                  <div className="text-center space-y-2">
                  <h1 className="text-4xl font-bold mb-4 text-center animate-pulse">THE MAGIC SHELF</h1>
                  <Button 
                        onClick={toggleAudio}
                        className="bg-green-900/20 border border-green-500/20 hover:bg-green-900/40 text-green-400 shadow-lg shadow-green-900/10">
                        {isPlaying ? (
                          <VolumeX className="h-8 w-8 md:h-10 md:w-10" />
                        ) : (
                          <Volume2 className="h-8 w-8 md:h-10 md:w-10" />
                        )}
                      </Button>                  </div>
                  <div className="space-y-4 font-mono text-sm md:text-base leading-relaxed">

                  <pre className="text-green-400 text-center mt-8 mb-8 font-mono">
{`Human            AI
 (o_o)          (•_•)
 <| |>----------<| |>
 /   \\          /   \\
\\___________/
 Documents`}
                    </pre>


                    <p className="">
                      Welcome to <span className="text-yellow-300">THE MAGIC SHELF</span>!
                    </p>
                    <p className="">
                      <span className="text-yellow-300">THE MAGIC SHELF</span> is a virtual bookshelf that re-organizes your documents in a <span className="text-yellow-300">win-win RAG</span> way.
                    </p>
                    <p className="">
                      Documents are prepared the same way <span className='text-yellow-300'>for human browsing</span> and <span className='text-yellow-300'>for AI assistant retrieval</span>.
                    </p>


                    <pre className="text-green-400 text-center mt-8 mb-8 font-mono">
{`   

Human     links between docs <------------------> embeddings        AI
  (o_o)      doc summary <----------------------> summary nodes       (•_•)
   shelf structure <-------> classification retrieval  


`}
                    </pre>


                    <p className="">
                      1. First, you need to <span className="text-yellow-300">INPUT DOCUMENTS</span>. You can upload pdf files, add web pages or use preprocessed documents.
                    </p>
                    <p className="">
                      2. Then you can <span className="text-yellow-300">NAVIGATE</span> the classification index <span className="text-yellow-300">OR ASK</span> questions to the AI assistant.
                    </p>
                    <br />
                    <div className="text-center">
                      <div className="flex justify-center mb-4">
                        <Quote className="text-green-400 w-4 h-4" />
                      </div>
                      <span className="text-yellow-300">
                      What is good for LLM is good for human, and vice versa.
                      </span>
                      <br />
                      - Anonymous
                    </div>
                    
                    <div className="flex items-center space-x-2 text-green-400/80">
                      <span className="w-2 h-4 bg-green-400" />
                    </div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Button 
                      asChild
                      className="bg-green-900/20 border border-green-500/20 hover:bg-green-900/40 text-green-400 shadow-lg shadow-green-900/10"
                    >
                      <Link href="/input" className="space-x-2">
                        <FileInput className="h-4 w-4" />
                        <span>INPUT DOCUMENTS</span>
                      </Link>
                    </Button>
                    <Button 
                      asChild
                      className="bg-green-900/20 border border-green-500/20 hover:bg-green-900/40 text-green-400 shadow-lg shadow-green-900/10"
                    >
                      <Link href="/browse-ask" className="space-x-2">
                        <MessageSquare className="h-4 w-4" />
                        <span>NAVIGATE OR ASK</span>
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          <style jsx global>{`
        @keyframes typing {
          from { width: 0 }
          to { width: 100% }
        }
        
        @keyframes blink {
          0%, 100% { opacity: 1 }
          50% { opacity: 0 }
        }
        
        .typing-effect {
          overflow: hidden;
          white-space: nowrap;
          animation: typing 2s steps(40, end);
        }
        
        .typing-effect-2 {
          overflow: hidden;
          white-space: nowrap;
          animation: typing 2s steps(40, end);
          animation-delay: 2s;
          animation-fill-mode: backwards;
        }
        
        .typing-effect-3 {
          overflow: hidden;
          white-space: nowrap;
          animation: typing 2s steps(40, end);
          animation-delay: 4s;
          animation-fill-mode: backwards;
        }
        
        .animate-blink {
          animation: blink 1s step-end infinite;
        }
      `}</style>
    </div>
  )
}