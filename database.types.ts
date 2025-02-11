export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      authors: {
        Row: {
          dateOfBirth: string | null
          defaultImage: string | null
          firstName: string
          id: string
          lastName: string | null
          olAuthorId: string | null
        }
        Insert: {
          dateOfBirth?: string | null
          defaultImage?: string | null
          firstName: string
          id?: string
          lastName?: string | null
          olAuthorId?: string | null
        }
        Update: {
          dateOfBirth?: string | null
          defaultImage?: string | null
          firstName?: string
          id?: string
          lastName?: string | null
          olAuthorId?: string | null
        }
        Relationships: []
      }
      books: {
        Row: {
          authorIds: string[] | null
          description: string | null
          format: string | null
          id: string
          isbn10: string | null
          isbn13: string | null
          olAuthorIds: string[] | null
          olEditionId: string | null
          olWorkId: string | null
          publishDate: string | null
          subjects: string[] | null
          subtitle: string | null
          tags: string[] | null
          title: string
        }
        Insert: {
          authorIds?: string[] | null
          description?: string | null
          format?: string | null
          id?: string
          isbn10?: string | null
          isbn13?: string | null
          olAuthorIds?: string[] | null
          olEditionId?: string | null
          olWorkId?: string | null
          publishDate?: string | null
          subjects?: string[] | null
          subtitle?: string | null
          tags?: string[] | null
          title: string
        }
        Update: {
          authorIds?: string[] | null
          description?: string | null
          format?: string | null
          id?: string
          isbn10?: string | null
          isbn13?: string | null
          olAuthorIds?: string[] | null
          olEditionId?: string | null
          olWorkId?: string | null
          publishDate?: string | null
          subjects?: string[] | null
          subtitle?: string | null
          tags?: string[] | null
          title?: string
        }
        Relationships: []
      }
      libraries: {
        Row: {
          bookId: string
          dateFinished: string | null
          dateStarted: string | null
          id: string
          progress: number | null
          progressType: string | null
          rating: number | null
          status: string
          userId: string
        }
        Insert: {
          bookId: string
          dateFinished?: string | null
          dateStarted?: string | null
          id?: string
          progress?: number | null
          progressType?: string | null
          rating?: number | null
          status: string
          userId?: string
        }
        Update: {
          bookId?: string
          dateFinished?: string | null
          dateStarted?: string | null
          id?: string
          progress?: number | null
          progressType?: string | null
          rating?: number | null
          status?: string
          userId?: string
        }
        Relationships: [
          {
            foreignKeyName: "libraries_bookId_fkey"
            columns: ["bookId"]
            isOneToOne: false
            referencedRelation: "books"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "libraries_userId_fkey"
            columns: ["userId"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      users: {
        Row: {
          avatarUrl: string | null
          createdAt: string | null
          email: string
          fullName: string | null
          id: string
          updatedAt: string | null
          username: string | null
          website: string | null
        }
        Insert: {
          avatarUrl?: string | null
          createdAt?: string | null
          email: string
          fullName?: string | null
          id?: string
          updatedAt?: string | null
          username?: string | null
          website?: string | null
        }
        Update: {
          avatarUrl?: string | null
          createdAt?: string | null
          email?: string
          fullName?: string | null
          id?: string
          updatedAt?: string | null
          username?: string | null
          website?: string | null
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type PublicSchema = Database[Extract<keyof Database, "public">]

export type Tables<
  PublicTableNameOrOptions extends
    | keyof (PublicSchema["Tables"] & PublicSchema["Views"])
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
        Database[PublicTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? (Database[PublicTableNameOrOptions["schema"]]["Tables"] &
      Database[PublicTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : PublicTableNameOrOptions extends keyof (PublicSchema["Tables"] &
        PublicSchema["Views"])
    ? (PublicSchema["Tables"] &
        PublicSchema["Views"])[PublicTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  PublicTableNameOrOptions extends
    | keyof PublicSchema["Tables"]
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : PublicTableNameOrOptions extends keyof PublicSchema["Tables"]
    ? PublicSchema["Tables"][PublicTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  PublicTableNameOrOptions extends
    | keyof PublicSchema["Tables"]
    | { schema: keyof Database },
  TableName extends PublicTableNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = PublicTableNameOrOptions extends { schema: keyof Database }
  ? Database[PublicTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : PublicTableNameOrOptions extends keyof PublicSchema["Tables"]
    ? PublicSchema["Tables"][PublicTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  PublicEnumNameOrOptions extends
    | keyof PublicSchema["Enums"]
    | { schema: keyof Database },
  EnumName extends PublicEnumNameOrOptions extends { schema: keyof Database }
    ? keyof Database[PublicEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = PublicEnumNameOrOptions extends { schema: keyof Database }
  ? Database[PublicEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : PublicEnumNameOrOptions extends keyof PublicSchema["Enums"]
    ? PublicSchema["Enums"][PublicEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof PublicSchema["CompositeTypes"]
    | { schema: keyof Database },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof Database
  }
    ? keyof Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof Database }
  ? Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof PublicSchema["CompositeTypes"]
    ? PublicSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never
