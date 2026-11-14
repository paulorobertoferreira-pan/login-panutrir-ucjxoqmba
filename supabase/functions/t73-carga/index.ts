import "jsr:@supabase/functions-js/edge-runtime.d.ts";

Deno.serve(async () => {
  return new Response(
    JSON.stringify({ error: "ponte t73 encerrada — carga concluída e verificada em 02/11/2026" }),
    { status: 410, headers: { "Content-Type": "application/json" } },
  );
});
