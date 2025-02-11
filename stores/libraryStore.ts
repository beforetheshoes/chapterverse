import { defineStore } from "pinia"
import type { Database } from "@/database.types"
import { createLibraryWithBooksQuery, type LibraryWithBooksItem } from "@/types/types"

export const useLibraryStore = defineStore("libraryStore", () => {
  const supabase = useSupabaseClient()

  const libraryWithBooksQuery = createLibraryWithBooksQuery(supabase)

  const books: Ref<Database["public"]["Tables"]["books"]["Row"][]> = ref([])
  const library: Ref<LibraryWithBooksItem[]> = ref([])

  const getBooks = async () => {
    const { data, error } = await supabase
      .from("books")
      .select("*")
      .order("title", { ascending: true })

    if (error) {
      console.log(error)
    } else {
      books.value = data
    }
  }

  const getLibrary = async () => {
    const { data, error } = await libraryWithBooksQuery

    if (error) {
      console.log(error)
    } else {
      library.value = data
    }
  }

  return {
    books,
    library,
    getBooks,
    getLibrary,
    libraryWithBooksQuery
  }
})
