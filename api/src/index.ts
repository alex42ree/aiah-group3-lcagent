import { serve } from '@hono/node-server'
import { Hono } from 'hono'
import { z } from 'zod'
import { zValidator } from '@hono/zod-validator'
import type { Context, Next } from 'hono'

// Define types and schemas
type CountryEntry = {
  id: string
  name: string
  country: string
  // Add other fields as needed
}

// In-memory storage (replace with a database in production)
const entries: CountryEntry[] = [
  { id: 'US-NYC', name: 'New York', country: 'USA' },
  { id: 'GB-LON', name: 'London', country: 'UK' },
  { id: 'FR-PAR', name: 'Paris', country: 'France' },
  { id: 'US-LAX', name: 'Los Angeles', country: 'USA' },
  { id: 'DE-HAM', name: 'Hamburg', country: 'Germany' },
  { id: 'DE-HRB', name: 'Hamburg', country: 'Germany' }
]

// Request validation schemas
const baseSchema = z.object({
  operation: z.enum(['get_entry', 'search', 'same_country'])
})

const getEntrySchema = baseSchema.extend({
  operation: z.literal('get_entry'),
  entry_id: z.string(),
  search_query: z.undefined(),
  entry1_id: z.undefined(),
  entry2_id: z.undefined()
})

const searchSchema = baseSchema.extend({
  operation: z.literal('search'),
  search_query: z.string(),
  entry_id: z.undefined(),
  entry1_id: z.undefined(),
  entry2_id: z.undefined()
})

const sameCountrySchema = baseSchema.extend({
  operation: z.literal('same_country'),
  entry1_id: z.string(),
  entry2_id: z.string(),
  entry_id: z.undefined(),
  search_query: z.undefined()
})

const countryDataSchema = z.discriminatedUnion('operation', [
  getEntrySchema,
  searchSchema,
  sameCountrySchema
])

// Create Hono app
const app = new Hono()

// Middleware for CORS and logging
app.use('*', async (c: Context, next: Next) => {
  // Add CORS headers
  c.header('Access-Control-Allow-Origin', '*')
  c.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  c.header('Access-Control-Allow-Headers', 'Content-Type')
  
  // Log request
  console.log(`${c.req.method} ${c.req.url}`)
  
  await next()
})

// Health check endpoint
app.get('/health', (c: Context) => c.json({ status: 'ok' }))

// Main country data endpoint
app.post('/country-data', zValidator('json', countryDataSchema), async (c: Context) => {
  const body = await c.req.json()
  console.log('Received request body:', JSON.stringify(body, null, 2))
  const { operation, entry_id, search_query, entry1_id, entry2_id } = body

  try {
    switch (operation) {
      case 'get_entry':
        if (!entry_id) {
          console.log('Error: entry_id is required for get_entry operation')
          return c.json({ error: 'entry_id is required for get_entry operation' }, 400)
        }
        console.log('Looking for entry with ID:', entry_id)
        const entry = entries.find(e => e.id === entry_id)
        console.log('Found entry:', entry)
        if (!entry) {
          console.log('Entry not found')
          return c.json({ error: 'Entry not found' }, 404)
        }
        const response = { data: entry }
        console.log('Sending response:', JSON.stringify(response, null, 2))
        return c.json(response)

      case 'search':
        if (!search_query) {
          return c.json({ error: 'search_query is required for search operation' }, 400)
        }
        const searchResults = entries.filter(e => 
          e.name.toLowerCase().includes(search_query.toLowerCase()) ||
          e.country.toLowerCase().includes(search_query.toLowerCase())
        )
        return c.json({ data: searchResults })

      case 'same_country':
        if (!entry1_id || !entry2_id) {
          return c.json({ error: 'Both entry1_id and entry2_id are required for same_country operation' }, 400)
        }
        const entry1 = entries.find(e => e.id === entry1_id)
        const entry2 = entries.find(e => e.id === entry2_id)
        
        if (!entry1 || !entry2) {
          return c.json({ error: 'One or both entries not found' }, 404)
        }
        
        const sameCountry = entry1.country === entry2.country
        return c.json({ 
          data: {
            same_country: sameCountry,
            entry1_country: entry1.country,
            entry2_country: entry2.country
          }
        })

      default:
        return c.json({ error: 'Invalid operation' }, 400)
    }
  } catch (error) {
    console.error('Error processing request:', error)
    return c.json({ error: 'Internal server error' }, 500)
  }
})

// Start the server
const port = process.env.PORT || 3000
console.log(`Server is running on port ${port}`)

serve({
  fetch: app.fetch,
  port: Number(port)
}) 