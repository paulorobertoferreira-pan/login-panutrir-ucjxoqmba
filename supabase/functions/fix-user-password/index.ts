// NEUTRALIZADA (Paulo, 03/11/2026) — NÃO REATIVAR.
//
// A versão anterior desta função resetava a senha do usuário de teste
// (paulo.ferreira@panutrir.com.br) para "Skip@Pass" e estava publicada no
// Supabase com verify_jwt=false — qualquer pessoa na internet podia chamá-la
// e reverter a troca de senha da T1.3. Foi o mecanismo real da reincidência
// da senha em 03/11 (não foi restore de backup).
//
// A função no Supabase já foi substituída por este stub (410 Gone, com
// verificação de JWT). Este arquivo mantém o repositório alinhado com o que
// está publicado, para que um futuro sync do Skip não recrie a versão
// perigosa. Se algum dia for preciso trocar a senha por função, ela deve
// exigir segredo de uso único e nunca conter senha em código.

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