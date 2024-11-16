'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Leaf, RotateCcw, AlertTriangle, LogOut, Link, MessageSquare } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Separator } from "@/components/ui/separator"
import axios from 'axios'
import { useAuth } from '@/hooks/useAuth'

export default function ProfilePage() {
  const [email] = useState('user@example.com')
  const [apiKey, setApiKey] = useState('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
  const [apiCalls, setApiCalls] = useState(1234)
  const [carbonFootprint, setCarbonFootprint] = useState(5.67)
  const [startTime, setStartTime] = useState(new Date())
  const [apiCallThreshold, setApiCallThreshold] = useState(1000)
  const [carbonFootprintThreshold, setCarbonFootprintThreshold] = useState(5)
  const { logout } = useAuth() as any
  const [message, setMessage] = useState('')
  
  const handleApiKeyChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setApiKey(event.target.value)
  }

  const handleSaveApiKey = () => {
    console.log('Saving API key:', apiKey)
  }

  const handleResetCounters = () => {
    setApiCalls(0)
    setCarbonFootprint(0)
    setStartTime(new Date())
  }

  const handleApiCallThresholdChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setApiCallThreshold(Number(event.target.value))
  }

  const handleCarbonFootprintThresholdChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCarbonFootprintThreshold(Number(event.target.value))
  }

  const logoutQuery = async () => {
    const response = await axios.post("http://localhost:5000/logout", {
      username: email,
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    if (response.status === 200) {
      console.log('logout', logout)
      logout(response.data.data)
    } else {
      setMessage('Logout failed')
    }
  }

  const handleLogout = () => {
    console.log('Logging out...')
    logoutQuery()
  }


  return (
    <div className="container px-4 md:px-6 py-8 md:py-12 mx-auto">
      <div className="relative mx-auto max-w-8xl">
      <Card className="relative border-green-900/20 bg-black/80 shadow-lg shadow-green-900/5">
        <CardContent className="p-6 text-green-400">

        <h1 className="text-4xl font-bold mb-4 text-center">PROFILE</h1>

          <div className="space-y-2">
            <Label htmlFor="email" className="font-mono text-green-500">{'>'} email</Label>
            <Input 
              id="email" 
              value={email} 
              readOnly 
              className="font-mono border-green-500/20 bg-black/50 text-green-500"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="api-key" className="font-mono text-green-500">{'>'} api_key</Label>
            <div className="flex space-x-2">
              <Input 
                id="api-key" 
                value={apiKey} 
                onChange={handleApiKeyChange} 
                className="font-mono border-green-500/20 bg-black/50 text-green-500"
              />
              <Button 
                onClick={handleSaveApiKey}
                className="border-green-500 bg-green-500/20 text-green-500 hover:bg-green-500/30"
              >
                save
              </Button>
            </div>
          </div>
          {/* <Separator className="border-green-500/20" /> */}
          <div className="space-y-4 mt-4">
            <div className="flex justify-between items-center">
              <Label className="font-mono text-green-500 text-lg">{'>'} system_metrics</Label>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleResetCounters}
                className="bg-green-900/20 border border-green-500/20 hover:bg-green-900/40 text-green-400 shadow-lg shadow-green-900/10"
                >
                <RotateCcw className="w-4 h-4 mr-2" />
                reset
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="api-calls-threshold" className="font-mono text-green-500">
                  {'>'} api_calls_threshold
                </Label>
                <Input 
                  id="api-calls-threshold"
                  type="number"
                  value={apiCallThreshold}
                  onChange={handleApiCallThresholdChange}
                  className="font-mono border-green-500/20 bg-black/50 text-green-500"
                />
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center space-x-2 p-2 bg-black/50 border border-green-500/20 rounded-md">
                        <span className="font-mono text-2xl text-green-500">
                          {apiCalls.toLocaleString()}
                        </span>
                        {apiCalls > apiCallThreshold && (
                          <AlertTriangle className="w-6 h-6 text-yellow-500" />
                        )}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent className="font-mono bg-black text-green-500 border-green-500">
                      <p>current: {apiCalls.toLocaleString()}</p>
                      <p>threshold: {apiCallThreshold.toLocaleString()}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <div className="space-y-2">
                <Label htmlFor="carbon-threshold" className="font-mono text-green-500 flex items-center space-x-2">
                  <Leaf className="w-5 h-5" />
                  <span>{'>'} carbon_threshold</span>
                </Label>
                <Input 
                  id="carbon-threshold"
                  type="number"
                  value={carbonFootprintThreshold}
                  onChange={handleCarbonFootprintThresholdChange}
                  className="font-mono border-green-500/20 bg-black/50 text-green-500"
                />
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center space-x-2 p-2 bg-black/50 border border-green-500/20 rounded-md">
                        <span className="font-mono text-2xl text-green-500">
                          {carbonFootprint.toFixed(2)} kg
                        </span>
                        {carbonFootprint > carbonFootprintThreshold && (
                          <AlertTriangle className="w-6 h-6 text-yellow-500" />
                        )}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent className="font-mono bg-black text-green-500 border-green-500">
                      <p>current: {carbonFootprint.toFixed(2)} kg</p>
                      <p>threshold: {carbonFootprintThreshold.toFixed(2)} kg</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>
            <p className="font-mono text-sm text-green-500/70">
              {'>'} counting_since: {startTime.toLocaleString()}
            </p>
          </div>
        </CardContent>
        <CardFooter className="border-t border-green-500/20">
       <div className="mx-auto mt-4">
        {message && <p className="text-red-500">{message}</p>}
          <Button 
              variant="outline" 
              onClick={handleLogout}
              className="bg-green-900/20 border border-green-500/20 hover:bg-green-900/40 text-green-400 shadow-lg shadow-green-900/10"
              >
              <LogOut className="w-4 h-4 mr-2" />
              logout
            </Button>
          </div>
        </CardFooter>
      </Card>
      </div>
    </div>
  )
}