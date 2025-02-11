<script setup lang="ts">
import { useLibraryStore } from "@/stores/libraryStore"
const libraryStore = useLibraryStore()

onMounted(async () => {
  if (libraryStore.books.length === 0) {
    await libraryStore.getBooks()
  }

  console.log(libraryStore.books)
})
</script>

<template>
  <div>
    <main class="grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0 md:gap-8">
      <Tabs default-value="all">
        <div class="flex items-center">
          <TabsList>
            <TabsTrigger value="all"> All </TabsTrigger>
            <TabsTrigger value="active"> Active </TabsTrigger>
            <TabsTrigger value="draft"> Draft </TabsTrigger>
            <TabsTrigger value="archived" class="hidden sm:flex">
              Archived
            </TabsTrigger>
          </TabsList>
          <div class="ml-auto flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="outline" size="sm" class="h-7 gap-1">
                  <LucideListFilter class="h-3.5 w-3.5" />
                  <span class="sr-only sm:not-sr-only sm:whitespace-nowrap">
                    Filter
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Filter by</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem checked> Active </DropdownMenuItem>
                <DropdownMenuItem>Draft</DropdownMenuItem>
                <DropdownMenuItem> Archived </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button size="sm" variant="outline" class="h-7 gap-1">
              <LucideFile class="h-3.5 w-3.5" />
              <span class="sr-only sm:not-sr-only sm:whitespace-nowrap">
                Export
              </span>
            </Button>
            <Button size="sm" class="h-7 gap-1">
              <LucidePlusCircle class="h-3.5 w-3.5" />
              <span class="sr-only sm:not-sr-only sm:whitespace-nowrap">
                Add Book
              </span>
            </Button>
          </div>
        </div>
        <TabsContent value="all">
          <Card>
            <CardHeader>
              <CardTitle>Books</CardTitle>
              <CardDescription>
                A list of all books that have been added by any user.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table v-if="libraryStore.books.length > 0">
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead class="hidden w-[100px] sm:table-cell">
                      <span class="sr-only">img</span>
                    </TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Subtitle</TableHead>
                    <TableHead>ISBN10 </TableHead>
                    <TableHead>ISBN13 </TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Publish Date</TableHead>
                    <TableHead>Tags</TableHead>
                    <TableHead>Subjects</TableHead>
                    <TableHead>Open Library Work ID</TableHead>
                    <TableHead>Open Library Edition ID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <BookTableItem
                    v-for="book in libraryStore.books"
                    :key="book.id"
                    :book="book"
                  />
                </TableBody>
              </Table>
            </CardContent>
            <CardFooter>
              <div class="text-xs text-muted-foreground">
                Showing <strong>1-10</strong> of <strong>32</strong>
                books
              </div>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  </div>
</template>
