'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuth } from '@/hooks/useAuth'
import axios from 'axios'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

export default function Component() {
  const [mode, setMode] = useState<'login' | 'register' | 'reset'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const { login } = useAuth() as any

  const loginQuery = async () => {
    setMessage('')
    const formData = new FormData();
    formData.append("email", email);
    formData.append("password", password);
    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_REST_URL}/login`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).catch((error) => {
      setMessage(error.response.data.error)
    })
    console.log('response', response)
    login(response?.data?.data)
  }

  const registerQuery = async () => {
    setMessage('')
    const formData = new FormData();
    formData.append("email", email);
    formData.append("password", password);
    formData.append("confirm_password", confirmPassword);
    const response = await axios.post(`${process.env.NEXT_PUBLIC_API_REST_URL}/register`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }).then((response: any) => {
      setMessage('Account created successfully')
    }).catch((error) => {
      setMessage(error.response.data.error)
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    switch (mode) {
      case 'login':
        loginQuery()
        break
      case 'register':
        registerQuery()
        break
      case 'reset':
        console.log('Resetting password...', { email })
        break
    }
  }

  const renderForm = () => {
    switch (mode) {
      case 'login':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="email" className="sr-only">Email</Label>
              <Input
                id="email"
                placeholder="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-black/50 border-green-700 text-green-400 placeholder-green-700"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="sr-only">Password</Label>
              <Input
                id="password"
                placeholder="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-black/50 border-green-700 text-green-400 placeholder-green-700"
              />
            </div>
            <Button type="submit" className="w-full bg-green-700 hover:bg-green-600 text-black font-bold">
              Enter
            </Button>
            {message && (
              <Alert className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{message}</AlertDescription>
              </Alert>
            )}
          </>
        )
      case 'register':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="email" className="sr-only">Email</Label>
              <Input
                id="email"
                placeholder="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-black/50 border-green-700 text-green-400 placeholder-green-700"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="sr-only">Password</Label>
              <Input
                id="password"
                placeholder="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-black/50 border-green-700 text-green-400 placeholder-green-700"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="sr-only">Confirm Password</Label>
              <Input
                id="confirmPassword"
                placeholder="Confirm Password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="bg-black/50 border-green-700 text-green-400 placeholder-green-700"
              />
            </div>
            <Button type="submit" className="w-full bg-green-700 hover:bg-green-600 text-black font-bold">
              Create Account
            </Button>
            {message && (
              <Alert className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{message}</AlertDescription>
              </Alert>
            )}
          </>
        )
      case 'reset':
        return (
          <>
            <div className="space-y-2">
              <Label htmlFor="email" className="sr-only">Email</Label>
              <Input
                id="email"
                placeholder="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-black/50 border-green-700 text-green-400 placeholder-green-700"
              />
            </div>
            <Button type="submit" className="w-full bg-green-700 hover:bg-green-600 text-black font-bold">
              Reset Password
            </Button>
            {message && (
              <Alert className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{message}</AlertDescription>
              </Alert>
            )}
          </>
        )
    }
  }

  return (
    <div className="container px-4 md:px-6 py-8 md:py-12 mx-auto">
      <Card className="relative border-green-900/20 bg-black/80 shadow-lg shadow-green-900/5">
        <CardContent className="p-6 text-green-400">
          <div className="flex-grow flex items-center justify-center p-8">
            <Card className="w-full max-w-md bg-black/70 border-0">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-bold text-green-400">
                  {mode === 'login' ? 'Access the Magic Shelf' :
                    mode === 'register' ? 'Join the Magic Shelf' :
                      'Reset Your Password'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  {renderForm()}
                </form>
                {/* {message && (
                  <Alert className="mt-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{message}</AlertDescription>
                  </Alert>
                )} */}
                <div className="mt-4 text-center space-y-2">
                  {mode === 'login' && (
                    <Button
                      variant="link"
                      onClick={() => setMode('reset')}
                      className="text-green-400 hover:text-green-300"
                    >
                      Forgot Password?
                    </Button>
                  )}
                  <Button
                    variant="link"
                    onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
                    className="text-green-400 hover:text-green-300"
                  >
                    {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Login'}
                  </Button>
                  {mode !== 'login' && (
                    <Button
                      variant="link"
                      onClick={() => setMode('login')}
                      className="text-green-400 hover:text-green-300"
                    >
                      Back to Login
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}