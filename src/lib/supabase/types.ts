// AVOID UPDATING THIS FILE DIRECTLY. It is automatically generated.
export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: '14.17'
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
            foreignKeyName: 'authorization_audit_log_operation_key_fkey'
            columns: ['operation_key']
            isOneToOne: false
            referencedRelation: 'app_operations'
            referencedColumns: ['operation_key']
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
          tag_pdv: string | null
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
          tag_pdv?: string | null
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
          tag_pdv?: string | null
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
      ciclo_evento: {
        Row: {
          ator: string
          ciclo_id: string
          criado_em: string
          detalhe: Json | null
          evento_id: string
          execucao_id: string | null
          motivo: string
          operacao: string
        }
        Insert: {
          ator: string
          ciclo_id: string
          criado_em?: string
          detalhe?: Json | null
          evento_id?: string
          execucao_id?: string | null
          motivo: string
          operacao: string
        }
        Update: {
          ator?: string
          ciclo_id?: string
          criado_em?: string
          detalhe?: Json | null
          evento_id?: string
          execucao_id?: string | null
          motivo?: string
          operacao?: string
        }
        Relationships: [
          {
            foreignKeyName: 'ciclo_evento_ciclo_id_fkey'
            columns: ['ciclo_id']
            isOneToOne: false
            referencedRelation: 'ciclo_meta'
            referencedColumns: ['ciclo_id']
          },
          {
            foreignKeyName: 'ciclo_evento_execucao_id_fkey'
            columns: ['execucao_id']
            isOneToOne: false
            referencedRelation: 'execucao_calculo'
            referencedColumns: ['execucao_id']
          },
        ]
      }
      ciclo_marcos: {
        Row: {
          aprovado_em: string | null
          ciclo_id: string
          executado_em: string | null
          mes_carregado_em: string | null
          publicado_em: string | null
        }
        Insert: {
          aprovado_em?: string | null
          ciclo_id: string
          executado_em?: string | null
          mes_carregado_em?: string | null
          publicado_em?: string | null
        }
        Update: {
          aprovado_em?: string | null
          ciclo_id?: string
          executado_em?: string | null
          mes_carregado_em?: string | null
          publicado_em?: string | null
        }
        Relationships: [
          {
            foreignKeyName: 'ciclo_marcos_ciclo_id_fkey'
            columns: ['ciclo_id']
            isOneToOne: true
            referencedRelation: 'ciclo_meta'
            referencedColumns: ['ciclo_id']
          },
        ]
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
            foreignKeyName: 'ciclo_meta_parametros_versao_id_fkey'
            columns: ['parametros_versao_id']
            isOneToOne: false
            referencedRelation: 'parametros_versao'
            referencedColumns: ['versao_id']
          },
        ]
      }
      consulta_vinculo: {
        Row: {
          carteira: string
          ciclo_fim: string | null
          ciclo_inicio: string
          criado_em: string
          papel: string
          profile_id: string
          vinculo_id: string
        }
        Insert: {
          carteira: string
          ciclo_fim?: string | null
          ciclo_inicio?: string
          criado_em?: string
          papel: string
          profile_id: string
          vinculo_id?: string
        }
        Update: {
          carteira?: string
          ciclo_fim?: string | null
          ciclo_inicio?: string
          criado_em?: string
          papel?: string
          profile_id?: string
          vinculo_id?: string
        }
        Relationships: [
          {
            foreignKeyName: 'consulta_vinculo_profile_id_fkey'
            columns: ['profile_id']
            isOneToOne: false
            referencedRelation: 'profiles'
            referencedColumns: ['id']
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
            foreignKeyName: 'execucao_calculo_ciclo_id_fkey'
            columns: ['ciclo_id']
            isOneToOne: false
            referencedRelation: 'ciclo_meta'
            referencedColumns: ['ciclo_id']
          },
          {
            foreignKeyName: 'execucao_calculo_parametros_versao_id_fkey'
            columns: ['parametros_versao_id']
            isOneToOne: false
            referencedRelation: 'parametros_versao'
            referencedColumns: ['versao_id']
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
            foreignKeyName: 'parametros_valor_versao_id_fkey'
            columns: ['versao_id']
            isOneToOne: false
            referencedRelation: 'parametros_versao'
            referencedColumns: ['versao_id']
          },
        ]
      }
      parametros_versao: {
        Row: {
          autor: string
          candidato_oficial: boolean
          congelada_em: string | null
          criado_em: string
          mes_referencia: string
          motivo: string | null
          origem: string
          promovido_em: string | null
          promovido_por: string | null
          simulacao: boolean
          status: string
          versao_anterior: string | null
          versao_codigo: string
          versao_id: string
        }
        Insert: {
          autor: string
          candidato_oficial?: boolean
          congelada_em?: string | null
          criado_em?: string
          mes_referencia: string
          motivo?: string | null
          origem?: string
          promovido_em?: string | null
          promovido_por?: string | null
          simulacao?: boolean
          status?: string
          versao_anterior?: string | null
          versao_codigo: string
          versao_id?: string
        }
        Update: {
          autor?: string
          candidato_oficial?: boolean
          congelada_em?: string | null
          criado_em?: string
          mes_referencia?: string
          motivo?: string | null
          origem?: string
          promovido_em?: string | null
          promovido_por?: string | null
          simulacao?: boolean
          status?: string
          versao_anterior?: string | null
          versao_codigo?: string
          versao_id?: string
        }
        Relationships: [
          {
            foreignKeyName: 'parametros_versao_versao_anterior_fkey'
            columns: ['versao_anterior']
            isOneToOne: false
            referencedRelation: 'parametros_versao'
            referencedColumns: ['versao_id']
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
            foreignKeyName: 'profile_role_assignments_profile_id_fkey'
            columns: ['profile_id']
            isOneToOne: false
            referencedRelation: 'profiles'
            referencedColumns: ['id']
          },
          {
            foreignKeyName: 'profile_role_assignments_role_key_fkey'
            columns: ['role_key']
            isOneToOne: false
            referencedRelation: 'app_roles'
            referencedColumns: ['role_key']
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
      reconciliacao_item: {
        Row: {
          causa: string
          controle: string
          declarado_em: string
          dono: string
          execucao_id: string
          modo: string
          pendencia: string
        }
        Insert: {
          causa: string
          controle: string
          declarado_em?: string
          dono: string
          execucao_id: string
          modo: string
          pendencia: string
        }
        Update: {
          causa?: string
          controle?: string
          declarado_em?: string
          dono?: string
          execucao_id?: string
          modo?: string
          pendencia?: string
        }
        Relationships: [
          {
            foreignKeyName: 'reconciliacao_item_execucao_id_fkey'
            columns: ['execucao_id']
            isOneToOne: false
            referencedRelation: 'execucao_calculo'
            referencedColumns: ['execucao_id']
          },
        ]
      }
      reconciliacao_modo: {
        Row: {
          apurado_em: string
          estado: string
          execucao_id: string
          itens_fora: number
          modo: string
        }
        Insert: {
          apurado_em?: string
          estado: string
          execucao_id: string
          itens_fora?: number
          modo: string
        }
        Update: {
          apurado_em?: string
          estado?: string
          execucao_id?: string
          itens_fora?: number
          modo?: string
        }
        Relationships: [
          {
            foreignKeyName: 'reconciliacao_modo_execucao_id_fkey'
            columns: ['execucao_id']
            isOneToOne: false
            referencedRelation: 'execucao_calculo'
            referencedColumns: ['execucao_id']
          },
        ]
      }
      redistribuicao_promotor_ajuste: {
        Row: {
          ajuste_id: string
          ator: string
          base_hash: string
          ciclo_id: string
          cliente: string | null
          criado_em: string
          motivo: string
          promotor: string
          rateio: Json | null
          sku: string | null
          supervisor: string | null
          valor: number
          versao_id: string
        }
        Insert: {
          ajuste_id?: string
          ator: string
          base_hash: string
          ciclo_id: string
          cliente?: string | null
          criado_em?: string
          motivo: string
          promotor: string
          rateio?: Json | null
          sku?: string | null
          supervisor?: string | null
          valor: number
          versao_id: string
        }
        Update: {
          ajuste_id?: string
          ator?: string
          base_hash?: string
          ciclo_id?: string
          cliente?: string | null
          criado_em?: string
          motivo?: string
          promotor?: string
          rateio?: Json | null
          sku?: string | null
          supervisor?: string | null
          valor?: number
          versao_id?: string
        }
        Relationships: [
          {
            foreignKeyName: 'redistribuicao_promotor_ajuste_ciclo_id_fkey'
            columns: ['ciclo_id']
            isOneToOne: false
            referencedRelation: 'ciclo_meta'
            referencedColumns: ['ciclo_id']
          },
          {
            foreignKeyName: 'redistribuicao_promotor_ajuste_versao_id_fkey'
            columns: ['versao_id']
            isOneToOne: false
            referencedRelation: 'parametros_versao'
            referencedColumns: ['versao_id']
          },
        ]
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
            foreignKeyName: 'role_operation_matrix_operation_key_fkey'
            columns: ['operation_key']
            isOneToOne: false
            referencedRelation: 'app_operations'
            referencedColumns: ['operation_key']
          },
          {
            foreignKeyName: 'role_operation_matrix_role_key_fkey'
            columns: ['role_key']
            isOneToOne: false
            referencedRelation: 'app_roles'
            referencedColumns: ['role_key']
          },
        ]
      }
      sortimento_restrito: {
        Row: {
          ciclo_inicio: string | null
          criado_em: string
          rede: string
          sku_codigo: string
          sortimento_id: string
          uf: string
          versao_id: string
        }
        Insert: {
          ciclo_inicio?: string | null
          criado_em?: string
          rede: string
          sku_codigo: string
          sortimento_id?: string
          uf: string
          versao_id: string
        }
        Update: {
          ciclo_inicio?: string | null
          criado_em?: string
          rede?: string
          sku_codigo?: string
          sortimento_id?: string
          uf?: string
          versao_id?: string
        }
        Relationships: [
          {
            foreignKeyName: 'sortimento_restrito_versao_id_fkey'
            columns: ['versao_id']
            isOneToOne: false
            referencedRelation: 'parametros_versao'
            referencedColumns: ['versao_id']
          },
        ]
      }
      substituicao: {
        Row: {
          ciclo_inicio: string | null
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
          ciclo_inicio?: string | null
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
          ciclo_inicio?: string | null
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
            foreignKeyName: 'substituicao_versao_id_fkey'
            columns: ['versao_id']
            isOneToOne: false
            referencedRelation: 'parametros_versao'
            referencedColumns: ['versao_id']
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
      ajustar_meta_promotor_rascunho: {
        Args: {
          p_acao?: string
          p_mes: string
          p_motivo?: string
          p_promotor?: string
          p_saldo_esperado?: number
          p_supervisor?: string
          p_valor?: number
        }
        Returns: Json
      }
      ajustar_meta_rascunho: {
        Args: {
          p_acao?: string
          p_cliente?: string
          p_mes: string
          p_motivo?: string
          p_promotor?: string
          p_saldo_esperado?: number
          p_sku?: string
          p_supervisor?: string
          p_valor?: number
        }
        Returns: Json
      }
      aprovar_execucao: {
        Args: { p_ciclo: string; p_execucao: string; p_motivo: string }
        Returns: string
      }
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
      carteiras_de: {
        Args: { p_ciclo?: string; p_papel: string }
        Returns: string[]
      }
      comparar_parametros_cenarios: {
        Args: { p_versao_a: string; p_versao_b: string }
        Returns: {
          parametro: string
          valor_a: string
          valor_b: string
        }[]
      }
      consulta_por_perfil: {
        Args: { p_ciclo: string; p_papel: string }
        Returns: {
          cliente: string
          cliente_nome: string
          gap_linha: number
          linha_produto: string
          meta_final: number
          meta_original: number
          produto_nome: string
          promotor: string
          regime: string
          sku: string
          supervisor: string
        }[]
      }
      consulta_publicada: {
        Args: { p_ciclo: string; p_papel: string }
        Returns: {
          ciclo: string
          cliente: string
          memoria: Json
          meta_final: number
          regime: string
          sku: string
        }[]
      }
      criar_cenario_ciclo: {
        Args: {
          p_alteracoes?: Json
          p_autor: string
          p_ciclo: string
          p_codigo: string
          p_motivo: string
          p_versao_origem: string
        }
        Returns: string
      }
      criar_ciclo_com_herdanca: {
        Args: { p_autor: string; p_ciclo: string; p_motivo: string }
        Returns: string
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
          from: '*'
          to: 'ciclo_meta'
          isOneToOne: true
          isSetofReturn: false
        }
      }
      criar_versao_cenario: {
        Args: {
          p_alteracoes?: Json
          p_autor: string
          p_codigo: string
          p_motivo: string
          p_versao_origem: string
        }
        Returns: string
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
      criar_versao_parametros_ciclo: {
        Args: {
          p_alteracoes?: Json
          p_autor: string
          p_ciclo: string
          p_motivo: string
          p_novo_codigo: string
          p_versao_origem: string
        }
        Returns: string
      }
      criar_versao_parametros_mes: {
        Args: {
          p_alteracoes?: Json
          p_autor: string
          p_mes_referencia: string
          p_motivo: string
          p_novo_codigo: string
          p_versao_origem: string
        }
        Returns: string
      }
      dblink: { Args: { '': string }; Returns: Record<string, unknown>[] }
      dblink_cancel_query: { Args: { '': string }; Returns: string }
      dblink_close: { Args: { '': string }; Returns: string }
      dblink_connect: { Args: { '': string }; Returns: string }
      dblink_connect_u: { Args: { '': string }; Returns: string }
      dblink_current_query: { Args: never; Returns: string }
      dblink_disconnect:
        | { Args: never; Returns: string }
        | { Args: { '': string }; Returns: string }
      dblink_error_message: { Args: { '': string }; Returns: string }
      dblink_exec: { Args: { '': string }; Returns: string }
      dblink_fdw_validator: {
        Args: { catalog: unknown; options: string[] }
        Returns: undefined
      }
      dblink_get_connections: { Args: never; Returns: string[] }
      dblink_get_notify:
        | { Args: { conname: string }; Returns: Record<string, unknown>[] }
        | { Args: never; Returns: Record<string, unknown>[] }
      dblink_get_pkey: {
        Args: { '': string }
        Returns: Database['public']['CompositeTypes']['dblink_pkey_results'][]
        SetofOptions: {
          from: '*'
          to: 'dblink_pkey_results'
          isOneToOne: false
          isSetofReturn: true
        }
      }
      dblink_get_result: {
        Args: { '': string }
        Returns: Record<string, unknown>[]
      }
      dblink_is_busy: { Args: { '': string }; Returns: number }
      derivar_reconciliacao: {
        Args: { p_execucao: string }
        Returns: undefined
      }
      execucao_aprovavel: { Args: { p_execucao: string }; Returns: boolean }
      extrato_saida: {
        Args: { p_ciclo: string }
        Returns: {
          cliente: string
          cliente_nome: string
          gap_linha: number
          linha_produto: string
          meta_final: number
          meta_original: number
          produto_nome: string
          promotor: string
          referencia_ciclo: string
          regime: string
          sku: string
          supervisor: string
        }[]
      }
      hash_insumos_execucao: {
        Args: { p_execucao_id: string }
        Returns: string
      }
      layout_saida: { Args: { p_ciclo: string }; Returns: string }
      limite_cenarios: {
        Args: { p_ciclo: string }
        Returns: {
          aviso: string
          limite: number
        }[]
      }
      oficializar_versao_parametros: {
        Args: { p_motivo: string; p_versao: string }
        Returns: undefined
      }
      pendencias_confirmacao: {
        Args: { p_execucao: string }
        Returns: {
          parametro_codigo: string
          valor: string
        }[]
      }
      prazo_k2: {
        Args: { p_ciclo: string }
        Returns: {
          dentro_do_prazo: boolean
          dias_ate_publicacao: number
          medido: boolean
          motivo: string
          prazo_limite: string
        }[]
      }
      promover_cenario: {
        Args: { p_autor: string; p_motivo: string; p_versao_cenario: string }
        Returns: string
      }
      publicar_ciclo: {
        Args: { p_ciclo: string; p_motivo: string }
        Returns: string
      }
      registrar_marco: {
        Args: { p_ciclo: string; p_marco: string }
        Returns: string
      }
      registrar_negativa: {
        Args: { p_alvo: string; p_operacao: string; p_razao: string }
        Returns: string
      }
      registrar_negativa_parametros: {
        Args: { p_alvo: string; p_operacao: string; p_razao: string }
        Returns: string
      }
      registrar_recusa: {
        Args: {
          p_ciclo: string
          p_execucao: string
          p_operacao: string
          p_razao: string
        }
        Returns: string
      }
      regras_vigentes: {
        Args: { p_ciclo: string }
        Returns: {
          ciclo_inicio: string | null
          criado_em: string
          rede: string
          sku_destino: string
          sku_origem: string
          substituicao_id: string
          taxa: number
          uf: string
          versao_id: string
        }[]
        SetofOptions: {
          from: '*'
          to: 'substituicao'
          isOneToOne: false
          isSetofReturn: true
        }
      }
      vigencia_valida: { Args: { p_ciclo_inicio: string }; Returns: boolean }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      dblink_pkey_results: {
        position: number | null
        colname: string | null
      }
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

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema['Enums']
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions['schema']]['Enums']
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions['schema']]['Enums'][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema['Enums']
    ? DefaultSchema['Enums'][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema['CompositeTypes']
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions['schema']]['CompositeTypes']
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions['schema']]['CompositeTypes'][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema['CompositeTypes']
    ? DefaultSchema['CompositeTypes'][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
