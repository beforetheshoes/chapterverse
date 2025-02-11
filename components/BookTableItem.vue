<script lang="ts" setup>
import type { Database } from "@/database.types"

const props = defineProps<{
  book: Database["public"]["Tables"]["books"]["Row"]
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
      <nuxt-img
        alt="Book cover image"
        class="aspect-square rounded-md object-cover"
        height="64"
        src="/chapterverse.png"
        width="64"
        v-slot="{ src, isLoaded, imgAttrs }"
      />
    </TableCell>
    <TableCell class="font-medium">{{ book.title }}</TableCell>
    <TableCell>{{ book.subtitle }}</TableCell>
    <TableCell>{{ book.isbn10 }}</TableCell>
    <TableCell>{{ book.isbn13 }}</TableCell>
    <TableCell>{{ book.format }}</TableCell>
    <TableCell>{{ book.description }}</TableCell>
    <TableCell>{{ book.publishDate }}</TableCell>
    <TableCell>{{ book.tags }}</TableCell>
    <TableCell>{{ book.subjects }}</TableCell>
    <TableCell>{{ book.olWorkId }}</TableCell>
    <TableCell>{{ book.olEditionId }}</TableCell>
  </TableRow>
</template>
