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
    if 'hoteis_comparar' not in st.session_state: st.session_state.hoteis_comparar = []

    tab_cad, tab_cons = st.tabs(["📝 Cadastro e Edição", "🔍 Consulta e Comparativo"])

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
                
                # Carregar Acomodações
                ac = pd.read_sql_query("SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h_id),))
                st.session_state.form_data['acomodacoes'] = ac.to_dict('records')
                
                # Carregar PIX com tratamento de erro
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

        # --- FORMULÁRIO ---
        st.subheader("Informações Gerais")
        c1, c2, c3 = st.columns(3)
        nome_com = c1.text_input("Nome Comercial", value=st.session_state.form_data.get('nome_comercial', ''))
        razao = c2.text_input("Razão Social", value=st.session_state.form_data.get('razao_social', ''))
        cnpj = c3.text_input("CNPJ", value=st.session_state.form_data.get('cnpj', ''))

        st.subheader("Localização")
        l1, l2, l3 = st.columns(3)
        pais_lista = get_countries()
        p_idx = pais_lista.index(st.session_state.form_data.get('pais')) if st.session_state.form_data.get('pais') in pais_lista else 0
        pais = l1.selectbox("País", pais_lista, index=p_idx)
        
        est_lista = get_states(pais)
        e_idx = est_lista.index(st.session_state.form_data.get('estado')) if st.session_state.form_data.get('estado') in est_lista else 0
        estado = l2.selectbox("Estado", est_lista, index=e_idx)
        
        cid_lista = get_cities(pais, estado)
        c_idx = cid_lista.index(st.session_state.form_data.get('cidade')) if st.session_state.form_data.get('cidade') in cid_lista else 0
        cidade = l3.selectbox("Cidade", cid_lista, index=c_idx)

        with st.expander("Endereço Detalhado"):
            ed1, ed2, ed3 = st.columns([1, 3, 1])
            cep = ed1.text_input("CEP", value=st.session_state.form_data.get('cep', ''))
            logradouro = ed2.text_input("Logradouro", value=st.session_state.form_data.get('logradouro', ''))
            num = ed3.text_input("Nº", value=st.session_state.form_data.get('numero', ''))
            lat = st.text_input("Latitude", value=st.session_state.form_data.get('latitude', ''))
            lon = st.text_input("Longitude", value=st.session_state.form_data.get('longitude', ''))

        # --- SEÇÃO PIX ---
        st.subheader("Dados Financeiros (PIX)")
        if 'pix' not in st.session_state.form_data: st.session_state.form_data['pix'] = []
        col_px1, col_px2, col_px3 = st.columns([2, 3, 1])
        t_pix = col_px1.selectbox("Tipo", ["CNPJ", "E-mail", "Telefone", "Chave Aleatória"], key="tp_pix")
        v_pix = col_px2.text_input("Chave", key="val_pix")
        if col_px3.button("➕", key="add_pix"):
            st.session_state.form_data['pix'].append({'tipo': t_pix, 'chave': v_pix})
            st.rerun()
        if st.session_state.form_data['pix']:
            st.table(pd.DataFrame(st.session_state.form_data['pix']))
            if st.button("Limpar PIX"):
                st.session_state.form_data['pix'] = []
                st.rerun()

        # --- SEÇÃO ACOMODAÇÕES ---
        st.subheader("Tarifário")
        if 'acomodacoes' not in st.session_state.form_data: st.session_state.form_data['acomodacoes'] = []
        a1, a2, a3, a4 = st.columns([2, 1, 2, 0.5])
        tipo_ac = a1.text_input("Tipo de Quarto")
        valor_ac = a2.number_input("Valor Diária", min_value=0.0, step=10.0)
        obs_ac = a3.text_input("Obs")
        if a4.button("➕", key="add_ac"):
            st.session_state.form_data['acomodacoes'].append({'tipo': tipo_ac, 'valor': valor_ac, 'obs': obs_ac})
            st.rerun()
        if st.session_state.form_data['acomodacoes']:
            st.table(pd.DataFrame(st.session_state.form_data['acomodacoes']))
            if st.button("Limpar Tarifas"):
                st.session_state.form_data['acomodacoes'] = []
                st.rerun()

        # --- SALVAR ---
        if st.button("💾 SALVAR HOTEL", use_container_width=True, type="primary"):
            if nome_com:
                cursor = conn.cursor()
                if st.session_state.id_edicao:
                    h_id = st.session_state.id_edicao
                    cursor.execute("""UPDATE hoteis SET nome_comercial=?, razao_social=?, cnpj=?, cidade=?, estado=?, pais=?, 
                                    latitude=?, longitude=?, cep=?, logradouro=?, numero=? WHERE id=?""",
                                 (nome_com, razao, cnpj, cidade, estado, pais, lat, lon, cep, logradouro, num, h_id))
                else:
                    cursor.execute("INSERT INTO hoteis (nome_comercial) VALUES (?)", (nome_com,))
                    h_id = cursor.lastrowid
                    cursor.execute("""UPDATE hoteis SET razao_social=?, cnpj=?, cidade=?, estado=?, pais=?, 
                                    latitude=?, longitude=?, cep=?, logradouro=?, numero=? WHERE id=?""",
                                 (razao, cnpj, cidade, estado, pais, lat, lon, cep, logradouro, num, h_id))
                
                conn.execute("DELETE FROM acomodacoes WHERE hotel_id=?", (h_id,))
                for ac in st.session_state.form_data['acomodacoes']:
                    conn.execute("INSERT INTO acomodacoes (hotel_id, tipo, valor, obs) VALUES (?,?,?,?)", (h_id, ac['tipo'], float(ac['valor']), ac['obs']))
                
                try:
                    conn.execute("DELETE FROM pix WHERE hotel_id=?", (h_id,))
                    for px in st.session_state.form_data.get('pix', []):
                        conn.execute("INSERT INTO pix (hotel_id, tipo, chave) VALUES (?,?,?)", (h_id, px['tipo'], px['chave']))
                except:
                    conn.execute("CREATE TABLE IF NOT EXISTS pix (id INTEGER PRIMARY KEY AUTOINCREMENT, hotel_id INTEGER, tipo TEXT, chave TEXT)")
                    conn.commit()

                conn.commit()
                st.success("Salvo com sucesso!")
                time.sleep(1)
                st.session_state.id_edicao = None
                st.rerun()

    # ==========================================
    # --- ABA 2: CONSULTA ---
    # ==========================================
    with tab_cons:
        busca = st.text_input("🔍 Buscar Hotel:")
        query = "SELECT * FROM hoteis"
        if busca: query += f" WHERE nome_comercial LIKE '%{busca}%'"
        df_lista = pd.read_sql_query(query, conn)
        
        for _, h in df_lista.iterrows():
            with st.container(border=True):
                col_txt, col_met, col_btn = st.columns([3, 2, 1])
                col_txt.markdown(f"### {h['nome_comercial']}")
                col_txt.write(f"📍 {h['cidade']} - {h['estado']}")
                
                # --- CORREÇÃO FINAL PARA VALUEERROR ---
                precos_df = pd.read_sql_query("SELECT valor FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h['id']),))
                
                if not precos_df.empty:
                    # Força a coluna a ser numérica, transformando erros em NaN
                    precos_df['valor'] = pd.to_numeric(precos_df['valor'], errors='coerce')
                    # Remove os NaN (valores inválidos ou nulos)
                    precos_validos = precos_df['valor'].dropna()
                    
                    if not precos_validos.empty:
                        min_p = float(precos_validos.min())
                        col_met.metric("Tarifa Inicial", f"R$ {min_p:,.2f}")
                    else:
                        col_met.info("Sem tarifas")
                else:
                    col_met.info("Sem tarifas")
                
                if col_btn.button("Ver Detalhes", key=f"btn_{h['id']}"):
                    st.session_state.hotel_detalhe = h['id']
                    st.rerun()
            
        if 'hotel_detalhe' in st.session_state:
            h_id = st.session_state.hotel_detalhe
            h_res = pd.read_sql_query("SELECT * FROM hoteis WHERE id=?", conn, params=(int(h_id),))
            if not h_res.empty:
                h = h_res.iloc[0]
                st.divider()
                if st.button("⬅️ Fechar Detalhes"): st.session_state.pop('hotel_detalhe'); st.rerun()
                
                st.subheader(f"🏨 {h['nome_comercial']}")
                st.write(f"**Razão:** {h['razao_social']} | **CNPJ:** {h['cnpj']}")
                st.write(f"**Endereço:** {h['logradouro']}, {h['numero']} - {h['cep']}")
                
                st.markdown("#### 💳 Tarifário")
                res_ac = pd.read_sql_query("SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h_id),))
                st.dataframe(res_ac, hide_index=True, use_container_width=True)

                if h['latitude'] and h['longitude']:
                    try:
                        st.markdown("#### 🗺️ Localização")
                        map_df = pd.DataFrame({'lat': [float(h['latitude'])], 'lon': [float(h['longitude'])]})
                        st.map(map_df)
                    except: st.warning("Coordenadas inválidas.")

if __name__ == "__main__":
    exibir_pagina_hoteis()