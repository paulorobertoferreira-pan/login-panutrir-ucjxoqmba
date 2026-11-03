// Neutralizada (Paulo, 03/11/2026): a versão do Skip v0.0.16 resetava a senha do
// usuário de teste para Skip@Pass e estava exposta SEM autenticação — foi o
// mecanismo que fez a senha antiga voltar a valer (2x). Qualquer chamada devolve
// 410 Gone e não toca no auth.
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS })
  return new Response(
    JSON.stringify({
      error: 'gone',
      message: 'Esta função foi desativada por segurança. Nenhuma senha é alterada por aqui.',
    }),
    { status: 410, headers: { ...CORS, 'Content-Type': 'application/json' } },
  )
})
