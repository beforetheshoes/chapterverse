<script setup lang="ts">
import { useLibraryStore } from "@/stores/libraryStore"
const libraryStore = useLibraryStore()

onMounted(async () => {
  if (
    Array.isArray(libraryStore.library) &&
    libraryStore.library.length === 0
  ) {
    await libraryStore.getLibrary()
  }

  console.log(libraryStore.library)
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
              <CardTitle>Library</CardTitle>
              <CardDescription>
                View and manage the books in your library.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table
                v-if="
                  Array.isArray(libraryStore.library) &&
                  libraryStore.library.length > 0
                "
              >
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead class="hidden w-[100px] sm:table-cell">
                      <span class="sr-only">img</span>
                    </TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Subtitle</TableHead>
                    <TableHead>Status </TableHead>
                    <TableHead>Progress </TableHead>
                    <TableHead>Progress Type</TableHead>
                    <TableHead>Date Started</TableHead>
                    <TableHead>Date Finished</TableHead>
                    <TableHead>Rating</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <LibraryTableItem
                    v-for="book in libraryStore.library"
                    :key="book.bookId"
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
