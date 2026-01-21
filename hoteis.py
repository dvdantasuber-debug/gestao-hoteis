import streamlit as st
import pandas as pd
import os, time, sqlite3
from database import init_db
from utils import get_countries, get_states, get_cities

def exibir_pagina_hoteis():
    st.title("🏨 Gestão de Hotéis")
    conn = init_db()
    
    if 'id_edicao' not in st.session_state: st.session_state.id_edicao = None
    if 'form_data' not in st.session_state: st.session_state.form_data = {'acomodacoes': [], 'pix': []}

    tab_cad, tab_cons = st.tabs(["📝 Cadastro e Edição", "🔍 Consulta e Gestão"])

    # --- ABA 1: CADASTRO E EDIÇÃO ---
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
                
                # Carregar dependentes
                ac = pd.read_sql_query("SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h_id),))
                st.session_state.form_data['acomodacoes'] = ac.to_dict('records')
                try:
                    px = pd.read_sql_query("SELECT tipo, chave FROM pix WHERE hotel_id=?", conn, params=(int(h_id),))
                    st.session_state.form_data['pix'] = px.to_dict('records')
                except: st.session_state.form_data['pix'] = []
                st.rerun()

            if col_btn_new.button("➕ Novo Cadastro", use_container_width=True):
                st.session_state.id_edicao = None
                st.session_state.form_data = {'acomodacoes': [], 'pix': []}
                st.rerun()

        # Formulário Principal
        st.subheader("Informações Gerais")
        c1, c2, c3 = st.columns(3)
        nome_com = c1.text_input("Nome Comercial", value=st.session_state.form_data.get('nome_comercial', ''))
        razao = c2.text_input("Razão Social", value=st.session_state.form_data.get('razao_social', ''))
        cnpj = c3.text_input("CNPJ", value=st.session_state.form_data.get('cnpj', ''))

        st.subheader("Localização")
        l1, l2, l3 = st.columns(3)
        p_lista = get_countries()
        pais = l1.selectbox("País", p_lista, index=p_lista.index(st.session_state.form_data.get('pais', 'Brasil')) if st.session_state.form_data.get('pais') in p_lista else 0)
        e_lista = get_states(pais)
        estado = l2.selectbox("Estado", e_lista, index=e_lista.index(st.session_state.form_data.get('estado', '')) if st.session_state.form_data.get('estado') in e_lista else 0)
        c_lista = get_cities(pais, estado)
        cidade = l3.selectbox("Cidade", c_lista, index=c_lista.index(st.session_state.form_data.get('cidade', '')) if st.session_state.form_data.get('cidade') in c_lista else 0)

        st.subheader("Dados Financeiros (PIX)")
        col_px1, col_px2, col_px3 = st.columns([2, 3, 1])
        t_pix = col_px1.selectbox("Tipo de Chave", ["CNPJ", "E-mail", "Telefone", "Chave Aleatória"], key="tp_pix")
        v_pix = col_px2.text_input("Chave PIX", key="val_pix")
        if col_px3.button("Adicionar PIX"):
            if v_pix:
                st.session_state.form_data['pix'].append({'tipo': t_pix, 'chave': v_pix})
                st.rerun()
        if st.session_state.form_data.get('pix'):
            st.table(pd.DataFrame(st.session_state.form_data['pix']))
            if st.button("Limpar PIX"): st.session_state.form_data['pix'] = []; st.rerun()

        st.subheader("Tarifário")
        with st.expander("💰 Configurar Tarifas", expanded=True):
            a1, a2, a3, a4 = st.columns([2, 1, 2, 0.5])
            tipo_ac = a1.text_input("Tipo de Quarto (ex: Single)")
            valor_ac = a2.text_input("Valor (ex: 500,00)")
            obs_ac = a3.text_input("Observações")
            if a4.button("➕", key="add_ac"):
                if tipo_ac:
                    st.session_state.form_data['acomodacoes'].append({'tipo': tipo_ac, 'valor': valor_ac, 'obs': obs_ac})
                    st.rerun()
            if st.session_state.form_data.get('acomodacoes'):
                st.table(pd.DataFrame(st.session_state.form_data['acomodacoes']))
                if st.button("Limpar Tarifas"): st.session_state.form_data['acomodacoes'] = []; st.rerun()

        if st.button("💾 SALVAR HOTEL", use_container_width=True, type="primary"):
            if nome_com:
                cursor = conn.cursor()
                if st.session_state.id_edicao:
                    h_id = st.session_state.id_edicao
                    cursor.execute("UPDATE hoteis SET nome_comercial=?, razao_social=?, cnpj=?, cidade=?, estado=?, pais=? WHERE id=?",
                                 (nome_com, razao, cnpj, cidade, estado, pais, h_id))
                else:
                    cursor.execute("INSERT INTO hoteis (nome_comercial, razao_social, cnpj, cidade, estado, pais) VALUES (?,?,?,?,?,?)",
                                 (nome_com, razao, cnpj, cidade, estado, pais))
                    h_id = cursor.lastrowid
                
                # Sincronizar Tabelas Filhas
                conn.execute("DELETE FROM acomodacoes WHERE hotel_id=?", (h_id,))
                for ac in st.session_state.form_data['acomodacoes']:
                    val_limpo = str(ac['valor']).replace(',', '.').strip()
                    try: val_final = float(val_limpo)
                    except: val_final = 0.0
                    conn.execute("INSERT INTO acomodacoes (hotel_id, tipo, valor, obs) VALUES (?,?,?,?)", (h_id, ac['tipo'], val_final, ac['obs']))
                
                try:
                    conn.execute("DELETE FROM pix WHERE hotel_id=?", (h_id,))
                    for px in st.session_state.form_data['pix']:
                        conn.execute("INSERT INTO pix (hotel_id, tipo, chave) VALUES (?,?,?)", (h_id, px['tipo'], px['chave']))
                except: pass # Tabela pix será criada no database.py
                
                conn.commit()
                st.success("Salvo com sucesso!")
                time.sleep(1)
                st.session_state.id_edicao = None
                st.rerun()

    # --- ABA 2: CONSULTA E EXCLUSÃO ---
    with tab_cons:
        busca = st.text_input("🔍 Filtrar Hotel:")
        df_lista = pd.read_sql_query(f"SELECT * FROM hoteis WHERE nome_comercial LIKE '%{busca}%'", conn)
        for _, h in df_lista.iterrows():
            with st.container(border=True):
                col_txt, col_met, col_btn = st.columns([3, 2, 1])
                col_txt.markdown(f"### {h['nome_comercial']}")
                col_txt.write(f"📍 {h['cidade']} - {h['estado']}")
                
                # Cálculo de preço seguro para exibição
                precos = pd.read_sql_query("SELECT valor FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h['id']),))
                precos['valor'] = pd.to_numeric(precos['valor'], errors='coerce')
                min_p = precos['valor'].dropna().min()
                if pd.notna(min_p): col_met.metric("A partir de", f"R$ {min_p:,.2f}")
                
                if col_btn.button("Gerir", key=f"btn_{h['id']}"):
                    st.session_state.hotel_detalhe = h['id']
                    st.rerun()

        if 'hotel_detalhe' in st.session_state:
            h_id_det = int(st.session_state.hotel_detalhe)
            h = pd.read_sql_query("SELECT * FROM hoteis WHERE id=?", conn, params=(h_id_det,)).iloc[0]
            st.divider()
            c_v, c_e = st.columns([4, 1])
            if c_v.button("⬅️ Fechar"): st.session_state.pop('hotel_detalhe'); st.rerun()
            
            # BOTÃO DE EXCLUSÃO
            if c_e.button("🗑️ EXCLUIR", type="secondary"):
                conn.execute("DELETE FROM acomodacoes WHERE hotel_id=?", (h_id_det,))
                conn.execute("DELETE FROM pix WHERE hotel_id=?", (h_id_det,))
                conn.execute("DELETE FROM hoteis WHERE id=?", (h_id_det,))
                conn.commit()
                st.success("Excluído!")
                time.sleep(1)
                st.session_state.pop('hotel_detalhe')
                st.rerun()
            
            st.subheader(f"🏨 {h['nome_comercial']}")
            st.table(pd.read_sql_query("SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id=?", conn, params=(h_id_det,)))