# Issue roadmap

This is a suggested order of execution based on dependencies and risk.

## 1) Foundation

- #29 Initialize Nuxt 3 project with UI library - DONE
- #18 Set up FastAPI with Supabase JWT verification middleware - DONE
- #7 Configure Alembic for database migrations - DONE

## 2) Core data model

- #8 Create bibliographic tables: authors, works, editions, work_authors - DONE
- #9 Create external provider tracking tables: external_ids, source_records - DONE
- #10 Create user tables: users, library_items, reading_sessions - DONE
- #11 Create content tables: notes, highlights, reviews - DONE
- #12 Create platform tables: api_clients, api_audit_logs - DONE
- #13 Configure RLS policies for user-owned tables

## 3) Auth

- #6 Disable email/password sign-in in Supabase Auth
- #4 Configure Supabase Auth with Apple and Google OAuth providers
- #5 Configure and test magic link (passwordless) login
- #25 Enable and configure Supabase OAuth 2.1 server mode
- #26 Implement OAuth consent page in Nuxt
- #27 Require client_id claim in all API requests
- #28 Implement rate limiting per (client_id, user_id)

## 4) API features

- #14 Implement Open Library Search API integration with caching
- #15 Implement import endpoint for Open Library works and editions
- #16 Cache Open Library cover images to Supabase Storage
- #17 Implement manual book creation endpoint
- #19 Implement /me profile endpoints
- #20 Implement library item CRUD with filtering and pagination
- #21 Implement reading session CRUD endpoints
- #22 Implement notes CRUD endpoints
- #23 Implement highlights CRUD with visibility controls
- #24 Implement review endpoints with public listing

## 5) Web UI

- #30 Implement login page with OAuth and magic link options
- #31 Implement book search and import interface
- #32 Implement library list with filters
- #33 Implement book detail page with reading/notes/highlights

## 6) iOS

- #34 Initialize SwiftUI project with OAuth PKCE authentication
- #35 Implement API client layer for iOS app
- #36 Implement library list and book search in SwiftUI
- #37 Implement notes, highlights, and reviews UI in iOS

## 7) Federation / ActivityPub

- #38 Define and document canonical public URL patterns
- #39 Add optional ap_uri columns for federation readiness
- #40 Reserve ActivityPub endpoints with placeholder responses

## 8) Hosting wiring

- #44 Configure hosting env vars for Supabase staging/production

## Notes

- #3 (Supabase staging/production projects) is done. Hosting wiring is tracked separately in #44.
