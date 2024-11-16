'use client'

import Home from '@/components/home'
import { ProtectedRoute } from '@/components/protected-route'

export default function Component() {
  return (
    <ProtectedRoute>
      <Home />
    </ProtectedRoute>
  )
}