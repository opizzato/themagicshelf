'use client'

import { BookOpen, Menu } from "lucide-react";
import Link from "next/link";

function Component() {

  return (
    <header className="px-4 lg:px-6 h-14 flex items-center border-b border-[#00ff00]/20 bg-black/80">
      <Link className="flex items-center justify-center group" href="/">
          <BookOpen className="h-6 w-6 mr-2 group-hover:text-green-400 transition-colors" />
          <span className="font-bold tracking-wider text-green-400 group-hover:text-green-400 transition-colors">THE MAGIC SHELF</span>
        </Link>
        <nav className="ml-auto flex gap-4 sm:gap-6">
          <Link 
            className="text-sm tracking-wide hover:text-[#66ff66] transition-colors" 
            href="/input"
          >
            [INPUT DOCUMENTS]
          </Link>
          <Link 
            className="text-sm tracking-wide hover:text-[#66ff66] transition-colors" 
            href="/browse-ask"
          >
            [NAVIGATE OR ASK]
          </Link>
          <Link 
            className="text-sm tracking-wide hover:text-[#66ff66] transition-colors" 
            href="/about"
          >
            [ABOUT]
          </Link>
            <Link 
              className="text-sm tracking-wide hover:text-[#66ff66] transition-colors" 
              href="/profile"
            >
              [PROFILE]
            </Link>
        </nav>
    </header>
  )
}

export default Component
