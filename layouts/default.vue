<script lang="ts" setup>
const supabase = useSupabaseClient()
const user = useSupabaseUser()

const signOut = async function () {
  await supabase.auth.signOut()
  navigateTo("/login")
}

onMounted(async () => {
  const {
    data: { session }
  } = await supabase.auth.getSession()

  if (session) {
    user.value = session.user
  }

  supabase.auth.onAuthStateChange((_event, session) => {
    user.value = session?.user || null
  })
})
</script>

<template>
  <div>
    <div class="flex min-h-screen w-full flex-col bg-muted/40">
      <aside
        class="fixed inset-y-0 left-0 z-10 hidden w-14 flex-col border-r bg-background sm:flex"
      >
        <nav class="flex flex-col items-center gap-4 px-2 py-4">
          <a
            href="#"
            class="group flex h-9 w-9 shrink-0 items-center justify-center gap-2 rounded-full bg-primary text-lg font-semibold text-primary-foreground md:h-8 md:w-8 md:text-base"
          >
            <LucidePackage2
              class="h-4 w-4 transition-all group-hover:scale-110"
            />
            <span class="sr-only">Acme Inc</span>
          </a>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <NuxtLink
                  :to="{ path: '/' }"
                  class="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:text-foreground md:h-8 md:w-8"
                >
                  <LucideHome class="h-5 w-5" />
                  <span class="sr-only">Dashboard</span>
                </NuxtLink>
              </TooltipTrigger>
              <TooltipContent side="right"> Dashboard </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <NuxtLink
                  :to="{ path: '/library' }"
                  class="flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:text-foreground md:h-8 md:w-8"
                >
                  <LucideLibrary class="h-5 w-5" />
                  <span class="sr-only">Library</span>
                </NuxtLink>
              </TooltipTrigger>
              <TooltipContent side="right"> Library </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <NuxtLink
                  :to="{ path: '/books' }"
                  class="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-accent-foreground transition-colors hover:text-foreground md:h-8 md:w-8"
                >
                  <LucidePackage class="h-5 w-5" />
                  <span class="sr-only">Books</span>
                </NuxtLink>
              </TooltipTrigger>
              <TooltipContent side="right"> Books </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <a
                  href="#"
                  class="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:text-foreground md:h-8 md:w-8"
                >
                  <LucideUsers2 class="h-5 w-5" />
                  <span class="sr-only">Customers</span>
                </a>
              </TooltipTrigger>
              <TooltipContent side="right"> Customers </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <a
                  href="#"
                  class="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:text-foreground md:h-8 md:w-8"
                >
                  <LucideLineChart class="h-5 w-5" />
                  <span class="sr-only">Analytics</span>
                </a>
              </TooltipTrigger>
              <TooltipContent side="right"> Analytics </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </nav>
        <nav class="mt-auto flex flex-col items-center gap-4 px-2 py-4">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <a
                  href="#"
                  class="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:text-foreground md:h-8 md:w-8"
                >
                  <LucideSettings class="h-5 w-5" />
                  <span class="sr-only">Settings</span>
                </a>
              </TooltipTrigger>
              <TooltipContent side="right"> Settings </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </nav>
      </aside>
      <div class="flex flex-col sm:gap-4 sm:py-4 sm:pl-14">
        <header
          class="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6"
        >
          <Sheet>
            <SheetTrigger as-child>
              <Button size="icon" variant="outline" class="sm:hidden">
                <LucidePanelLeft class="h-5 w-5" />
                <span class="sr-only">Toggle Menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" class="sm:max-w-xs">
              <nav class="grid gap-6 text-lg font-medium">
                <a
                  href="#"
                  class="group flex h-10 w-10 shrink-0 items-center justify-center gap-2 rounded-full bg-primary text-lg font-semibold text-primary-foreground md:text-base"
                >
                  <LucidePackage2
                    class="h-5 w-5 transition-all group-hover:scale-110"
                  />
                  <span class="sr-only">Acme Inc</span>
                </a>
                <NuxtLink
                  :to="{ path: '/' }"
                  class="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground"
                >
                  <LucideHome class="h-5 w-5" />
                  Dashboard
                </NuxtLink>
                <NuxtLink
                  :to="{ path: '/library' }"
                  class="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground"
                >
                  <LucideLibrary class="h-5 w-5" />
                  Library
                </NuxtLink>
                <NuxtLink
                  :to="{ path: '/books' }"
                  class="flex items-center gap-4 px-2.5 text-foreground"
                >
                  <LucidePackage class="h-5 w-5" />
                  Books
                </NuxtLink>
                <a
                  href="#"
                  class="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground"
                >
                  <LucideUsers2 class="h-5 w-5" />
                  Customers
                </a>
                <a
                  href="#"
                  class="flex items-center gap-4 px-2.5 text-muted-foreground hover:text-foreground"
                >
                  <LucideLineChart class="h-5 w-5" />
                  Settings
                </a>
              </nav>
            </SheetContent>
          </Sheet>
          <h2 class="hidden md:flex">chapterverse</h2>
          <div class="relative ml-auto flex-1 md:grow-0">
            <LucideSearch
              class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground"
            />
            <Input
              type="search"
              placeholder="Search..."
              class="w-full rounded-lg bg-background pl-8 md:w-[200px] lg:w-[320px]"
            />
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="secondary" size="icon" class="rounded-full">
                <LucideCircleUser class="h-5 w-5" />
                <span class="sr-only">Toggle user menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Settings</DropdownMenuItem>
              <DropdownMenuItem>Support</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="signOut()">Sign out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>
        <slot />
      </div>
    </div>
  </div>
</template>
