import streamlit as st
from streamlit_option_menu import option_menu

# Importe as funções de cada página
from interfaces.segmentacao import dashboard_segmentacao
from interfaces.recompra import dashboard_recompra
from interfaces.recomendacao import dashboard_recomendacoes

# Configurações da página (deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title='Dashboard ClickBus',
    page_icon='images/logo-clickbus.ico', # Verifique se o caminho da imagem está correto
    layout='wide'
)

# --- AQUI ESTÁ A CORREÇÃO ---
# O código que cria o menu precisa estar dentro do "with st.sidebar"
with st.sidebar: 
    st.image('images/logo-clickbus-sem-fundo.png') # Verifique se o caminho da imagem está correto
    
    # Esta linha CRIA a variável 'menu' com base na escolha do usuário
    menu = option_menu(
        'Navegação', 
        options=['Segmentação', 'Recompra', 'Recomendações', 'AI Insights'],
        icons=['people-fill', 'cart-check-fill', 'bus-front', 'robot'],
        menu_icon='compass-fill',
        default_index=0,
        styles={
            "nav-link-selected": {
                "background-color": "#a528fe",
                "color": "white",
                "border-radius": "10px"
            },
        }
    )

# --- FIM DA CORREÇÃO ---

# Mudando de página conforme a seleção do menu
if menu == 'Segmentação':
    dashboard_segmentacao()

if menu == 'Recompra':
    dashboard_recompra()

if menu == 'Recomendações':
    dashboard_recomendacoes()

if menu == 'AI Insights':
    st.title("AI Insights")
    st.info("Esta página está em desenvolvimento.")