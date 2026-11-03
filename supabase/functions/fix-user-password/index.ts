import { createClient } from 'npm:@supabase/supabase-js@2'

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS })

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const anonKey = Deno.env.get('SUPABASE_ANON_KEY') || serviceRoleKey

    const admin = createClient(supabaseUrl, serviceRoleKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    })

    const targetEmail = 'paulo.ferreira@panutrir.com.br'
    const newPassword = 'Skip@Pass'

    // 1. Check if user exists
    const { data: usersData, error: listError } = await admin.auth.admin.listUsers()
    if (listError) {
      return new Response(JSON.stringify({ error: listError.message }), {
        status: 500,
        headers: CORS,
      })
    }

    const existingUser = usersData.users.find(
      (u) => u.email?.toLowerCase() === targetEmail.toLowerCase(),
    )

    let updateResult: any = null
    if (existingUser) {
      const { data, error } = await admin.auth.admin.updateUserById(existingUser.id, {
        password: newPassword,
        email_confirm: true,
      })
      if (error) {
        return new Response(JSON.stringify({ step: 'updateUserById', error: error.message }), {
          status: 500,
          headers: CORS,
        })
      }
      updateResult = { action: 'updated', id: data.user.id }
    } else {
      const { data, error } = await admin.auth.admin.createUser({
        email: targetEmail,
        password: newPassword,
        email_confirm: true,
      })
      if (error) {
        return new Response(JSON.stringify({ step: 'createUser', error: error.message }), {
          status: 500,
          headers: CORS,
        })
      }
      updateResult = { action: 'created', id: data.user.id }
    }

    // 2. Test login directly with signInWithPassword using anon client
    const testClient = createClient(supabaseUrl, anonKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    })

    const { data: signInData, error: signInError } = await testClient.auth.signInWithPassword({
      email: targetEmail,
      password: newPassword,
    })

    return new Response(
      JSON.stringify({
        success: !signInError,
        updateResult,
        loginSuccess: !!signInData?.session,
        loginUser: signInData?.user?.email,
        signInError: signInError ? signInError.message : null,
      }),
      {
        headers: { 'Content-Type': 'application/json', ...CORS },
      },
    )
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err?.message || String(err) }), {
      status: 500,
      headers: CORS,
    })
  }
})
