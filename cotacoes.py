import streamlit as st
import pandas as pd
import datetime
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid
from database import init_db
from utils import get_countries, get_states, get_cities
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

# --- CORES E CONFIGURAÇÕES ---
AZUL_UNIGLOBE_RGB = (25, 45, 95)
AZUL_UNIGLOBE_HEX = "#192d5f"
AZUL_CLARO_HEX = "#E8EDF6"

def gerar_identificador_unico(conn):
    hoje = datetime.date.today().strftime("%Y%m%d")
    cursor = conn.cursor()
    cursor.execute("SELECT identificador FROM cotacoes WHERE identificador LIKE ? ORDER BY identificador DESC LIMIT 1", (f"COT-{hoje}-%",))
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
    pdf.set_font("Helvetica", "B", 11); pdf.cell(0, 10, f"Evento: {cotacao_info['evento'].upper()}", ln=True)

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
    USER = os.getenv("EMAIL_USER").strip()
    PASS = "".join(os.getenv("EMAIL_PASS").split()).replace('"', '').replace("'", "")
    HOST = os.getenv("EMAIL_HOST").strip()
    PORT = int(os.getenv("EMAIL_PORT", 587))
    image_cid = make_msgid()

    total_proposta = 0
    linhas_tabela = ""
    for i, (_, row) in enumerate(itens_df.iterrows()):
        cor_fundo = AZUL_CLARO_HEX if i % 2 == 0 else "#FFFFFF"
        sub = row['valor'] * row['quantidade'] * row.get('diarias', 1)
        total_proposta += sub
        linhas_tabela += f"""
        <tr style="background-color: {cor_fundo};">
            <td style="padding: 12px; border-bottom: 1px solid #EEE;">
                <b>{row['Hotel']}</b><br><small>{row['Quarto']}</small>
            </td>
            <td style="text-align: center;">R$ {row['valor']:,.2f}</td>
            <td style="text-align: center;">{row['quantidade']}</td>
            <td style="text-align: right; padding-right: 10px;">R$ {sub:,.2f}</td>
        </tr>"""

    corpo_html = f"""<html><body style="font-family: Arial;"><div style="max-width: 700px; margin: auto; border: 1px solid #ddd;">
        <div style="background: {AZUL_UNIGLOBE_HEX}; color: white; padding: 20px; text-align: center;">
            <img src="cid:{image_cid[1:-1]}" style="max-height: 50px;"><br>
            <h2>PROPOSTA DE HOSPEDAGEM</h2><small>ID: {cotacao_id}</small>
        </div>
        <div style="padding: 20px;">
            <p>Olá, segue a cotação para o evento: <b>{inf['evento']}</b></p>
            <table style="width: 100%; border-collapse: collapse;">
                <thead style="background: {AZUL_UNIGLOBE_HEX}; color: white;">
                    <tr><th style="padding: 10px; text-align: left;">Hotel</th><th>Diária</th><th>Qtd</th><th style="text-align: right;">Subtotal</th></tr>
                </thead>
                <tbody>{linhas_tabela}</tbody>
            </table>
            <h3 style="text-align: right; margin-top: 20px;">Total da Proposta: R$ {total_proposta:,.2f}</h3>
        </div></div></body></html>"""

    try:
        msg = EmailMessage()
        msg['Subject'] = f"Proposta Uniglobe - {cotacao_id}"; msg['From'] = USER; msg['To'] = destinatario
        msg.add_alternative(corpo_html, subtype='html')
        if os.path.exists("logo.png"):
            with open("logo.png", "rb") as img: msg.get_payload()[0].add_related(img.read(), 'image', 'png', cid=image_cid)
        
        # AJUSTE SSL: SMTP + STARTTLS (Porta 587)
        server = smtplib.SMTP(HOST, PORT)
        server.starttls()
        server.login(USER, PASS)
        server.send_message(msg)
        server.quit()
        return True, "E-mail enviado!"
    except Exception as e: return False, str(e)

def exibir_pagina_cotacoes():
    st.title("💰 Gestão de Cotações e Pedidos")
    conn = init_db()
    if 'carrinho' not in st.session_state: st.session_state.carrinho = []

    tab1, tab2 = st.tabs(["📝 Nova Cotação", "🔍 Pesquisar e Efetivar Pedidos"])

    with tab1:
        identificador = gerar_identificador_unico(conn)
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            grupos = pd.read_sql_query("SELECT id, nome FROM grupos_economicos", conn)
            g_sel = c1.selectbox("Grupo", [""] + grupos['nome'].tolist())
            empresas = [""]
            if g_sel:
                g_id = grupos[grupos['nome'] == g_sel]['id'].values[0]
                empresas += pd.read_sql_query("SELECT nome FROM empresas_clientes WHERE grupo_id=?", conn, params=(int(g_id),))['nome'].tolist()
            e_sel = c2.selectbox("Empresa", empresas)
            evento = c3.text_input("Evento")
            
            l1, l2, l3 = st.columns(3)
            pais = l1.selectbox("País", get_countries())
            est = l2.selectbox("Estado", get_states(pais))
            cid = l3.selectbox("Cidade", get_cities(pais, est))
            
            d1, d2 = st.columns(2)
            checkin = d1.date_input("Check-in", datetime.date.today())
            checkout = d2.date_input("Check-out", datetime.date.today() + datetime.timedelta(days=1))
            diarias = (checkout - checkin).days or 1

        hoteis = pd.read_sql_query("SELECT * FROM hoteis WHERE cidade = ?", conn, params=(cid,))
        for _, h in hoteis.iterrows():
            with st.expander(f"🏨 {h['nome_comercial']}"):
                quartos = pd.read_sql_query("SELECT * FROM acomodacoes WHERE hotel_id = ?", conn, params=(h['id'],))
                for _, q in quartos.iterrows():
                    col1, col2, col3, col4 = st.columns([2,1,1,1])
                    col1.write(f"**{q['tipo']}**")
                    col2.write(f"R$ {q['valor']:,.2f}")
                    qtd = col3.number_input("Qtd", 1, 100, 1, key=f"q_{q['id']}")
                    if col4.button("Selecionar", key=f"b_{q['id']}", use_container_width=True):
                        st.session_state.carrinho.append({
                            "Hotel_ID": h['id'], "Hotel": h['nome_comercial'], "Quarto": q['tipo'], 
                            "valor": q['valor'], "obs": q['obs'], "quantidade": qtd, "diarias": diarias
                        })
                        st.rerun()

        if st.session_state.carrinho:
            st.divider()
            st.subheader("🛒 Itens Selecionados")
            df_c = pd.DataFrame(st.session_state.carrinho)
            df_c['Subtotal'] = df_c['valor'] * df_c['quantidade'] * df_c['diarias']
            st.dataframe(df_c[["Hotel", "Quarto", "valor", "quantidade", "diarias", "Subtotal"]].style.format({'valor': 'R$ {:,.2f}', 'Subtotal': 'R$ {:,.2f}'})
                         .set_properties(**{'background-color': AZUL_CLARO_HEX}, subset=pd.IndexSlice[df_c.index[::2], :]), use_container_width=True)
            
            if st.button("💾 Salvar Cotação", type="primary"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO cotacoes (identificador, grupo, empresa, evento, checkin, checkout, cidade, estado) VALUES (?,?,?,?,?,?,?,?)",
                             (identificador, g_sel, e_sel, evento, str(checkin), str(checkout), cid, est))
                c_id = cursor.lastrowid
                for item in st.session_state.carrinho:
                    cursor.execute("INSERT INTO cotacao_hoteis (cotacao_id, hotel_id, quarto_tipo, valor, quantidade) VALUES (?,?,?,?,?)",
                                 (c_id, item['Hotel_ID'], item['Quarto'], item['valor'], item['quantidade']))
                conn.commit(); st.session_state.carrinho = []; st.success("Salvo!"); st.rerun()

    with tab2:
        st.subheader("🔍 Pesquisar e Enviar")
        busca = st.text_input("Buscar ID")
        df_h = pd.read_sql_query("SELECT * FROM cotacoes WHERE identificador LIKE ?", conn, params=(f"%{busca}%",))
        if not df_h.empty:
            sel = st.selectbox("Selecione:", df_h['identificador'])
            inf = df_h[df_h['identificador'] == sel].iloc[0]
            itens = pd.read_sql_query("""
                SELECT ch.id, h.nome_comercial as Hotel, ch.quarto_tipo as Quarto, ch.valor, ch.quantidade, ch.pedido, ch.sistema, ac.obs 
                FROM cotacao_hoteis ch 
                JOIN hoteis h ON ch.hotel_id = h.id 
                LEFT JOIN acomodacoes ac ON h.id = ac.hotel_id AND ch.quarto_tipo = ac.tipo 
                WHERE ch.cotacao_id = ?""", conn, params=(int(inf['id']),))
            
            d_i, d_o = datetime.datetime.strptime(inf['checkin'], '%Y-%m-%d'), datetime.datetime.strptime(inf['checkout'], '%Y-%m-%d')
            itens['diarias'] = (d_o - d_i).days or 1
            
            st.dataframe(itens[["Hotel", "Quarto", "obs", "valor", "quantidade", "pedido", "sistema"]].style.set_properties(**{'background-color': AZUL_CLARO_HEX}, subset=pd.IndexSlice[itens.index[::2], :]), use_container_width=True)
            
            emp_info = pd.read_sql_query("SELECT email FROM empresas_clientes WHERE nome = ?", conn, params=(inf['empresa'],))
            mail_sugerido = emp_info['email'].iloc[0] if not emp_info.empty else ""
            
            c1, c2 = st.columns(2)
            pdf_bytes = gerar_pdf_cotacao(inf, itens)
            c1.download_button("📄 Baixar PDF", pdf_bytes, f"{sel}.pdf", use_container_width=True)
            dest = c2.text_input("E-mail:", value=mail_sugerido)
            if c2.button("📧 Enviar por E-mail", type="primary", use_container_width=True):
                ok, msg = enviar_email_html(dest, sel, inf, itens)
                st.success(msg) if ok else st.error(msg)