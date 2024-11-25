'use client'

import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'

export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { token } = useAuth()
  const router = useRouter()
  const [isProtected, setIsProtected] = useState(true)

  useEffect(() => {
    if (!token) {
      setIsProtected(true)
      router.push('/login') // Redirect to login if not authenticated
    } else {
      setIsProtected(false)
    }
  }, [token, router])

  return isProtected ? null : <>{children}</>
};
