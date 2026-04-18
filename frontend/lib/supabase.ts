import { createClient, SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

/**
 * Browser/SSR Supabase client.
 *
 * We intentionally export a lazy singleton so the app still builds when
 * env vars are missing during local scaffolding. Runtime calls will throw
 * a clear error if the credentials are not configured.
 */
let _client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (_client) return _client;
  if (!url || !anonKey) {
    throw new Error(
      "Supabase credentials missing. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in .env.local",
    );
  }
  _client = createClient(url, anonKey, {
    auth: { persistSession: false },
  });
  return _client;
}

export const isSupabaseConfigured = (): boolean => Boolean(url && anonKey);

export const supabase = {
  get client() {
    return getSupabase();
  },
};
