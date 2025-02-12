<script lang="ts" setup>
import { useLibraryStore } from "@/stores/libraryStore"

const libraryStore = useLibraryStore()
//libraryStore.searchBooks(searchQuery)
const supabase = useSupabaseClient<Database>()
const searchQuery = ref("")
const searchResults: Ref<Book[]> = ref([])

const searchBooks = async (query: string): Promise<void> => {
  const formattedQuery = `"${query}"`
  const { data, error } = await supabase
    .from("books")
    .select()
    .textSearch("title", formattedQuery, { type: "websearch" })

  if (error) {
    console.log(error)
  } else {
    searchResults.value = data
  }
}

const handleAddBookClick = (book: Book) => {
  console.log("Adding book:", book)
}
</script>

<template>
  <DialogHeader>
    <DialogTitle>Add a book to your library</DialogTitle>
    <DialogDescription>
      Search in the box below or add a book manually.
    </DialogDescription>
  </DialogHeader>
  <Separator class="my-4" />
  <div class="grid grid-cols-4 items-center gap-4">
    <Label for="search" class="text-right"> Search </Label>
    <Input
      id="search"
      v-model="searchQuery"
      default-value=""
      class="col-span-3"
      @keypress.enter="searchBooks(searchQuery)"
    />
  </div>
  <div v-if="searchResults.length > 0">
    <ul class="space-y-2 p-4 border rounded-lg">
      <li v-for="book in searchResults" :key="book.id" class="p-2 rounded-md">
        <button
          @click="handleAddBookClick(book)"
          class="block w-full text-left p-2 focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {{ book.title + (book.subtitle ? " - " + book.subtitle : "") }}
        </button>
      </li>
    </ul>
  </div>
  <Separator class="my-4" label="Or" />
  <div class="grid gap-4 py-4">
    <div class="grid grid-cols-4 items-center gap-4">
      <Label for="title" class="text-right"> Title </Label>
      <Input id="title" default-value="" class="col-span-3" />
    </div>
    <div class="grid grid-cols-4 items-center gap-4">
      <Label for="subtitle" class="text-right"> Subtitle </Label>
      <Input id="subtitle" default-value="" class="col-span-3" />
    </div>
  </div>
  <DialogFooter>
    <Button type="submit"> Save changes </Button>
  </DialogFooter>
</template>
