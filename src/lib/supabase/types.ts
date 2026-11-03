// AVOID UPDATING THIS FILE DIRECTLY. It is automatically generated.
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.17"
  }
  public: {
    Tables: {
      app_operations: {
        Row: {
          created_at: string
          description: string
          display_name: string
          operation_key: string
        }
        Insert: {
          created_at?: string
          description: string
          display_name: string
          operation_key: string
        }
        Update: {
          created_at?: string
          description?: string
          display_name?: string
          operation_key?: string
        }
        Relationships: []
      }
      app_roles: {
        Row: {
          created_at: string
          description: string
          display_name: string
          role_key: string
        }
        Insert: {
          created_at?: string
          description: string
          display_name: string
          role_key: string
        }
        Update: {
          created_at?: string
          description?: string
          display_name?: string
          role_key?: string
        }
        Relationships: []
      }
      auditoria_estrutura: {
        Row: {
          auditoria_id: string
          codigo: string
          created_at: string
          detalhe: Json | null
          execucao_id: string
          motivo: string
          nome: string | null
          tipo: string
        }
        Insert: {
          auditoria_id?: string
          codigo: string
          created_at?: string
          detalhe?: Json | null
          execucao_id: string
          motivo: string
          nome?: string | null
          tipo: string
        }
        Update: {
          auditoria_id?: string
          codigo?: string
          created_at?: string
          detalhe?: Json | null
          execucao_id?: string
          motivo?: string
          nome?: string | null
          tipo?: string
        }
        Relationships: []
      }
      authorization_audit_log: {
        Row: {
          actor_id: string | null
          correlation_id: string
          created_at: string
          decision: string
          event_id: string
          operation_key: string
          reason: string | null
          target_id: string | null
          target_type: string | null
        }
        Insert: {
          actor_id?: string | null
          correlation_id?: string
          created_at?: string
          decision: string
          event_id?: string
          operation_key: string
          reason?: string | null
          target_id?: string | null
          target_type?: string | null
        }
        Update: {
          actor_id?: string | null
          correlation_id?: string
          created_at?: string
          decision?: string
          event_id?: string
          operation_key?: string
          reason?: string | null
          target_id?: string | null
          target_type?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "authorization_audit_log_operation_key_fkey"
            columns: ["operation_key"]
            isOneToOne: false
            referencedRelation: "app_operations"
            referencedColumns: ["operation_key"]
          },
        ]
      }
      calendario_mes: {
        Row: {
          criado_em: string
          dias_uteis: number
          is_origem: string
          is_valor: number | null
          mes: string
          pendente_de: string | null
        }
        Insert: {
          criado_em?: string
          dias_uteis: number
          is_origem?: string
          is_valor?: number | null
          mes: string
          pendente_de?: string | null
        }
        Update: {
          criado_em?: string
          dias_uteis?: number
          is_origem?: string
          is_valor?: number | null
          mes?: string
          pendente_de?: string | null
        }
        Relationships: []
      }
      carga_rede_pendente: {
        Row: {
          cliente_codigo: string
          criado_em: string
          motivo: string
        }
        Insert: {
          cliente_codigo: string
          criado_em?: string
          motivo: string
        }
        Update: {
          cliente_codigo?: string
          criado_em?: string
          motivo?: string
        }
        Relationships: []
      }
      carga_registro: {
        Row: {
          arquivo_bytes: number | null
          arquivo_hash: string
          arquivo_nome: string
          carga_id: string
          concluido_em: string | null
          erro: string | null
          executado_por: string
          iniciado_em: string
          linhas_agregadas: number
          linhas_lidas: number
          linhas_rejeitadas: number
          meses_afetados: string[]
          rejeicoes: Json
          status: string
          totais_por_mes: Json
        }
        Insert: {
          arquivo_bytes?: number | null
          arquivo_hash: string
          arquivo_nome: string
          carga_id?: string
          concluido_em?: string | null
          erro?: string | null
          executado_por: string
          iniciado_em?: string
          linhas_agregadas?: number
          linhas_lidas?: number
          linhas_rejeitadas?: number
          meses_afetados?: string[]
          rejeicoes?: Json
          status?: string
          totais_por_mes?: Json
        }
        Update: {
          arquivo_bytes?: number | null
          arquivo_hash?: string
          arquivo_nome?: string
          carga_id?: string
          concluido_em?: string | null
          erro?: string | null
          executado_por?: string
          iniciado_em?: string
          linhas_agregadas?: number
          linhas_lidas?: number
          linhas_rejeitadas?: number
          meses_afetados?: string[]
          rejeicoes?: Json
          status?: string
          totais_por_mes?: Json
        }
        Relationships: []
      }
      catalog_clientes: {
        Row: {
          canal: string | null
          cliente_codigo: string
          cliente_id: string
          cliente_nome: string
          created_at: string
          promotor_codigo: string | null
          rede: string | null
          rede_codigo: string | null
          rede_codigo_sap: string | null
          supervisor_codigo: string | null
          uf: string | null
          updated_at: string
          vigencia_fim: string | null
          vigencia_inicio: string
        }
        Insert: {
          canal?: string | null
          cliente_codigo: string
          cliente_id?: string
          cliente_nome: string
          created_at?: string
          promotor_codigo?: string | null
          rede?: string | null
          rede_codigo?: string | null
          rede_codigo_sap?: string | null
          supervisor_codigo?: string | null
          uf?: string | null
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio: string
        }
        Update: {
          canal?: string | null
          cliente_codigo?: string
          cliente_id?: string
          cliente_nome?: string
          created_at?: string
          promotor_codigo?: string | null
          rede?: string | null
          rede_codigo?: string | null
          rede_codigo_sap?: string | null
          supervisor_codigo?: string | null
          uf?: string | null
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio?: string
        }
        Relationships: []
      }
      catalog_pendencias_resolucao: {
        Row: {
          correlation_id: string
          created_at: string
          detalhe: string | null
          entidade_codigo: string | null
          entidade_tipo: string
          motivo: string
          pendencia_id: string
          resolucao_motivo: string | null
          resolvida_em: string | null
          resolvida_por: string | null
          status: string
          tipo: string
        }
        Insert: {
          correlation_id?: string
          created_at?: string
          detalhe?: string | null
          entidade_codigo?: string | null
          entidade_tipo: string
          motivo: string
          pendencia_id?: string
          resolucao_motivo?: string | null
          resolvida_em?: string | null
          resolvida_por?: string | null
          status?: string
          tipo: string
        }
        Update: {
          correlation_id?: string
          created_at?: string
          detalhe?: string | null
          entidade_codigo?: string | null
          entidade_tipo?: string
          motivo?: string
          pendencia_id?: string
          resolucao_motivo?: string | null
          resolvida_em?: string | null
          resolvida_por?: string | null
          status?: string
          tipo?: string
        }
        Relationships: []
      }
      catalog_produtos: {
        Row: {
          ativo: boolean
          created_at: string
          ean: string | null
          is_panettone: boolean
          linha_codigo: string
          produto_codigo: string
          produto_id: string
          produto_nome: string
          unidade_medida: string | null
          updated_at: string
          vigencia_fim: string | null
          vigencia_inicio: string
        }
        Insert: {
          ativo?: boolean
          created_at?: string
          ean?: string | null
          is_panettone?: boolean
          linha_codigo: string
          produto_codigo: string
          produto_id?: string
          produto_nome: string
          unidade_medida?: string | null
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio: string
        }
        Update: {
          ativo?: boolean
          created_at?: string
          ean?: string | null
          is_panettone?: boolean
          linha_codigo?: string
          produto_codigo?: string
          produto_id?: string
          produto_nome?: string
          unidade_medida?: string | null
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio?: string
        }
        Relationships: []
      }
      catalog_responsaveis: {
        Row: {
          created_at: string
          responsavel_codigo: string
          responsavel_id: string
          responsavel_rotulo: string
          responsavel_tipo: string
          updated_at: string
          vigencia_fim: string | null
          vigencia_inicio: string
        }
        Insert: {
          created_at?: string
          responsavel_codigo: string
          responsavel_id?: string
          responsavel_rotulo: string
          responsavel_tipo: string
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio: string
        }
        Update: {
          created_at?: string
          responsavel_codigo?: string
          responsavel_id?: string
          responsavel_rotulo?: string
          responsavel_tipo?: string
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio?: string
        }
        Relationships: []
      }
      catalog_territorios: {
        Row: {
          created_at: string
          territorio_codigo: string
          territorio_id: string
          territorio_nome: string
          updated_at: string
          vigencia_fim: string | null
          vigencia_inicio: string
        }
        Insert: {
          created_at?: string
          territorio_codigo: string
          territorio_id?: string
          territorio_nome: string
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio: string
        }
        Update: {
          created_at?: string
          territorio_codigo?: string
          territorio_id?: string
          territorio_nome?: string
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio?: string
        }
        Relationships: []
      }
      catalog_vinculos: {
        Row: {
          created_at: string
          responsavel_codigo: string
          territorio_codigo: string
          updated_at: string
          vigencia_fim: string | null
          vigencia_inicio: string
          vinculo_id: string
        }
        Insert: {
          created_at?: string
          responsavel_codigo: string
          territorio_codigo: string
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio: string
          vinculo_id?: string
        }
        Update: {
          created_at?: string
          responsavel_codigo?: string
          territorio_codigo?: string
          updated_at?: string
          vigencia_fim?: string | null
          vigencia_inicio?: string
          vinculo_id?: string
        }
        Relationships: []
      }
      ciclo_meta: {
        Row: {
          atualizado_em: string
          ciclo_id: string
          criado_em: string
          criado_por: string | null
          mes_referencia: string
          meta_diretoria: number
          parametros_versao_id: string
          status: string
        }
        Insert: {
          atualizado_em?: string
          ciclo_id?: string
          criado_em?: string
          criado_por?: string | null
          mes_referencia: string
          meta_diretoria: number
          parametros_versao_id: string
          status?: string
        }
        Update: {
          atualizado_em?: string
          ciclo_id?: string
          criado_em?: string
          criado_por?: string | null
          mes_referencia?: string
          meta_diretoria?: number
          parametros_versao_id?: string
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "ciclo_meta_parametros_versao_id_fkey"
            columns: ["parametros_versao_id"]
            isOneToOne: false
            referencedRelation: "parametros_versao"
            referencedColumns: ["versao_id"]
          },
        ]
      }
      controle_gabarito: {
        Row: {
          controle: string
          controle_id: string
          criado_em: string
          diferenca: number | null
          diferenca_pct: number | null
          estado: string
          gabarito: number
          medido: number | null
          modo: string
          referencia_ciclo: string
          tolerancia: number
        }
        Insert: {
          controle: string
          controle_id?: string
          criado_em?: string
          diferenca?: number | null
          diferenca_pct?: number | null
          estado: string
          gabarito: number
          medido?: number | null
          modo: string
          referencia_ciclo?: string
          tolerancia?: number
        }
        Update: {
          controle?: string
          controle_id?: string
          criado_em?: string
          diferenca?: number | null
          diferenca_pct?: number | null
          estado?: string
          gabarito?: number
          medido?: number | null
          modo?: string
          referencia_ciclo?: string
          tolerancia?: number
        }
        Relationships: []
      }
      execucao_calculo: {
        Row: {
          autor: string
          cargas: Json
          ciclo_id: string
          contagens: Json | null
          execucao_id: string
          finalizado_em: string | null
          hash_resultado: string | null
          iniciado_em: string
          motor_versao: string
          parametros_versao_id: string
          status: string
        }
        Insert: {
          autor: string
          cargas?: Json
          ciclo_id: string
          contagens?: Json | null
          execucao_id?: string
          finalizado_em?: string | null
          hash_resultado?: string | null
          iniciado_em?: string
          motor_versao: string
          parametros_versao_id: string
          status?: string
        }
        Update: {
          autor?: string
          cargas?: Json
          ciclo_id?: string
          contagens?: Json | null
          execucao_id?: string
          finalizado_em?: string | null
          hash_resultado?: string | null
          iniciado_em?: string
          motor_versao?: string
          parametros_versao_id?: string
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "execucao_calculo_ciclo_id_fkey"
            columns: ["ciclo_id"]
            isOneToOne: false
            referencedRelation: "ciclo_meta"
            referencedColumns: ["ciclo_id"]
          },
          {
            foreignKeyName: "execucao_calculo_parametros_versao_id_fkey"
            columns: ["parametros_versao_id"]
            isOneToOne: false
            referencedRelation: "parametros_versao"
            referencedColumns: ["versao_id"]
          },
        ]
      }
      meta_linha: {
        Row: {
          cliente: string
          cliente_nome: string | null
          criado_em: string
          gap_linha: number
          linha_produto: string | null
          memoria: Json | null
          meta_final: number
          meta_linha_id: string
          meta_original: number
          produto_nome: string | null
          promotor: string | null
          referencia_ciclo: string
          regime: string
          sku: string
          supervisor: string | null
        }
        Insert: {
          cliente: string
          cliente_nome?: string | null
          criado_em?: string
          gap_linha?: number
          linha_produto?: string | null
          memoria?: Json | null
          meta_final?: number
          meta_linha_id?: string
          meta_original?: number
          produto_nome?: string | null
          promotor?: string | null
          referencia_ciclo?: string
          regime: string
          sku: string
          supervisor?: string | null
        }
        Update: {
          cliente?: string
          cliente_nome?: string | null
          criado_em?: string
          gap_linha?: number
          linha_produto?: string | null
          memoria?: Json | null
          meta_final?: number
          meta_linha_id?: string
          meta_original?: number
          produto_nome?: string | null
          promotor?: string | null
          referencia_ciclo?: string
          regime?: string
          sku?: string
          supervisor?: string | null
        }
        Relationships: []
      }
      parametros_valor: {
        Row: {
          criado_em: string
          descricao: string
          parametro_codigo: string
          pendente_de: string | null
          unidade: string | null
          valor_id: string
          valor_json: Json | null
          valor_numero: number | null
          valor_texto: string | null
          versao_id: string
        }
        Insert: {
          criado_em?: string
          descricao: string
          parametro_codigo: string
          pendente_de?: string | null
          unidade?: string | null
          valor_id?: string
          valor_json?: Json | null
          valor_numero?: number | null
          valor_texto?: string | null
          versao_id: string
        }
        Update: {
          criado_em?: string
          descricao?: string
          parametro_codigo?: string
          pendente_de?: string | null
          unidade?: string | null
          valor_id?: string
          valor_json?: Json | null
          valor_numero?: number | null
          valor_texto?: string | null
          versao_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "parametros_valor_versao_id_fkey"
            columns: ["versao_id"]
            isOneToOne: false
            referencedRelation: "parametros_versao"
            referencedColumns: ["versao_id"]
          },
        ]
      }
      parametros_versao: {
        Row: {
          autor: string
          congelada_em: string | null
          criado_em: string
          mes_referencia: string
          motivo: string | null
          origem: string
          status: string
          versao_anterior: string | null
          versao_codigo: string
          versao_id: string
        }
        Insert: {
          autor: string
          congelada_em?: string | null
          criado_em?: string
          mes_referencia: string
          motivo?: string | null
          origem?: string
          status?: string
          versao_anterior?: string | null
          versao_codigo: string
          versao_id?: string
        }
        Update: {
          autor?: string
          congelada_em?: string | null
          criado_em?: string
          mes_referencia?: string
          motivo?: string | null
          origem?: string
          status?: string
          versao_anterior?: string | null
          versao_codigo?: string
          versao_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "parametros_versao_versao_anterior_fkey"
            columns: ["versao_anterior"]
            isOneToOne: false
            referencedRelation: "parametros_versao"
            referencedColumns: ["versao_id"]
          },
        ]
      }
      profile_role_assignments: {
        Row: {
          assigned_at: string
          assigned_by: string | null
          profile_id: string
          revoked_at: string | null
          role_key: string
        }
        Insert: {
          assigned_at?: string
          assigned_by?: string | null
          profile_id: string
          revoked_at?: string | null
          role_key: string
        }
        Update: {
          assigned_at?: string
          assigned_by?: string | null
          profile_id?: string
          revoked_at?: string | null
          role_key?: string
        }
        Relationships: [
          {
            foreignKeyName: "profile_role_assignments_profile_id_fkey"
            columns: ["profile_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "profile_role_assignments_role_key_fkey"
            columns: ["role_key"]
            isOneToOne: false
            referencedRelation: "app_roles"
            referencedColumns: ["role_key"]
          },
        ]
      }
      profiles: {
        Row: {
          created_at: string
          department: string | null
          email: string
          id: string
          name: string | null
          role: string | null
          updated_at: string
        }
        Insert: {
          created_at?: string
          department?: string | null
          email: string
          id: string
          name?: string | null
          role?: string | null
          updated_at?: string
        }
        Update: {
          created_at?: string
          department?: string | null
          email?: string
          id?: string
          name?: string | null
          role?: string | null
          updated_at?: string
        }
        Relationships: []
      }
      role_operation_matrix: {
        Row: {
          decision: string
          operation_key: string
          rationale: string
          role_key: string
          updated_at: string
        }
        Insert: {
          decision: string
          operation_key: string
          rationale: string
          role_key: string
          updated_at?: string
        }
        Update: {
          decision?: string
          operation_key?: string
          rationale?: string
          role_key?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "role_operation_matrix_operation_key_fkey"
            columns: ["operation_key"]
            isOneToOne: false
            referencedRelation: "app_operations"
            referencedColumns: ["operation_key"]
          },
          {
            foreignKeyName: "role_operation_matrix_role_key_fkey"
            columns: ["role_key"]
            isOneToOne: false
            referencedRelation: "app_roles"
            referencedColumns: ["role_key"]
          },
        ]
      }
      sortimento_restrito: {
        Row: {
          criado_em: string
          rede: string
          sku_codigo: string
          sortimento_id: string
          uf: string
          versao_id: string
        }
        Insert: {
          criado_em?: string
          rede: string
          sku_codigo: string
          sortimento_id?: string
          uf: string
          versao_id: string
        }
        Update: {
          criado_em?: string
          rede?: string
          sku_codigo?: string
          sortimento_id?: string
          uf?: string
          versao_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "sortimento_restrito_versao_id_fkey"
            columns: ["versao_id"]
            isOneToOne: false
            referencedRelation: "parametros_versao"
            referencedColumns: ["versao_id"]
          },
        ]
      }
      substituicao: {
        Row: {
          criado_em: string
          rede: string
          sku_destino: string
          sku_origem: string
          substituicao_id: string
          taxa: number
          uf: string
          versao_id: string
        }
        Insert: {
          criado_em?: string
          rede: string
          sku_destino: string
          sku_origem: string
          substituicao_id?: string
          taxa: number
          uf: string
          versao_id: string
        }
        Update: {
          criado_em?: string
          rede?: string
          sku_destino?: string
          sku_origem?: string
          substituicao_id?: string
          taxa?: number
          uf?: string
          versao_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "substituicao_versao_id_fkey"
            columns: ["versao_id"]
            isOneToOne: false
            referencedRelation: "parametros_versao"
            referencedColumns: ["versao_id"]
          },
        ]
      }
      t23_bridge_config: {
        Row: {
          criado_em: string
          id: number
          secret_hash: string
        }
        Insert: {
          criado_em?: string
          id?: number
          secret_hash: string
        }
        Update: {
          criado_em?: string
          id?: number
          secret_hash?: string
        }
        Relationships: []
      }
      venda_mensal: {
        Row: {
          atualizado_em: string
          carga_id: string | null
          cod_cliente: number
          cod_sku: number
          criado_em: string
          mes: string
          qtdade: number
          venda_bruta: number | null
          venda_liquida: number | null
          venda_mensal_id: string
          vlrdesc: number
          vlritens: number
          vlrtroca: number
        }
        Insert: {
          atualizado_em?: string
          carga_id?: string | null
          cod_cliente: number
          cod_sku: number
          criado_em?: string
          mes: string
          qtdade?: number
          venda_bruta?: number | null
          venda_liquida?: number | null
          venda_mensal_id?: string
          vlrdesc?: number
          vlritens?: number
          vlrtroca?: number
        }
        Update: {
          atualizado_em?: string
          carga_id?: string | null
          cod_cliente?: number
          cod_sku?: number
          criado_em?: string
          mes?: string
          qtdade?: number
          venda_bruta?: number | null
          venda_liquida?: number | null
          venda_mensal_id?: string
          vlrdesc?: number
          vlritens?: number
          vlrtroca?: number
        }
        Relationships: []
      }
    }
    Views: {
      vw_meta_promotor: {
        Row: {
          clientes: number | null
          combinacoes: number | null
          gap_linha: number | null
          meta_final: number | null
          meta_original: number | null
          promotor: string | null
          referencia_ciclo: string | null
          supervisor: string | null
        }
        Relationships: []
      }
      vw_meta_regime: {
        Row: {
          combinacoes: number | null
          gap_linha: number | null
          meta_final: number | null
          meta_original: number | null
          referencia_ciclo: string | null
          regime: string | null
        }
        Relationships: []
      }
      vw_meta_supervisor: {
        Row: {
          clientes: number | null
          combinacoes: number | null
          gap_linha: number | null
          meta_final: number | null
          meta_original: number | null
          referencia_ciclo: string | null
          supervisor: string | null
        }
        Relationships: []
      }
    }
    Functions: {
      authorize_operation: {
        Args: {
          p_correlation_id?: string
          p_operation_key: string
          p_reason?: string
          p_target_id?: string
          p_target_type?: string
        }
        Returns: boolean
      }
      criar_ciclo_meta: {
        Args: {
          p_correlation_id?: string
          p_mes_referencia: string
          p_meta_diretoria: number
          p_parametros_versao_id: string
        }
        Returns: {
          atualizado_em: string
          ciclo_id: string
          criado_em: string
          criado_por: string | null
          mes_referencia: string
          meta_diretoria: number
          parametros_versao_id: string
          status: string
        }
        SetofOptions: {
          from: "*"
          to: "ciclo_meta"
          isOneToOne: true
          isSetofReturn: false
        }
      }
      criar_versao_parametros: {
        Args: {
          p_alteracoes?: Json
          p_autor: string
          p_motivo: string
          p_novo_codigo: string
          p_versao_origem: string
        }
        Returns: string
      }
      hash_insumos_execucao: {
        Args: { p_execucao_id: string }
        Returns: string
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const

