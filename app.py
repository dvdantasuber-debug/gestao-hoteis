import streamlit as st
from database import init_db
from seguranca import login_usuario, logout_usuario

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Sistema de Gestão de Eventos",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Inicializa o Banco e Tabelas
    init_db()

    # Controle de Sessão
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        # --- TELA DE LOGIN ---
        st.markdown("<br><h2 style='text-align: center;'>🔐 Acesso ao Sistema</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            with st.form("login_box"):
                u = st.text_input("Utilizador")
                s = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar", use_container_width=True):
                    if login_usuario(u, s):
                        st.rerun()
                    else:
                        st.error("Utilizador ou senha incorretos.")
    else:
        # --- MENU PRINCIPAL (APÓS LOGIN) ---
        # Importação dos módulos funcionais
        try:
            from clientes import exibir_pagina_clientes
            from hoteis import exibir_pagina_hoteis
            from cotacoes import exibir_pagina_cotacoes
            from usuarios import exibir_usuarios
        except ImportError as e:
            st.error(f"Erro ao carregar ficheiros: {e}")

        with st.sidebar:
            st.title(f"👋 Olá, {st.session_state.usuario_nome}")
            st.caption(f"Nível: {st.session_state.usuario_nivel}")
            st.divider()
            
            menu = st.radio(
                "Navegação:",
                ["Página Inicial", "👥 Clientes", "🏨 Hotéis", "💰 Cotações", "🔐 Usuários"]
            )
            
            st.divider()
            if st.button("🚪 Sair", use_container_width=True):
                logout_usuario()
                st.rerun()

        # Roteamento
        if menu == "Página Inicial":
            st.title("🏢 Painel de Controlo")
            st.write("Bem-vindo ao sistema de gestão Uniglobe.")
            st.info("Selecione uma opção no menu lateral para começar.")
        elif menu == "👥 Clientes":
            exibir_pagina_clientes()
        elif menu == "🏨 Hotéis":
            exibir_pagina_hoteis()
        elif menu == "💰 Cotações":
            exibir_pagina_cotacoes()
        elif menu == "🔐 Usuários":
            exibir_usuarios()

if __name__ == "__main__":
    main()