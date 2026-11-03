import { createClient } from 'jsr:@supabase/supabase-js@2'

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-t73-secret',
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS })
  if (req.method !== 'POST') return new Response(JSON.stringify({ error: 'method' }), { status: 405, headers: CORS })

  const secret = req.headers.get('x-t73-secret') ?? ''
  const encoder = new TextEncoder()
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(secret))
  const sha = Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('')

  const admin = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!)
  // Tabela pode estar vazia (limpeza da T2.3): gravar a linha 1 por upsert id=1.
  const { error } = await admin.from('t23_bridge_config').upsert({ id: 1, secret_hash: sha })
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: CORS })
  return new Response(JSON.stringify({ ok: true }), { headers: CORS })
})
