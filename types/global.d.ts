import type { QueryData } from "@supabase/supabase-js"
import type { Database } from "~/types/database.types"

declare global {
    type Database = Database
    type Book = Database["public"]["Tables"]["books"]["Row"]
    type LibraryWithBooks = QueryData<ReturnType<typeof createLibraryWithBooksQuery>>[]

    type LibraryWithBooksItem = {
        status: string | null
        progress: number | null
        progressType: string | null
        dateStarted: string | null
        dateFinished: string | null
        rating: number | null
        bookId: string
        books: {
        id: string
        title: string
        subtitle: string | null
        }
    }
}