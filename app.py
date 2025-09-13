import streamlit as st
from streamlit_option_menu import option_menu

# Importe as funções de cada página
from interfaces.segmentacao import dashboard_segmentacao
from interfaces.recompra import dashboard_recompra
from interfaces.recomendacao import dashboard_recomendacoes

# Configurações da página
st.set_page_config(
    page_title='Dashboard ClickBus',
    page_icon='images/logo-clickbus.ico',
    layout='wide'
)

# O código que cria o menu precisa estar dentro do "with st.sidebar"
with st.sidebar: 
    st.image('images/logo-clickbus-sem-fundo.png')
    
    # Esta linha CRIA a variável 'menu' com base na escolha do usuário
    menu = option_menu(
        'Navegação', 
        options=['Segmentação', 'Recompra', 'Recomendações'],
        icons=['people-fill', 'cart-check-fill', 'bus-front'],
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

# Mudando de página conforme a seleção do menu
if menu == 'Segmentação':
    dashboard_segmentacao()

if menu == 'Recompra':
    dashboard_recompra()

if menu == 'Recomendações':
    dashboard_recomendacoes()