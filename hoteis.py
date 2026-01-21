import streamlit as st
import pandas as pd
import os, time, base64
from database import init_db
from utils import get_countries, get_states, get_cities

def exibir_pagina_hoteis():
    st.title("🏨 Gestão de Hotéis")
    conn = init_db()
    PASTA_ANEXOS = "arquivos_hoteis"
    if not os.path.exists(PASTA_ANEXOS): os.makedirs(PASTA_ANEXOS)

    # Inicialização de estados
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
            col_sel, col_btn = st.columns([3, 1])
            sel_nome = col_sel.selectbox("Escolha um hotel cadastrado", ["--- NOVO HOTEL ---"] + hoteis_db['nome_comercial'].tolist())
            
            if col_btn.button("Carregar Dados"):
                if sel_nome != "--- NOVO HOTEL ---":
                    h_id = hoteis_db[hoteis_db['nome_comercial'] == sel_nome]['id'].values[0]
                    st.session_state.id_edicao = int(h_id)
                    res = pd.read_sql_query(f"SELECT * FROM hoteis WHERE id={h_id}", conn).iloc[0]
                    st.session_state.form_data = res.to_dict()
                    st.session_state.acomodacoes_df = pd.read_sql_query(f"SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id={h_id}", conn)
                    st.session_state.pix_df = pd.read_sql_query(f"SELECT tipo, chave FROM pix WHERE hotel_id={h_id}", conn)
                    st.rerun()
                else:
                    st.session_state.id_edicao = None
                    st.session_state.form_data = {}
                    st.session_state.acomodacoes_df = pd.DataFrame(columns=['tipo', 'valor', 'obs'])
                    st.session_state.pix_df = pd.DataFrame(columns=['tipo', 'chave'])
                    st.rerun()

        fd = st.session_state.form_data
        
        with st.container(border=True):
            st.subheader("📍 Identificação e Localização")
            nome_c = st.text_input("Nome Comercial", value=fd.get('nome_comercial', ''))
            razao = st.text_input("Razão Social", value=fd.get('razao_social', ''))
            
            c_cep, c_tipo, c_logra = st.columns([1, 1, 2])
            cep = c_cep.text_input("CEP", value=fd.get('cep', ''))
            opcoes_log = ["Rua", "Avenida", "Alameda", "Praça", "Rodovia", "Travessa"]
            val_log = fd.get('tipo_logradouro', 'Rua')
            idx_log = opcoes_log.index(val_log) if val_log in opcoes_log else 0
            t_logra = c_tipo.selectbox("Tipo", opcoes_log, index=idx_log)
            logra = c_logra.text_input("Logradouro", value=fd.get('logradouro', ''))
            
            c_num, c_bai, c_comp = st.columns([1, 2, 2])
            num = c_num.text_input("Nº", value=fd.get('numero', ''))
            bairro = c_bai.text_input("Bairro", value=fd.get('bairro', ''))
            complem = c_comp.text_input("Complemento", value=fd.get('complemento', ''))
            
            col_p, col_e, col_c = st.columns(3)
            p_lista = get_countries()
            pais_atual = fd.get('pais') if fd.get('pais') in p_lista else 'Brazil'
            p_sel = col_p.selectbox("País", p_lista, index=p_lista.index(pais_atual))
            e_lista = get_states(p_sel)
            est_atual = fd.get('estado') if fd.get('estado') in e_lista else e_lista[0]
            e_sel = col_e.selectbox("Estado", e_lista, index=e_lista.index(est_atual) if est_atual in e_lista else 0)
            c_lista = get_cities(p_sel, e_sel)
            cid_atual = fd.get('cidade') if fd.get('cidade') in c_lista else c_lista[0]
            c_sel = col_c.selectbox("Cidade", c_lista, index=c_lista.index(cid_atual) if cid_atual in c_lista else 0)

            c_lat, c_lon = st.columns(2)
            lat = c_lat.text_input("Latitude", value=fd.get('latitude', ''))
            lon = c_lon.text_input("Longitude", value=fd.get('longitude', ''))

        st.subheader("📊 Tarifas e Financeiro")
        cq, cp = st.columns(2)
        with cq:
            st.session_state.acomodacoes_df = st.data_editor(
                st.session_state.get('acomodacoes_df', pd.DataFrame(columns=['tipo', 'valor', 'obs'])), 
                num_rows="dynamic", use_container_width=True, key="q_editor",
                column_config={"tipo": st.column_config.SelectboxColumn("Quarto", options=["Single", "Double", "Twin", "Triple", "Master"], required=True)}
            )
        with cp:
            st.session_state.pix_df = st.data_editor(
                st.session_state.get('pix_df', pd.DataFrame(columns=['tipo', 'chave'])), 
                num_rows="dynamic", use_container_width=True, key="p_editor",
                column_config={
                    "tipo": st.column_config.SelectboxColumn("Tipo de Chave", options=["CNPJ", "E-mail", "Telefone", "Chave Aleatória", "CPF"], required=True)
                }
            )

        st.subheader("📁 Anexos")
        if st.session_state.id_edicao:
            p_atual = os.path.join(PASTA_ANEXOS, str(st.session_state.id_edicao))
            if os.path.exists(p_atual):
                for arq in os.listdir(p_atual):
                    c_n, c_d = st.columns([4, 1])
                    c_n.caption(f"📄 {arq}")
                    if c_d.button("🗑️", key=f"del_{arq}"):
                        os.remove(os.path.join(p_atual, arq)); st.rerun()
        novos_f = st.file_uploader("Subir arquivos", accept_multiple_files=True)

        if st.button("💾 SALVAR HOTEL", type="primary", use_container_width=True):
            cursor = conn.cursor()
            if st.session_state.id_edicao:
                cursor.execute("""UPDATE hoteis SET nome_comercial=?, razao_social=?, cep=?, tipo_logradouro=?, logradouro=?, 
                                  numero=?, bairro=?, complemento=?, pais=?, estado=?, cidade=?, latitude=?, longitude=? WHERE id=?""", 
                               (nome_c, razao, cep, t_logra, logra, num, bairro, complem, p_sel, e_sel, c_sel, lat, lon, st.session_state.id_edicao))
                h_id = st.session_state.id_edicao
            else:
                cursor.execute("""INSERT INTO hoteis (nome_comercial, razao_social, cep, tipo_logradouro, logradouro, numero, bairro, complemento, pais, estado, cidade, latitude, longitude) 
                                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (nome_c, razao, cep, t_logra, logra, num, bairro, complem, p_sel, e_sel, c_sel, lat, lon))
                h_id = cursor.lastrowid
            
            conn.execute("DELETE FROM acomodacoes WHERE hotel_id=?", (h_id,))
            df_q = st.session_state.acomodacoes_df.copy(); df_q['hotel_id'] = h_id
            df_q.to_sql('acomodacoes', conn, if_exists='append', index=False)
            
            conn.execute("DELETE FROM pix WHERE hotel_id=?", (h_id,))
            df_p = st.session_state.pix_df.copy(); df_p['hotel_id'] = h_id
            df_p.to_sql('pix', conn, if_exists='append', index=False)
            
            if novos_f:
                p_save = os.path.join(PASTA_ANEXOS, str(h_id))
                if not os.path.exists(p_save): os.makedirs(p_save)
                for f in novos_f:
                    with open(os.path.join(p_save, f.name), "wb") as b: b.write(f.getbuffer())
            conn.commit(); st.success("✅ Salvo!"); time.sleep(1); st.rerun()

    # ==========================================
    # --- ABA 2: CONSULTA E COMPARATIVO ---
    # ==========================================
    with tab_cons:
        st.header("🔍 Busca e Comparação Lateral")
        f1, f2, f3 = st.columns(3)
        p_db = ["Todos"] + [r[0] for r in conn.execute("SELECT DISTINCT pais FROM hoteis").fetchall()]
        sel_p = f1.selectbox("Filtro País", p_db)
        e_db = ["Todos"] + [r[0] for r in conn.execute(f"SELECT DISTINCT estado FROM hoteis WHERE pais='{sel_p}'" if sel_p != "Todos" else "SELECT DISTINCT estado FROM hoteis").fetchall()]
        sel_e = f2.selectbox("Filtro Estado", e_db)
        c_db = ["Todos"] + [r[0] for r in conn.execute(f"SELECT DISTINCT cidade FROM hoteis WHERE estado='{sel_e}'" if sel_e != "Todos" else "SELECT DISTINCT cidade FROM hoteis").fetchall()]
        sel_c = f3.selectbox("Filtro Cidade", c_db)

        q = "SELECT * FROM hoteis WHERE 1=1"
        if sel_p != "Todos": q += f" AND pais='{sel_p}'"
        if sel_e != "Todos": q += f" AND estado='{sel_e}'"
        if sel_c != "Todos": q += f" AND cidade='{sel_c}'"
        df_final = pd.read_sql_query(q, conn)

        if not df_final.empty:
            temp_list = []
            for _, r in df_final.iterrows():
                with st.container(border=True):
                    ci, cc = st.columns([4, 1])
                    ci.write(f"🏨 **{r['nome_comercial']}**")
                    if cc.checkbox("Comparar", key=f"cb_{r['id']}"): temp_list.append(r['id'])
            
            if st.button("📊 GERAR COMPARATIVO", type="primary"):
                st.session_state.hoteis_comparar = temp_list

        if st.session_state.hoteis_comparar:
            st.divider()
            cores = ["#1E3A8A", "#B91C1C", "#15803D", "#7E22CE", "#C2410C"]
            
            cols = st.columns(len(st.session_state.hoteis_comparar))
            for i, h_id in enumerate(st.session_state.hoteis_comparar):
                cor = cores[i % len(cores)]
                with cols[i]:
                    h = pd.read_sql_query(f"SELECT * FROM hoteis WHERE id={h_id}", conn).iloc[0]
                    
                    st.markdown(f"""<div style='background-color:{cor}; padding:10px; border-radius:10px 10px 0 0; color:white; text-align:center;'>
                                    <h4 style='margin:0; color:white;'>{h['nome_comercial'].upper()}</h4></div>""", unsafe_allow_html=True)
                    
                    with st.container(border=True):
                        t1, t2, t3 = st.tabs(["💰 Tarifas", "📂 Anexos", "📍 Mapa"])
                        with t1:
                            df_t = pd.read_sql_query(f"SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id={h_id}", conn)
                            st.dataframe(df_t.style.set_properties(**{'background-color': cor + '15', 'color': 'black'}), use_container_width=True, hide_index=True)
                        
                        with t2:
                            p_path = os.path.join(PASTA_ANEXOS, str(h_id))
                            if os.path.exists(p_path):
                                for a in os.listdir(p_path):
                                    st.write(f"📄 **{a}**")
                                    f_path = os.path.join(p_path, a)
                                    if a.lower().endswith(('png', 'jpg', 'jpeg')):
                                        st.image(f_path)
                                    elif a.lower().endswith('pdf'):
                                        with open(f_path, "rb") as f:
                                            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                                        st.markdown(pdf_display, unsafe_allow_html=True)
                                    st.download_button("Baixar", open(f_path, "rb"), file_name=a, key=f"d_{h_id}_{a}")
                        
                        with t3:
                            # --- SECÇÃO DO MAPA COM BOTÃO DE PARTILHA ---
                            if h['latitude'] and h['longitude']:
                                # Exibe o mapa no Streamlit
                                st.map(pd.DataFrame({'lat': [float(h['latitude'])], 'lon': [float(h['longitude'])]}))
                                
                                # Botão de Partilha/Navegação
                                url_maps = f"https://www.google.com/maps/search/?api=1&query={h['latitude']},{h['longitude']}"
                                st.link_button("🌐 Abrir e Partilhar no Google Maps", url_maps, use_container_width=True)
                            else:
                                st.warning("Coordenadas não disponíveis para este hotel.")