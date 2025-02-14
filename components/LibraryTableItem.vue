<script lang="ts" setup>
import type { Database } from "~/types/database.types"
import { useLibraryStore } from "@/stores/libraryStore"
import type { QueryData } from "@supabase/supabase-js"
import type { LibraryWithBooksItem } from "@/types/types"
const libraryStore = useLibraryStore()

const props = defineProps<{
  book: LibraryWithBooksItem
}>()
</script>

<template>
  <TableRow>
    <TableCell>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button aria-haspopup="true" size="icon" variant="ghost">
            <LucideMoreHorizontal class="h-4 w-4" />
            <span class="sr-only">Toggle menu</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem>Edit</DropdownMenuItem>
          <DropdownMenuItem>Delete</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </TableCell>
    <TableCell class="hidden sm:table-cell">
      <NuxtImg
        alt="Book cover image"
        class="aspect-square rounded-md object-cover"
        height="64"
        src="/chapterverse.png"
        width="64"
        v-slot="{ src, isLoaded, imgAttrs }"
      />
    </TableCell>
    <TableCell class="font-medium">{{ book.book.title }}</TableCell>
    <TableCell>{{ book.book.subtitle }}</TableCell>
    <TableCell>{{ book.status }}</TableCell>
    <TableCell>{{ book.progress }}</TableCell>
    <TableCell>{{ book.progress_type }}</TableCell>
    <TableCell>{{ book.date_started }}</TableCell>
    <TableCell>{{ book.date_finished }}</TableCell>
    <TableCell>{{ book.rating }}</TableCell>
  </TableRow>
</template>
