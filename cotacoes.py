import streamlit as st
import pandas as pd
import datetime
import os
import smtplib
from email.message import EmailMessage
from database import init_db
from utils import get_countries, get_states, get_cities
from fpdf import FPDF

# --- CONFIGURAÇÕES VISUAIS UNIGLOBE ---
AZUL_UNIGLOBE_RGB = (25, 45, 95)
AZUL_UNIGLOBE_HEX = "#192d5f"
AZUL_CLARO_HEX = "#E8EDF6"

def gerar_identificador_unico(conn):
    hoje = datetime.date.today().strftime("%Y%m%d")
    cursor = conn.cursor()
    # Sintaxe PostgreSQL usa %s para parâmetros
    cursor.execute("SELECT identificador FROM cotacoes WHERE identificador LIKE %s ORDER BY identificador DESC LIMIT 1", (f"COT-{hoje}-%",))
    ultimo = cursor.fetchone()
    novo_num = int(ultimo[0].split('-')[-1]) + 1 if ultimo else 1
    return f"COT-{hoje}-{novo_num:03d}"

def gerar_pdf_cotacao(cotacao_info, itens_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(*AZUL_UNIGLOBE_RGB)
    pdf.rect(0, 0, 210, 45, 'F')
    if os.path.exists("logo.png"): pdf.image("logo.png", x=10, y=8, h=28)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(110, 18)
    pdf.cell(90, 10, "PROPOSTA DE HOSPEDAGEM", align='R', ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(110); pdf.cell(90, 5, f"ID: {cotacao_info['identificador']}", align='R', ln=True)
    
    pdf.set_xy(10, 55); pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 11); pdf.cell(0, 10, f"Evento: {str(cotacao_info['evento']).upper()}", ln=True)

    w_hotel, w_val, w_qtd, w_sub = 105, 30, 15, 40
    pdf.set_fill_color(*AZUL_UNIGLOBE_RGB); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(w_hotel, 10, "  HOTEL / ACOMODACAO", fill=True)
    pdf.cell(w_val, 10, "DIARIA", align='C', fill=True)
    pdf.cell(w_qtd, 10, "QTD", align='C', fill=True)
    pdf.cell(w_sub, 10, "SUBTOTAL  ", align='R', fill=True, ln=True)

    pdf.set_text_color(30, 30, 30)
    for i, (_, row) in enumerate(itens_df.iterrows()):
        pdf.set_fill_color(232, 237, 246) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        obs = str(row.get('obs', ''))
        tem_obs = obs != "None" and obs.strip() != ""
        h_linha = 16 if tem_obs else 12
        y_atual = pdf.get_y()
        pdf.rect(10, y_atual, 190, h_linha, 'F')
        pdf.set_xy(12, y_atual + 2)
        pdf.set_font("Helvetica", "B", 9); pdf.cell(w_hotel-2, 4, row['Hotel'], ln=True)
        pdf.set_font("Helvetica", "", 8); pdf.set_x(12); pdf.cell(w_hotel-2, 4, row['Quarto'], ln=True)
        if tem_obs:
            pdf.set_font("Helvetica", "I", 7); pdf.set_text_color(100, 100, 100)
            pdf.set_x(12); pdf.cell(w_hotel-2, 4, f"Obs: {obs}", ln=True)
            pdf.set_text_color(30, 30, 30)
        pdf.set_xy(10 + w_hotel, y_atual)
        pdf.cell(w_val, h_linha, f"R$ {row['valor']:,.2f}", align='C')
        pdf.cell(w_qtd, h_linha, str(row['quantidade']), align='C')
        pdf.cell(w_sub, h_linha, f"R$ {row['valor']*row['quantidade']*row.get('diarias', 1):,.2f}  ", align='R', ln=True)
    return bytes(pdf.output())

def enviar_email_html(destinatario, cotacao_id, inf, itens_df):
    try:
        USER = st.secrets["EMAIL_USER"]
        PASS = st.secrets["EMAIL_PASS"]
        HOST = st.secrets["EMAIL_HOST"]
        PORT = int(st.secrets["EMAIL_PORT"])
        
        total_proposta = 0
        linhas_tabela = ""
        for i, (_, row) in enumerate(itens_df.iterrows()):
            cor_fundo = AZUL_CLARO_HEX if i % 2 == 0 else "#FFFFFF"
            sub = row['valor'] * row['quantidade'] * row.get('diarias', 1)
            total_proposta += sub
            linhas_tabela += f"<tr style='background:{cor_fundo};'><td><b>{row['Hotel']}</b></td><td align='center'>R$ {row['valor']:,.2f}</td><td align='center'>{row['quantidade']}</td><td align='right'>R$ {sub:,.2f}</td></tr>"

        corpo = f"<html><body><div style='background:{AZUL_UNIGLOBE_HEX};color:white;padding:20px;'><h2>PROPOSTA {cotacao_id}</h2></div><p>Evento: {inf['evento']}</p><table width='100%'>{linhas_tabela}</table><h3>Total: R$ {total_proposta:,.2f}</h3></body></html>"

        msg = EmailMessage()
        msg['Subject'] = f"Proposta Uniglobe - {cotacao_id}"
        msg['From'] = USER; msg['To'] = destinatario
        msg.add_alternative(corpo, subtype='html')

        with smtplib.SMTP(HOST, PORT) as server:
            server.starttls()
            server.login(USER, PASS)
            server.send_message(msg)
        return True, "E-mail enviado!"
    except Exception as e: return False, str(e)

def exibir_pagina_cotacoes():
    st.title("💰 Gestão de Cotações e Pedidos")
    conn = init_db()
    if not conn: return
    if 'carrinho' not in st.session_state: st.session_state.carrinho = []

    tab1, tab2 = st.tabs(["📝 Nova Cotação", "🔍 Pesquisar e Efetivar Pedidos"])

    with tab1:
        identificador = gerar_identificador_unico(conn)
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            grupos = pd.read_sql_query("SELECT id, nome FROM grupos_economicos ORDER BY nome", conn)
            g_sel = c1.selectbox("Grupo", [""] + grupos['nome'].tolist())
            empresas = [""]
            if g_sel:
                g_id = grupos[grupos['nome'] == g_sel]['id'].values[0]
                empresas += pd.read_sql_query("SELECT nome FROM empresas_clientes WHERE grupo_id=%s", conn, params=(int(g_id),))['nome'].tolist()
            e_sel = c2.selectbox("Empresa", empresas)
            evento = c3.text_input("Evento")
            
            l1, l2, l3 = st.columns(3)
            p_lista = get_countries()
            pais = l1.selectbox("País", p_lista, index=p_lista.index("Brazil") if "Brazil" in p_lista else 0)
            est = l2.selectbox("Estado", get_states(pais), index=0)
            cid = l3.selectbox("Cidade", get_cities(pais, est), index=0)
            
            d1, d2 = st.columns(2)
            checkin = d1.date_input("Check-in", datetime.date.today())
            checkout = d2.date_input("Check-out", datetime.date.today() + datetime.timedelta(days=1))
            diarias = (checkout - checkin).days or 1

        hoteis = pd.read_sql_query("SELECT * FROM hoteis WHERE cidade = %s", conn, params=(cid,))
        for _, h in hoteis.iterrows():
            with st.expander(f"🏨 {h['nome_comercial']}"):
                quartos = pd.read_sql_query("SELECT * FROM acomodacoes WHERE hotel_id = %s", conn, params=(h['id'],))
                for _, q in quartos.iterrows():
                    col1, col2, col3, col4 = st.columns([2,1,1,1])
                    col1.write(f"**{q['tipo']}**"); col2.write(f"R$ {q['valor']:,.2f}")
                    qtd = col3.number_input("Qtd", 1, 100, 1, key=f"q_{q['id']}")
                    if col4.button("Selecionar", key=f"b_{q['id']}", use_container_width=True):
                        st.session_state.carrinho.append({"Hotel_ID": h['id'], "Hotel": h['nome_comercial'], "Quarto": q['tipo'], "valor": q['valor'], "obs": q['obs'], "quantidade": qtd, "diarias": diarias})
                        st.rerun()

        if st.session_state.carrinho:
            st.divider()
            df_c = pd.DataFrame(st.session_state.carrinho)
            st.dataframe(df_c[["Hotel", "Quarto", "valor", "quantidade", "diarias"]], use_container_width=True)
            if st.button("💾 Salvar Cotação", type="primary"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO cotacoes (identificador, grupo, empresa, evento, checkin, checkout, cidade, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id", (identificador, g_sel, e_sel, evento, checkin, checkout, cid, est))
                c_id = cursor.fetchone()[0]
                for item in st.session_state.carrinho:
                    cursor.execute("INSERT INTO cotacao_hoteis (cotacao_id, hotel_id, quarto_tipo, valor, quantidade) VALUES (%s,%s,%s,%s,%s)", (c_id, item['Hotel_ID'], item['Quarto'], item['valor'], item['quantidade']))
                conn.commit(); st.session_state.carrinho = []; st.success("Salvo!"); st.rerun()

    with tab2:
        st.subheader("🔍 Pesquisar e Efetivar")
        busca = st.text_input("Buscar ID (Ex: COT-2026)")
        # ILIKE para busca case-insensitive no PostgreSQL
        df_h = pd.read_sql_query("SELECT * FROM cotacoes WHERE identificador ILIKE %s", conn, params=(f"%{busca}%",))
        if not df_h.empty:
            sel = st.selectbox("Selecione:", df_h['identificador'])
            inf = df_h[df_h['identificador'] == sel].iloc[0]
            itens = pd.read_sql_query("SELECT ch.id, h.nome_comercial as Hotel, ch.quarto_tipo as Quarto, ch.valor, ch.quantidade, ch.pedido, ch.sistema, ac.obs FROM cotacao_hoteis ch JOIN hoteis h ON ch.hotel_id = h.id LEFT JOIN acomodacoes ac ON (h.id = ac.hotel_id AND ch.quarto_tipo = ac.tipo) WHERE ch.cotacao_id = %s", conn, params=(int(inf['id']),))
            
            # Cálculo de diárias para o PDF
            d_i, d_o = pd.to_datetime(inf['checkin']), pd.to_datetime(inf['checkout'])
            itens['diarias'] = (d_o - d_i).days or 1
            
            st.dataframe(itens[["Hotel", "Quarto", "obs", "valor", "quantidade", "pedido", "sistema"]], use_container_width=True)
            
            st.divider()
            st.subheader("📌 Vincular ao Pedido")
            c_f1, c_f2, c_f3 = st.columns([2, 1, 1])
            escolha = c_f1.selectbox("Quarto Escolhido", itens['Hotel'] + " - " + itens['Quarto'])
            sistema, num_ped = c_f2.selectbox("Sistema", ["Reserve", "Argo", "Outro"]), c_f3.text_input("Nº Pedido")
            
            if st.button("✅ Confirmar Vínculo", type="primary"):
                if num_ped:
                    idx = (itens['Hotel'] + " - " + itens['Quarto']).tolist().index(escolha)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE cotacao_hoteis SET pedido=%s, sistema=%s WHERE id=%s", (num_ped, sistema, int(itens.iloc[idx]['id'])))
                    conn.commit(); st.success("Pedido vinculado!"); st.rerun()

            c1, c2 = st.columns(2)
            pdf_bytes = gerar_pdf_cotacao(inf, itens)
            c1.download_button("📄 Baixar PDF", pdf_bytes, f"{sel}.pdf", use_container_width=True)
            dest = c2.text_input("E-mail do Cliente:")
            if c2.button("📧 Enviar por E-mail", use_container_width=True):
                ok, msg = enviar_email_html(dest, sel, inf, itens)
                st.success(msg) if ok else st.error(msg)