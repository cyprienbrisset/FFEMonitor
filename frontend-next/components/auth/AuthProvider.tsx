'use client'

import { createContext, useContext, useEffect, useState, ReactNode, useMemo, useCallback } from 'react'
import { Session, User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'

interface AuthContextType {
  session: Session | null
  user: User | null
  loading: boolean
  signOut: () => Promise<void>
  getAccessToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextType>({
  session: null,
  user: null,
  loading: true,
  signOut: async () => {},
  getAccessToken: async () => null,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Memoize the supabase client to prevent recreating it on every render
  const supabase = useMemo(() => createClient(), [])

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    }

    getInitialSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [supabase])

  const signOut = async () => {
    await supabase.auth.signOut()
    setSession(null)
    setUser(null)
  }

  // Get a fresh access token (auto-refreshes if needed)
  const getAccessToken = useCallback(async (): Promise<string | null> => {
    try {
      const { data: { session: freshSession }, error } = await supabase.auth.getSession()
      if (error) {
        console.error('[Auth] Error getting session:', error)
        return null
      }
      if (freshSession) {
        // Update state if session changed
        if (freshSession.access_token !== session?.access_token) {
          setSession(freshSession)
          setUser(freshSession.user)
        }
        return freshSession.access_token
      }
      return null
    } catch (error) {
      console.error('[Auth] Error refreshing token:', error)
      return null
    }
  }, [supabase, session?.access_token])

  return (
    <AuthContext.Provider value={{ session, user, loading, signOut, getAccessToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

export function useSession() {
  const { session } = useAuth()
  return session
}
