<script setup lang="ts">
import { ref, computed } from "vue"
import { useAuthStore } from "~/stores/auth"
import { useSupabaseClient } from "#imports"

const supabase = useSupabaseClient()
const authStore = useAuthStore()

const email = ref("")
const otpCode = ref("")
const mode = ref("email")

const buttonLabel = computed(() => {
  return mode.value === "email" ? "Send One-Time Password" : "Verify Code"
})

const handleSubmit = async () => {
  console.log("mode", mode.value)
  if (mode.value === "email") {
    try {
      await authStore.sendOtp(email.value)
      mode.value = "code"
    } catch (error) {
      console.log("Error sending OTP: ", error)
    }
  } else {
    const success = await authStore.verifyOtp(email.value, otpCode.value)

    if (!success) {
      return
    }

    navigateTo("/")
  }
}

definePageMeta({
  colorMode: "light"
})
</script>

<template>
  <div class="flex h-screen">
    <div class="max-w-md m-auto p-8 rounded-lg shadow-md">
      <h2
        class="text-center scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight transition-colors first:mt-0"
      >
        welcome
      </h2>
      <img
        src="/chapterverse.png"
        alt="Chapterverse Logo"
        width="200"
        class="mx-auto border-b pb-2"
      />
      <p class="text-sm text-muted-foreground pt-4 mb-6 text-center">
        Sign in to your account to continue
      </p>
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div v-if="mode === 'email'">
          <Input
            type="email"
            id="email"
            v-model="email"
            required
            placeholder="Enter your email"
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200"
          />
        </div>

        <div v-else-if="mode === 'code'">
          <p class="text-sm text-muted-foreground pt-4 mb-6 text-center">
            Enter the 6-digit code sent to {{ email }}
          </p>
          <input
            type="text"
            v-model="otpCode"
            required
            placeholder="Enter 6-digit code"
            maxlength="6"
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200"
          />
        </div>

        <button
          icon="i-heroicons-paper-airplane"
          size="lg"
          color="primary"
          variant="solid"
          :label="buttonLabel"
          :trailing="true"
          block
        />
      </form>
    </div>
  </div>
</template>
