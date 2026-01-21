import streamlit as st
import pandas as pd
import os, time, base64, sqlite3
from database import init_db
from utils import get_countries, get_states, get_cities

def exibir_pagina_hoteis():
    st.title("🏨 Gestão de Hotéis")
    conn = init_db()
    PASTA_ANEXOS = "arquivos_hoteis"
    if not os.path.exists(PASTA_ANEXOS): os.makedirs(PASTA_ANEXOS)

    # Inicialização de estados de sessão
    if 'id_edicao' not in st.session_state: st.session_state.id_edicao = None
    if 'form_data' not in st.session_state: st.session_state.form_data = {}
    
    tab_cad, tab_cons = st.tabs(["📝 Cadastro e Edição", "🔍 Consulta"])

    # ==========================================
    # --- ABA 1: CADASTRO E EDIÇÃO ---
    # ==========================================
    with tab_cad:
        hoteis_db = pd.read_sql_query("SELECT id, nome_comercial FROM hoteis ORDER BY nome_comercial", conn)
        
        with st.expander("🛠️ Localizar Hotel para Editar", expanded=not st.session_state.id_edicao):
            col_sel, col_btn_new = st.columns([3, 1])
            hotel_selecionado = col_sel.selectbox("Escolha um hotel:", [""] + hoteis_db['nome_comercial'].tolist())
            
            if col_sel.button("Carregar para Edição") and hotel_selecionado:
                h_id = hoteis_db[hoteis_db['nome_comercial'] == hotel_selecionado]['id'].iloc[0]
                st.session_state.id_edicao = int(h_id)
                h_data = pd.read_sql_query("SELECT * FROM hoteis WHERE id=?", conn, params=(int(h_id),)).iloc[0]
                st.session_state.form_data = h_data.to_dict()
                
                ac = pd.read_sql_query("SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h_id),))
                st.session_state.form_data['acomodacoes'] = ac.to_dict('records')
                
                try:
                    px = pd.read_sql_query("SELECT tipo, chave FROM pix WHERE hotel_id=?", conn, params=(int(h_id),))
                    st.session_state.form_data['pix'] = px.to_dict('records')
                except:
                    st.session_state.form_data['pix'] = []
                st.rerun()

            if col_btn_new.button("➕ Novo Cadastro", use_container_width=True):
                st.session_state.id_edicao = None
                st.session_state.form_data = {'acomodacoes': [], 'pix': []}
                st.rerun()

        # --- CAMPOS DO FORMULÁRIO ---
        st.subheader("Informações Gerais")
        c1, c2, c3 = st.columns(3)
        nome_com = c1.text_input("Nome Comercial", value=st.session_state.form_data.get('nome_comercial', ''))
        razao = c2.text_input("Razão Social", value=st.session_state.form_data.get('razao_social', ''))
        cnpj = c3.text_input("CNPJ", value=st.session_state.form_data.get('cnpj', ''))

        st.subheader("Localização")
        l1, l2, l3 = st.columns(3)
        p_lista = get_countries()
        p_idx = p_lista.index(st.session_state.form_data.get('pais')) if st.session_state.form_data.get('pais') in p_lista else 0
        pais = l1.selectbox("País", p_lista, index=p_idx)
        
        e_lista = get_states(pais)
        e_idx = e_lista.index(st.session_state.form_data.get('estado')) if st.session_state.form_data.get('estado') in e_lista else 0
        estado = l2.selectbox("Estado", e_lista, index=e_idx)
        
        c_lista = get_cities(pais, estado)
        c_idx = c_lista.index(st.session_state.form_data.get('cidade')) if st.session_state.form_data.get('cidade') in c_lista else 0
        cidade = l3.selectbox("Cidade", c_lista, index=c_idx)

        # --- SEÇÃO FINANCEIRA ---
        st.subheader("Financeiro e Tarifário")
        with st.expander("💰 Configurar Tarifas", expanded=True):
            if 'acomodacoes' not in st.session_state.form_data: st.session_state.form_data['acomodacoes'] = []
            a1, a2, a3, a4 = st.columns([2, 1, 2, 0.5])
            tipo_ac = a1.text_input("Tipo de Quarto", key="tipo_ac_new")
            valor_ac = a2.text_input("Valor (ex: 150.00)", key="valor_ac_new") # Texto para limpeza manual
            obs_ac = a3.text_input("Obs", key="obs_ac_new")
            
            if a4.button("➕", key="add_ac"):
                if tipo_ac:
                    st.session_state.form_data['acomodacoes'].append({'tipo': tipo_ac, 'valor': valor_ac, 'obs': obs_ac})
                    st.rerun()

            if st.session_state.form_data['acomodacoes']:
                st.table(pd.DataFrame(st.session_state.form_data['acomodacoes']))
                if st.button("Limpar Tarifas"):
                    st.session_state.form_data['acomodacoes'] = []
                    st.rerun()

        # --- BOTÃO SALVAR (Onde estava o erro) ---
        if st.button("💾 SALVAR HOTEL", use_container_width=True, type="primary"):
            if nome_com:
                cursor = conn.cursor()
                # Coleta dados básicos do form_data ou inputs
                # (Para brevidade, simplificado; ajuste se precisar de CEP/Lat/Long aqui)
                
                if st.session_state.id_edicao:
                    h_id = st.session_state.id_edicao
                    cursor.execute("UPDATE hoteis SET nome_comercial=?, razao_social=?, cnpj=?, cidade=?, estado=?, pais=? WHERE id=?",
                                 (nome_com, razao, cnpj, cidade, estado, pais, h_id))
                else:
                    cursor.execute("INSERT INTO hoteis (nome_comercial, razao_social, cnpj, cidade, estado, pais) VALUES (?,?,?,?,?,?)",
                                 (nome_com, razao, cnpj, cidade, estado, pais))
                    h_id = cursor.lastrowid
                
                # --- SALVAMENTO BLINDADO DE ACOMODAÇÕES ---
                conn.execute("DELETE FROM acomodacoes WHERE hotel_id=?", (h_id,))
                for ac in st.session_state.form_data.get('acomodacoes', []):
                    # Limpeza do valor: remove vírgulas, espaços e valida se é número
                    val_limpo = str(ac['valor']).replace(',', '.').strip()
                    try:
                        val_final = float(val_limpo) if val_limpo else 0.0
                    except ValueError:
                        val_final = 0.0
                    
                    conn.execute("INSERT INTO acomodacoes (hotel_id, tipo, valor, obs) VALUES (?,?,?,?)", 
                                 (h_id, ac['tipo'], val_final, ac['obs']))
                
                conn.commit()
                st.success("Hotel salvo com sucesso!")
                time.sleep(1)
                st.session_state.id_edicao = None
                st.rerun()
            else:
                st.error("Nome Comercial é obrigatório.")

    # ==========================================
    # --- ABA 2: CONSULTA ---
    # ==========================================
    with tab_cons:
        busca = st.text_input("🔍 Buscar Hotel:")
        df_lista = pd.read_sql_query(f"SELECT * FROM hoteis WHERE nome_comercial LIKE '%{busca}%'", conn)
        
        for _, h in df_lista.iterrows():
            with st.container(border=True):
                col_txt, col_met, col_btn = st.columns([3, 2, 1])
                col_txt.markdown(f"### {h['nome_comercial']}")
                col_txt.write(f"📍 {h['cidade']} - {h['estado']}")
                
                # Exibição de Preço com tratamento
                precos_df = pd.read_sql_query("SELECT valor FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h['id']),))
                precos_df['valor'] = pd.to_numeric(precos_df['valor'], errors='coerce')
                min_p = precos_df['valor'].dropna().min()
                
                if pd.notna(min_p):
                    col_met.metric("A partir de", f"R$ {min_p:,.2f}")
                else:
                    col_met.info("Sob consulta")
                
                if col_btn.button("Detalhes", key=f"btn_{h['id']}"):
                    st.session_state.hotel_detalhe = h['id']
                    st.rerun()

        if 'hotel_detalhe' in st.session_state:
            st.divider()
            if st.button("⬅️ Voltar"): st.session_state.pop('hotel_detalhe'); st.rerun()
            # (Exibição de detalhes omitida para brevidade, mas mantida no seu código original)

if __name__ == "__main__":
    exibir_pagina_hoteis()