import streamlit as st
import pandas as pd
import os, time, sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import init_db
from utils import get_countries, get_states, get_cities

def enviar_email_cotacao(destinatario, assunto, corpo):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["EMAIL_USER"]
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'html'))
        server = smtplib.SMTP(st.secrets["EMAIL_HOST"], st.secrets["EMAIL_PORT"])
        server.starttls()
        server.login(st.secrets["EMAIL_USER"], st.secrets["EMAIL_PASS"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro no e-mail: {e}")
        return False

def exibir_pagina_hoteis():
    st.title("🏨 Gestão de Hotéis & Cotações")
    conn = init_db()
    
    if 'id_edicao' not in st.session_state: st.session_state.id_edicao = None
    if 'form_data' not in st.session_state: st.session_state.form_data = {'acomodacoes': [], 'pix': []}

    tab_cad, tab_cons = st.tabs(["📝 Cadastro e Edição", "🔍 Gerar Cotação e Vínculo"])

    # --- ABA 1: CADASTRO COMPLETO ---
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
                st.session_state.form_data['acomodacoes'] = pd.read_sql_query("SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id=?", conn, params=(int(h_id),)).to_dict('records')
                try:
                    px = pd.read_sql_query("SELECT tipo, chave FROM pix WHERE hotel_id=?", conn, params=(int(h_id),))
                    st.session_state.form_data['pix'] = px.to_dict('records')
                except: st.session_state.form_data['pix'] = []
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

        st.subheader("📍 Localização")
        l1, l2, l3 = st.columns(3)
        p_lista = get_countries()
        pais = l1.selectbox("País", p_lista, index=p_lista.index("Brazil") if "Brazil" in p_lista else 0)
        e_lista = get_states(pais)
        est_idx = e_lista.index("Goiás") if "Goiás" in e_lista else 0
        estado = l2.selectbox("Estado", e_lista, index=e_lista.index(st.session_state.form_data.get('estado')) if st.session_state.form_data.get('estado') in e_lista else est_idx)
        c_lista = get_cities(pais, estado)
        cid_idx = c_lista.index("Goiânia") if "Goiânia" in c_lista else 0
        cidade = l3.selectbox("Cidade", c_lista, index=c_lista.index(st.session_state.form_data.get('cidade')) if st.session_state.form_data.get('cidade') in c_lista else cid_idx)

        with st.expander("Endereço Completo e Coordenadas", expanded=True):
            ed1, ed2, ed3 = st.columns([1.5, 3, 1])
            cep = ed1.text_input("CEP", value=st.session_state.form_data.get('cep', ''))
            logr = ed2.text_input("Logradouro", value=st.session_state.form_data.get('logradouro', ''))
            num = ed3.text_input("Nº", value=st.session_state.form_data.get('numero', ''))
            co1, co2 = st.columns(2)
            lat = co1.text_input("Latitude", value=st.session_state.form_data.get('latitude', ''))
            lon = co2.text_input("Longitude", value=st.session_state.form_data.get('longitude', ''))

        st.subheader("💰 Dados Financeiros (PIX)")
        px1, px2, px3 = st.columns([2, 3, 1])
        t_pix = px1.selectbox("Tipo de Chave", ["CNPJ", "E-mail", "Telefone", "Chave Aleatória"])
        v_pix = px2.text_input("Chave PIX")
        if px3.button("Adicionar PIX"):
            if v_pix:
                st.session_state.form_data['pix'].append({'tipo': t_pix, 'chave': v_pix})
                st.rerun()
        if st.session_state.form_data.get('pix'):
            st.table(pd.DataFrame(st.session_state.form_data['pix']))
            if st.button("Limpar PIX"): st.session_state.form_data['pix'] = []; st.rerun()

        st.subheader("💳 Tarifário")
        with st.expander("Configurar Tarifas", expanded=True):
            a1, a2, a3, a4 = st.columns([2, 1, 2, 0.5])
            tipo_ac = a1.selectbox("Tipo de Quarto", ["Single", "Double", "Triple", "Suíte Luxo", "Standard"])
            valor_ac = a2.text_input("Valor (R$)", placeholder="0,00")
            obs_ac = a3.text_input("Observações")
            if a4.button("➕"):
                if valor_ac:
                    st.session_state.form_data['acomodacoes'].append({'tipo': tipo_ac, 'valor': valor_ac, 'obs': obs_ac})
                    st.rerun()
            if st.session_state.form_data.get('acomodacoes'):
                st.table(pd.DataFrame(st.session_state.form_data['acomodacoes']))
                if st.button("Limpar Tarifas"): st.session_state.form_data['acomodacoes'] = []; st.rerun()

        if st.button("💾 SALVAR HOTEL", use_container_width=True, type="primary"):
            if nome_com:
                cursor = conn.cursor()
                vals = (nome_com, razao, cnpj, cidade, estado, pais, cep, logr, num, lat, lon)
                if st.session_state.id_edicao:
                    cursor.execute("UPDATE hoteis SET nome_comercial=?, razao_social=?, cnpj=?, cidade=?, estado=?, pais=?, cep=?, logradouro=?, numero=?, latitude=?, longitude=? WHERE id=?", vals + (st.session_state.id_edicao,))
                    h_id = st.session_state.id_edicao
                else:
                    cursor.execute("INSERT INTO hoteis (nome_comercial, razao_social, cnpj, cidade, estado, pais, cep, logradouro, numero, latitude, longitude) VALUES (?,?,?,?,?,?,?,?,?,?,?)", vals)
                    h_id = cursor.lastrowid
                
                conn.execute("DELETE FROM acomodacoes WHERE hotel_id=?", (h_id,))
                for ac in st.session_state.form_data['acomodacoes']:
                    v = round(float(str(ac['valor']).replace(',', '.')), 2)
                    conn.execute("INSERT INTO acomodacoes (hotel_id, tipo, valor, obs) VALUES (?,?,?,?)", (h_id, ac['tipo'], v, ac['obs']))
                
                conn.execute("DELETE FROM pix WHERE hotel_id=?", (h_id,))
                for px in st.session_state.form_data['pix']:
                    conn.execute("INSERT INTO pix (hotel_id, tipo, chave) VALUES (?,?,?)", (h_id, px['tipo'], px['chave']))
                
                conn.commit()
                st.success("Hotel Salvo!"); time.sleep(1); st.session_state.id_edicao = None; st.rerun()

    # --- ABA 2: CONSULTA E COTAÇÃO VINCULADA ---
    with tab_cons:
        st.subheader("🔍 Selecione o Hotel para Cotação")
        busca = st.text_input("Filtrar por nome:")
        hoteis = pd.read_sql_query(f"SELECT * FROM hoteis WHERE nome_comercial LIKE '%{busca}%'", conn)
        
        for _, h in hoteis.iterrows():
            with st.container(border=True):
                c_i, c_b = st.columns([4, 1])
                c_i.write(f"### {h['nome_comercial']}\n📍 {h['cidade']} - {h['estado']}")
                if c_b.button("Selecionar", key=f"q_{h['id']}"):
                    st.session_state.hotel_detalhe = h['id']
                    st.rerun()

        if 'hotel_detalhe' in st.session_state:
            h_id_det = int(st.session_state.hotel_detalhe)
            h = pd.read_sql_query("SELECT * FROM hoteis WHERE id=?", conn, params=(h_id_det,)).iloc[0]
            st.divider()
            
            # Cabeçalho da Cotação
            col_v, col_e = st.columns([4, 1])
            if col_v.button("⬅️ Voltar"): st.session_state.pop('hotel_detalhe'); st.rerun()
            if col_e.button("🗑️ EXCLUIR HOTEL", type="secondary"):
                conn.execute("DELETE FROM hoteis WHERE id=?", (h_id_det,)); conn.commit()
                st.success("Removido!"); time.sleep(1); st.session_state.pop('hotel_detalhe'); st.rerun()

            st.subheader(f"📋 Gerar Cotação: {h['nome_comercial']}")
            
            # Dados do Vínculo (Pedido)
            st.info("Preencha os dados do pedido para vincular à cotação enviada.")
            c_sis, c_ped = st.columns(2)
            sistema = c_sis.selectbox("Sistema de Destino", ["Reserve", "Argo", "Outro"])
            pedido_id = c_ped.text_input("ID do Pedido (Ex: 123456)")
            
            # Exibição de Opções de Quarto
            df_ac = pd.read_sql_query("SELECT tipo, valor, obs FROM acomodacoes WHERE hotel_id=?", conn, params=(h_id_det,))
            if not df_ac.empty:
                st.table(df_ac)
                
                # Envio da Cotação
                email_cli = st.text_input("E-mail do Passageiro / Solicitante")
                if st.button("🚀 Enviar Cotação Vinculada"):
                    if email_cli and pedido_id:
                        corpo_html = f"""
                        <h3>Cotação de Hospedagem - Pedido #{pedido_id}</h3>
                        <p><b>Sistema:</b> {sistema}</p>
                        <hr>
                        <p>Olá, seguem as opções para o hotel <b>{h['nome_comercial']}</b>:</p>
                        <table border='1' style='border-collapse: collapse;'>
                            <tr><th>Quarto</th><th>Valor</th><th>Obs</th></tr>
                            {"".join([f"<tr><td>{r['tipo']}</td><td>R$ {r['valor']:,.2f}</td><td>{r['obs']}</td></tr>" for _, r in df_ac.iterrows()])}
                        </table>
                        <p>Para confirmar, basta responder este e-mail informando a opção desejada.</p>
                        """
                        if enviar_email_cotacao(email_cli, f"Cotação Pedido #{pedido_id} - {h['nome_comercial']}", corpo_html):
                            st.success(f"Cotação enviada com sucesso! Vínculo: {sistema} #{pedido_id}")
                    else:
                        st.warning("Informe o ID do Pedido e o E-mail para prosseguir.")
            else:
                st.warning("Este hotel não possui tarifas cadastradas.")