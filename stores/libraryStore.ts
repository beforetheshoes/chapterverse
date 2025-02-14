import type { QueryResult, QueryData } from "@supabase/supabase-js"
import { defineStore } from "pinia"

export const useLibraryStore = defineStore("libraryStore", () => {
  const supabase = useSupabaseClient<Database>()

  const libraryWithBooksQuery = supabase.from("libraries").select(`
    status,
    progress,
    progress_type,
    date_started,
    date_finished,
    rating,
    book_id,
    books (
      id,
      title,
      subtitle
    )
  `)
  
  const books: Ref<Book[]> = ref([])
  const library: Ref<LibraryWithBooks> = ref([])

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
