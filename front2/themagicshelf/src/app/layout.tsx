import { AuthProvider } from "@/hooks/useAuth";
import "./globals.css";
import Menu from "@/components/menu";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-[#1a1a1a] text-green-400 font-mono bg-wooden-shelf bg-shelf-size bg-shelf-position bg-shelf-repeat">
        <AuthProvider>
          <main className="flex-1">
            <Menu />
            {children}
          </main>
        </AuthProvider>
        </div>
      </body>
    </html>
  )
}
