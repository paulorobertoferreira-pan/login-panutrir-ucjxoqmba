// AVOID UPDATING THIS FILE DIRECTLY. It is automatically generated.
export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: '14.5'
  }
  public: {
    Tables: {
      meta_linha: {
        Row: {
          meta_linha_id: string
          referencia_ciclo: string
          cliente: string
          sku: string
          cliente_nome: string | null
          produto_nome: string | null
          linha_produto: string | null
          supervisor: string | null
          promotor: string | null
          regime: string
          meta_original: number
          gap_linha: number
          meta_final: number
          memoria: Json | null
          criado_em: string
        }
        Insert: {
          meta_linha_id?: string
          referencia_ciclo?: string
          cliente: string
          sku: string
          cliente_nome?: string | null
          produto_nome?: string | null
          linha_produto?: string | null
          supervisor?: string | null
          promotor?: string | null
          regime: string
          meta_original?: number
          gap_linha?: number
          meta_final?: number
          memoria?: Json | null
          criado_em?: string
        }
        Update: {
          meta_linha_id?: string
          referencia_ciclo?: string
          cliente?: string
          sku?: string
          cliente_nome?: string | null
          produto_nome?: string | null
          linha_produto?: string | null
          supervisor?: string | null
          promotor?: string | null
          regime?: string
          meta_original?: number
          gap_linha?: number
          meta_final?: number
          memoria?: Json | null
          criado_em?: string
        }
        Relationships: []
      }
      controle_gabarito: {
        Row: {
          controle_id: string
          modo: string
          controle: string
          gabarito: number
          medido: number | null
          diferenca: number | null
          diferenca_pct: number | null
          tolerancia: number
          estado: string
          referencia_ciclo: string
          criado_em: string
        }
        Insert: {
          controle_id?: string
          modo: string
          controle: string
          gabarito: number
          medido?: number | null
          diferenca?: number | null
          diferenca_pct?: number | null
          tolerancia?: number
          estado: string
          referencia_ciclo?: string
          criado_em?: string
        }
        Update: {
          controle_id?: string
          modo?: string
          controle?: string
          gabarito?: number
          medido?: number | null
          diferenca?: number | null
          diferenca_pct?: number | null
          tolerancia?: number
          estado?: string
          referencia_ciclo?: string
          criado_em?: string
        }
        Relationships: []
      }
    }
    Views: {
      vw_meta_supervisor: {
        Row: {
          referencia_ciclo: string
          supervisor: string | null
          combinacoes: number
          clientes: number
          meta_original: number | null
          gap_linha: number | null
          meta_final: number | null
        }
        Relationships: []
      }
      vw_meta_promotor: {
        Row: {
          referencia_ciclo: string
          supervisor: string | null
          promotor: string | null
          combinacoes: number
          clientes: number
          meta_original: number | null
          gap_linha: number | null
          meta_final: number | null
        }
        Relationships: []
      }
      vw_meta_regime: {
        Row: {
          referencia_ciclo: string
          regime: string
          combinacoes: number
          meta_original: number | null
          gap_linha: number | null
          meta_final: number | null
        }
        Relationships: []
      }
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, '__InternalSupabase'>

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, 'public'>]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema['Tables'] & DefaultSchema['Views'])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables'] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Views'])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables'] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Views'])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema['Tables'] & DefaultSchema['Views'])
    ? (DefaultSchema['Tables'] & DefaultSchema['Views'])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema['Tables']
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables']
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables'][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema['Tables']
    ? DefaultSchema['Tables'][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema['Tables']
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables']
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables'][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema['Tables']
    ? DefaultSchema['Tables'][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<T extends keyof DefaultSchema['Enums']> = DefaultSchema['Enums'][T]

export type CompositeTypes<T extends keyof DefaultSchema['CompositeTypes']> =
  DefaultSchema['CompositeTypes'][T]

export const Constants = {
  public: {
    Enums: {},
  },
} as const
