import "./globals.css";
import { BookOpen } from "lucide-react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-[#1a1a1a] text-green-400 font-mono bg-wooden-shelf bg-shelf-size bg-shelf-position bg-shelf-repeat">
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
        </nav>
      </header>
      <main className="flex-1">
          {children}
        </main>
        </div>
      </body>
    </html>
  )
}
