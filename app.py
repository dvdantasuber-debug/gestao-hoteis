import streamlit as st
from database import init_db
from seguranca import login_usuario, logout_usuario

st.set_page_config(page_title="Sistema de Gestão Uniglobe", page_icon="🏢", layout="wide")

def main():
    init_db()

    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("<h2 style='text-align: center;'>🔐 Acesso Restrito</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            with st.form("login_box"):
                u = st.text_input("Utilizador")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar", use_container_width=True):
                    if login_usuario(u, s):
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
    else:
        from clientes import exibir_pagina_clientes
        from hoteis import exibir_pagina_hoteis
        from cotacoes import exibir_pagina_cotacoes
        from usuarios import exibir_usuarios

        with st.sidebar:
            st.title(f"👋 Olá, {st.session_state.usuario_nome}")
            menu = st.radio("Navegação:", ["Página Inicial", "👥 Clientes", "🏨 Hotéis", "💰 Cotações", "🔐 Usuários"])
            if st.button("🚪 Sair"):
                logout_usuario()
                st.rerun()

        if menu == "Página Inicial":
            st.title("🏢 Painel de Controlo")
            st.info("Bem-vindo ao sistema de gestão.")
        elif menu == "👥 Clientes": exibir_pagina_clientes()
        elif menu == "🏨 Hotéis": exibir_pagina_hoteis()
        elif menu == "💰 Cotações": exibir_pagina_cotacoes()
        elif menu == "🔐 Usuários": exibir_usuarios()

if __name__ == "__main__":
    main()