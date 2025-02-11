import { defineStore } from "pinia"

export const useAuthStore = defineStore("auth", () => {
  const supabase = useSupabaseClient()

  const sendOtp = async (email: string) => {
    const { error } = await supabase.auth.signInWithOtp({
      email
    })

    if (error) {
      throw error
    }

    return true
  }

  const verifyOtp = async (email: string, otp: string) => {
    const {
      data: { session },
      error
    } = await supabase.auth.verifyOtp({
      type: "email",
      token: otp,
      email
    })

    if (error) {
      throw error
    }

    return true
  }

  return {
    sendOtp,
    verifyOtp
  }
})
