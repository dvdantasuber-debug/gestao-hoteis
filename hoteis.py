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
            col_sel, col_btn_new = st.columns([3, 1])
            hotel_selecionado = col_sel.selectbox("Escolha um hotel:", [""] + hoteis_db['nome_comercial'].tolist())
            
            if col_sel.button("Carregar para Edição") and hotel_selecionado:
                h_id = hoteis_db[hoteis_db['nome_comercial'] == hotel_selecionado]['id'].iloc[0]
                st.session_state.id_edicao = h_id
                # Carregar dados do banco
                h_data = pd.read_sql_query("SELECT * FROM hoteis WHERE id=?", conn, params=(int(h_id),)).iloc[0]
                st.session_state.form_data = h_data.to_dict()
                # Carregar Acomodações
                ac = pd.read_sql_query("SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h_id),))
                st.session_state.form_data['acomodacoes'] = ac.to_dict('records')
                # Carregar PIX
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

        # --- FORMULÁRIO PRINCIPAL ---
        st.subheader("Informações Gerais")
        c1, c2, c3 = st.columns(3)
        nome_com = c1.text_input("Nome Comercial", value=st.session_state.form_data.get('nome_comercial', ''))
        razao = c2.text_input("Razão Social", value=st.session_state.form_data.get('razao_social', ''))
        cnpj = c3.text_input("CNPJ", value=st.session_state.form_data.get('cnpj', ''))

        st.subheader("Localização")
        l1, l2, l3 = st.columns(3)
        pais = l1.selectbox("País", get_countries(), index=get_countries().index(st.session_state.form_data.get('pais', 'Brasil')) if st.session_state.form_data.get('pais') in get_countries() else 0)
        estado = l2.selectbox("Estado", get_states(pais), index=get_states(pais).index(st.session_state.form_data.get('estado', '')) if st.session_state.form_data.get('estado') in get_states(pais) else 0)
        cidade = l3.selectbox("Cidade", get_cities(pais, estado), index=get_cities(pais, estado).index(st.session_state.form_data.get('cidade', '')) if st.session_state.form_data.get('cidade') in get_cities(pais, estado) else 0)

        with st.expander("Endereço Detalhado"):
            ed1, ed2, ed3 = st.columns([1, 3, 1])
            cep = ed1.text_input("CEP", value=st.session_state.form_data.get('cep', ''))
            logradouro = ed2.text_input("Logradouro", value=st.session_state.form_data.get('logradouro', ''))
            num = ed3.text_input("Nº", value=st.session_state.form_data.get('numero', ''))
            
            ed4, ed5 = st.columns(2)
            lat = ed4.text_input("Latitude", value=st.session_state.form_data.get('latitude', ''))
            lon = ed5.text_input("Longitude", value=st.session_state.form_data.get('longitude', ''))

        # --- SEÇÃO FINANCEIRA (PIX) ---
        st.subheader("Dados Financeiros (PIX)")
        if 'pix' not in st.session_state.form_data: st.session_state.form_data['pix'] = []
        
        col_px1, col_px2, col_px3 = st.columns([2, 3, 1])
        t_pix = col_px1.selectbox("Tipo de Chave", ["CNPJ", "E-mail", "Telefone", "Chave Aleatória"], key="tp_pix")
        v_pix = col_px2.text_input("Chave PIX", key="val_pix")
        if col_px3.button("➕", key="add_pix"):
            st.session_state.form_data['pix'].append({'tipo': t_pix, 'chave': v_pix})
            st.rerun()
        
        if st.session_state.form_data['pix']:
            df_pix = pd.DataFrame(st.session_state.form_data['pix'])
            st.table(df_pix)
            if st.button("Limpar Chaves PIX"):
                st.session_state.form_data['pix'] = []
                st.rerun()

        # --- SEÇÃO DE ACOMODAÇÕES ---
        st.subheader("Tarifário de Acomodações")
        if 'acomodacoes' not in st.session_state.form_data: st.session_state.form_data['acomodacoes'] = []
        
        a1, a2, a3, a4 = st.columns([2, 1, 2, 0.5])
        tipo_ac = a1.text_input("Tipo de Quarto (ex: Single, Double)")
        valor_ac = a2.number_input("Valor Diária", min_value=0.0, step=50.0)
        obs_ac = a3.text_input("Observações")
        if a4.button("➕", key="add_ac"):
            st.session_state.form_data['acomodacoes'].append({'tipo': tipo_ac, 'valor': valor_ac, 'obs': obs_ac})
            st.rerun()

        if st.session_state.form_data['acomodacoes']:
            st.table(pd.DataFrame(st.session_state.form_data['acomodacoes']))
            if st.button("Limpar Acomodações"):
                st.session_state.form_data['acomodacoes'] = []
                st.rerun()

        # --- BOTÃO SALVAR ---
        if st.button("💾 SALVAR HOTEL COMPLETO", use_container_width=True, type="primary"):
            if nome_com:
                if st.session_state.id_edicao:
                    # UPDATE
                    conn.execute("""UPDATE hoteis SET nome_comercial=?, razao_social=?, cnpj=?, cidade=?, estado=?, pais=?, 
                                    latitude=?, longitude=?, cep=?, logradouro=?, numero=? WHERE id=?""",
                                 (nome_com, razao, cnpj, cidade, estado, pais, lat, lon, cep, logradouro, num, st.session_state.id_edicao))
                    h_id = st.session_state.id_edicao
                else:
                    # INSERT
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO hoteis (nome_comercial) VALUES (?)", (nome_com,))
                    h_id = cursor.lastrowid
                    conn.execute("""UPDATE hoteis SET razao_social=?, cnpj=?, cidade=?, estado=?, pais=?, 
                                    latitude=?, longitude=?, cep=?, logradouro=?, numero=? WHERE id=?""",
                                 (razao, cnpj, cidade, estado, pais, lat, lon, cep, logradouro, num, h_id))
                
                # Sincronizar Tabelas Filhas (Acomodações)
                conn.execute("DELETE FROM acomodacoes WHERE hotel_id=?", (h_id,))
                for ac in st.session_state.form_data['acomodacoes']:
                    conn.execute("INSERT INTO acomodacoes (hotel_id, tipo, valor, obs) VALUES (?,?,?,?)", (h_id, ac['tipo'], ac['valor'], ac['obs']))
                
                # Sincronizar Tabelas Filhas (PIX) - COM CORREÇÃO PARA DEPLOY
                try:
                    conn.execute("DELETE FROM pix WHERE hotel_id=?", (h_id,))
                    for px in st.session_state.form_data.get('pix', []):
                        conn.execute("INSERT INTO pix (hotel_id, tipo, chave) VALUES (?,?,?)", (h_id, px['tipo'], px['chave']))
                except sqlite3.OperationalError:
                    # Se a tabela não existir, cria e tenta novamente
                    conn.execute("CREATE TABLE IF NOT EXISTS pix (id INTEGER PRIMARY KEY AUTOINCREMENT, hotel_id INTEGER, tipo TEXT, chave TEXT)")
                    for px in st.session_state.form_data.get('pix', []):
                        conn.execute("INSERT INTO pix (hotel_id, tipo, chave) VALUES (?,?,?)", (h_id, px['tipo'], px['chave']))
                
                conn.commit()
                st.success("Hotel Salvo com Sucesso!")
                time.sleep(1)
                st.session_state.id_edicao = None
                st.rerun()
            else:
                st.error("O campo 'Nome Comercial' é obrigatório.")

    # ==========================================
    # --- ABA 2: CONSULTA E COMPARATIVO ---
    # ==========================================
    with tab_cons:
        st.subheader("Pesquisa de Hotéis")
        busca = st.text_input("🔍 Digite o nome do hotel para filtrar:")
        
        query = "SELECT * FROM hoteis"
        if busca: query += f" WHERE nome_comercial LIKE '%{busca}%'"
        
        df_lista = pd.read_sql_query(query, conn)
        
        for idx, h in df_lista.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"### {h['nome_comercial']}")
                c1.write(f"📍 {h['cidade']} - {h['estado']} ({h['pais']})")
                
                # Resumo de preços
                precos = pd.read_sql_query("SELECT tipo, valor FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h['id']),))
                if not precos.empty:
                    min_p = precos['valor'].min()
                    c2.metric("Tarifa Inicial", f"R$ {min_p:,.2f}")
                
                if c3.button("Ver Detalhes", key=f"det_{h['id']}"):
                    st.session_state.hotel_detalhe = h['id']
            
        # Modal de Detalhes (Simulado por Container)
        if 'hotel_detalhe' in st.session_state:
            h_id = st.session_state.hotel_detalhe
            h = pd.read_sql_query("SELECT * FROM hoteis WHERE id=?", conn, params=(int(h_id),)).iloc[0]
            
            st.divider()
            st.button("⬅️ Voltar para Lista", on_click=lambda: st.session_state.pop('hotel_detalhe'))
            
            t1, t2, t3 = st.tabs(["📋 Dados e Tarifas", "📂 Anexos", "🗺️ Mapa"])
            
            with t1:
                st.write(f"**Razão Social:** {h['razao_social']}")
                st.write(f"**CNPJ:** {h['cnpj']}")
                st.write(f"**Endereço:** {h['logradouro']}, {h['numero']} - {h['bairro']}")
                
                st.subheader("Tarifas")
                ac_df = pd.read_sql_query("SELECT tipo as Quarto, valor as Diária, obs as Observação FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h_id),))
                st.table(ac_df)

            with t2:
                st.info("Funcionalidade de anexos disponível após upload de arquivos na pasta arquivos_hoteis.")

            with t3:
                if h['latitude'] and h['longitude']:
                    try:
                        map_data = pd.DataFrame({'lat': [float(h['latitude'])], 'lon': [float(h['longitude'])]})
                        st.map(map_data)
                        url_maps = f"https://www.google.com/maps?q={h['latitude']},{h['longitude']}"
                        st.link_button("🌐 Ver no Google Maps", url_maps)
                    except:
                        st.warning("Coordenadas inválidas para exibição no mapa.")
                else:
                    st.warning("Coordenadas não cadastradas.")

if __name__ == "__main__":
    exibir_pagina_hoteis()