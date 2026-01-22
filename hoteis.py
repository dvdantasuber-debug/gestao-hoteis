import streamlit as st
import pandas as pd
from database import init_db
from utils import get_countries, get_states, get_cities

def exibir_pagina_hoteis():
    st.title("🏨 Cadastro e Gestão de Hotéis")
    conn = init_db()
    if not conn: return
    
    tab_cad, tab_list, tab_aco = st.tabs(["📝 Cadastrar Hotel", "🔍 Lista de Hotéis", "🛌 Acomodações"])

    with tab_cad:
        with st.container(border=True):
            l1, l2, l3 = st.columns(3)
            p_lista = get_countries()
            pais = l1.selectbox("País", p_lista, index=p_lista.index("Brazil") if "Brazil" in p_lista else 0)
            e_lista = get_states(pais)
            estado = l2.selectbox("Estado", e_lista, index=e_lista.index("Goiás") if "Goiás" in e_lista else 0)
            c_lista = get_cities(pais, estado)
            cidade = l3.selectbox("Cidade", c_lista, index=c_lista.index("Goiânia") if "Goiânia" in c_lista else 0)
            
            nome = st.text_input("Nome Comercial do Hotel")
            cnpj = st.text_input("CNPJ")
            
            if st.button("💾 Salvar Hotel", type="primary"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO hoteis (nome_comercial, cnpj, cidade, estado, pais) VALUES (%s, %s, %s, %s)", 
                               (nome, cnpj, cidade, estado, pais))
                conn.commit(); st.success("Hotel cadastrado no Supabase!")

    with tab_list:
        busca = st.text_input("Filtrar Hotéis")
        hoteis = pd.read_sql_query("SELECT * FROM hoteis WHERE nome_comercial ILIKE %s", conn, params=(f"%{busca}%",))
        st.dataframe(hoteis, use_container_width=True)
        
        st.subheader("Excluir Hotel")
        id_del = st.number_input("ID do Hotel para excluir", step=1)
        if st.button("🗑️ Excluir permanentemente"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hoteis WHERE id = %s", (id_del,))
            conn.commit(); st.warning("Hotel removido."); st.rerun()

    with tab_aco:
        st.subheader("Gerenciar Quartos/Tarifas")
        h_lista = pd.read_sql_query("SELECT id, nome_comercial FROM hoteis ORDER BY nome_comercial", conn)
        h_sel = st.selectbox("Selecione o Hotel", h_lista['nome_comercial'].tolist())
        
        if h_sel:
            h_id = h_lista[h_lista['nome_comercial'] == h_sel]['id'].values[0]
            with st.form("cad_aco"):
                tipo = st.text_input("Tipo de Quarto (Ex: Single, Double)")
                valor = st.number_input("Valor da Diária", min_value=0.0)
                obs = st.text_area("Observações (Café, Estacionamento...)")
                if st.form_submit_button("Adicionar Acomodação"):
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO acomodacoes (hotel_id, tipo, valor, obs) VALUES (%s, %s, %s, %s)", 
                                   (int(h_id), tipo, valor, obs))
                    conn.commit(); st.success("Quarto adicionado!"); st.rerun()
            
            st.divider()
            acos = pd.read_sql_query("SELECT * FROM acomodacoes WHERE hotel_id = %s", conn, params=(int(h_id),))
            st.table(acos)