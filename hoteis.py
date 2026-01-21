import streamlit as st
import pandas as pd
import os, time, sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import init_db
from utils import get_countries, get_states, get_cities

def enviar_email_cotacao(destinatario, assunto, corpo):
    """Função base para enviar e-mail utilizando os Secrets do Streamlit"""
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["EMAIL_USUARIO"]
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'html'))

        server = smtplib.SMTP(st.secrets["EMAIL_SMTP"], st.secrets["EMAIL_PORTA"])
        server.starttls()
        server.login(st.secrets["EMAIL_USUARIO"], st.secrets["EMAIL_SENHA"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

def exibir_pagina_hoteis():
    st.title("🏨 Gestão de Hotéis")
    conn = init_db()
    
    if 'id_edicao' not in st.session_state: st.session_state.id_edicao = None
    if 'form_data' not in st.session_state: st.session_state.form_data = {'acomodacoes': [], 'pix': []}

    tab_cad, tab_cons = st.tabs(["📝 Cadastro e Edição", "🔍 Consulta e Gestão"])

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
                st.rerun()

            if col_btn_new.button("➕ Novo Cadastro", use_container_width=True):
                st.session_state.id_edicao = None
                st.session_state.form_data = {'acomodacoes': [], 'pix': []}
                st.rerun()

        st.subheader("Informações Gerais")
        c1, c2, c3 = st.columns(3)
        nome_com = c1.text_input("Nome Comercial", value=st.session_state.form_data.get('nome_comercial', ''))
        razao = c2.text_input("Razão Social", value=st.session_state.form_data.get('razao_social', ''))
        cnpj = c3.text_input("CNPJ", value=st.session_state.form_data.get('cnpj', ''))

        st.subheader("📍 Localização e Endereço")
        l1, l2, l3 = st.columns(3)
        
        # --- DEFINIÇÃO DE PADRÕES: Brazil, Goiás, Goiânia ---
        p_lista = get_countries()
        p_idx = p_lista.index("Brazil") if "Brazil" in p_lista else 0
        pais = l1.selectbox("País", p_lista, index=p_lista.index(st.session_state.form_data.get('pais')) if st.session_state.form_data.get('pais') in p_lista else p_idx)
        
        e_lista = get_states(pais)
        e_idx = e_lista.index("Goiás") if "Goiás" in e_lista else 0
        estado = l2.selectbox("Estado", e_lista, index=e_lista.index(st.session_state.form_data.get('estado')) if st.session_state.form_data.get('estado') in e_lista else e_idx)
        
        c_lista = get_cities(pais, estado)
        c_idx = c_lista.index("Goiânia") if "Goiânia" in c_lista else 0
        cidade = l3.selectbox("Cidade", c_lista, index=c_lista.index(st.session_state.form_data.get('cidade')) if st.session_state.form_data.get('cidade') in c_lista else c_idx)

        with st.expander("Detalhes do Endereço", expanded=True):
            ed1, ed2, ed3 = st.columns([1.5, 3, 1])
            cep = ed1.text_input("CEP", value=st.session_state.form_data.get('cep', ''))
            logradouro = ed2.text_input("Logradouro", value=st.session_state.form_data.get('logradouro', ''))
            num = ed3.text_input("Nº", value=st.session_state.form_data.get('numero', ''))
            
            coord1, coord2 = st.columns(2)
            lat = coord1.text_input("Latitude", value=st.session_state.form_data.get('latitude', ''))
            lon = coord2.text_input("Longitude", value=st.session_state.form_data.get('longitude', ''))

        # (Restante das seções de PIX e Tarifário mantidas...)
        # Ao final, o botão Salvar utiliza os campos lat, lon, cep, etc.
        if st.button("💾 SALVAR HOTEL", use_container_width=True, type="primary"):
            # Lógica de banco de dados (INSERT/UPDATE) incluindo as novas variáveis de endereço
            cursor = conn.cursor()
            # ... (código de salvamento conforme versões anteriores)
            conn.commit()
            st.success("Salvo com sucesso!")
            time.sleep(1)
            st.rerun()

    # --- ABA DE CONSULTA COM OPÇÃO DE E-MAIL ---
    with tab_cons:
        # Lógica de busca e exibição de detalhes...
        if 'hotel_detalhe' in st.session_state:
            st.markdown("### 📧 Enviar Cotação por E-mail")
            email_destino = st.text_input("E-mail do Cliente")
            if st.button("Enviar Dados do Hotel"):
                if email_destino:
                    corpo = f"<h1>Dados do Hotel</h1><p>O hotel {nome_com} em {cidade} possui tarifas a partir de...</p>"
                    if enviar_email_cotacao(email_destino, f"Cotação - {nome_com}", corpo):
                        st.success("E-mail enviado!")
                else:
                    st.error("Digite um e-mail válido.")

if __name__ == "__main__":
    exibir_pagina_hoteis()