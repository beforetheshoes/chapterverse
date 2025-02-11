// Follow this setup guide to integrate the Deno language server with your editor:
// https://deno.land/manual/getting_started/setup_your_environment
// This enables autocomplete, go to definition, etc.

// Setup type definitions for built-in Supabase Runtime APIs
import "jsr:@supabase/functions-js/edge-runtime.d.ts"

async function validateImageUrl(url: string): Promise<boolean> {
  try {
    const response = await fetch(url);
    const contentType = response.headers.get('Content-Type');
    
    if (contentType && contentType.startsWith('image/')) {
      return true;
    }
  } catch (error) {
    console.error('Error fetching image:', error);
  }
  return false;
}

// Function to download and upload the image to Supabase Storage
async function uploadImageToStorage(url: string, fileName: string) {
  const response = await fetch(url);
  const buffer = await response.arrayBuffer(); // Deno uses arrayBuffer instead of buffer
  
  const { data, error } = await fetch(`${Deno.env.get('SUPABASE_URL')}/storage/v1/object/book-covers/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('SUPABASE_KEY')}`,
      'Content-Type': response.headers.get('Content-Type') || 'application/octet-stream',
    },
    body: buffer,
  });

  if (error) {
    console.error('Error uploading file to Supabase Storage:', error);
    return null;
  }

  return data?.path;
}

// Define the Edge Function
Deno.serve(async (req) => {
  try {
    // Parse the request body
    const { url, bookId } = await req.json();
    
    // Validate the image URL
    const isValidImage = await validateImageUrl(url);
    if (!isValidImage) {
      return new Response('Invalid image URL or not an image', { status: 400 });
    }

    // Generate a file name for storage (You can use any logic here)
    const fileName = `book-covers/${bookId}.jpg`;

    // Upload the image to Supabase
    const storagePath = await uploadImageToStorage(url, fileName);
    if (!storagePath) {
      return new Response('Error uploading image', { status: 500 });
    }

    // Construct the public URL for the uploaded image
    const publicUrl = `${Deno.env.get('SUPABASE_URL')}/storage/v1/object/public/${storagePath}`;

    // Return the image URL in the response
    return new Response(JSON.stringify({ imageUrl: publicUrl }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    
  } catch (error) {
    console.error('Error in Edge Function:', error);
    return new Response('Internal server error', { status: 500 });
  }
});