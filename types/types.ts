import type { QueryData } from "@supabase/supabase-js"
import type { Database } from "@/database.types"

export type LibraryWithBooks = QueryData<
  ReturnType<typeof createLibraryWithBooksQuery>
>[]

export type LibraryWithBooksItem = {
  status: string | null
  progress: number | null
  progressType: string | null
  dateStarted: string | null
  dateFinished: string | null
  rating: number | null
  bookId: string
  book: {
    id: string
    title: string
    subtitle: string | null
  }
}

// Function to define the query shape
export const createLibraryWithBooksQuery = (supabase: any) => 
  supabase
    .from("libraries")
    .select(`
      status,
      progress,
      progressType,
      dateStarted,
      dateFinished,
      rating,
      bookId,
      book (
        id,
        title,
        subtitle
      )
    `)
    .order("title", { ascending: true })