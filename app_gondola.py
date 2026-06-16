import streamlit as st
import pandas as pd

# Configuração inicial da página
st.set_page_config(page_title="Gerador de Planograma", layout="wide")

st.title("🛒 Gerenciador de Share de Gôndola")
st.write("Ajuste as metragens na barra lateral e edite a tabela de produtos para visualizar a melhor exposição.")

# ==========================================
# 1. BARRA LATERAL (Inputs de Metragem)
# ==========================================
st.sidebar.header("Configurações do Módulo")

# Sliders e Inputs para as dimensões
altura_visual = st.sidebar.slider("Altura Visual da Gôndola (pixels)", min_value=400, max_value=1000, value=600, step=50)
qtd_prateleiras = st.sidebar.number_input("Quantidade de Réguas (Prateleiras)", min_value=1, max_value=10, value=5)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Dica:** O sistema ajusta automaticamente o tamanho dos blocos se a soma das porcentagens passar ou faltar para 100%.")

# ==========================================
# 2. ÁREA PRINCIPAL (Tabela de Produtos)
# ==========================================
st.subheader("Itens e Share (%)")

# Inicializa os dados padrão na primeira vez que o app roda
if 'df_produtos' not in st.session_state:
    st.session_state.df_produtos = pd.DataFrame({
        "Marca": ["Marca A", "Marca B", "Marca C"],
        "Share (%)": [40.0, 35.0, 25.0],
        "Cor": ["#e63946", "#1d3557", "#2a9d8f"] # Cores em Hexadecimal
    })

# O st.data_editor é a "mágica" aqui. Ele permite ao usuário adicionar/remover itens na interface.
df_editado = st.data_editor(
    st.session_state.df_produtos,
    num_rows="dynamic", # Permite adicionar e excluir linhas
    use_container_width=True,
    column_config={
        "Marca": st.column_config.TextColumn("Nome do Produto/Marca", required=True),
        "Share (%)": st.column_config.NumberColumn("Importância (%)", min_value=0.0, max_value=100.0, format="%.1f"),
        "Cor": st.column_config.TextColumn("Cor (Código Hex)", required=True)
    }
)

# Salva o estado atualizado
st.session_state.df_produtos = df_editado

# ==========================================
# 3. MOTOR DE DESENHO (Visualização)
# ==========================================
st.markdown("---")
st.subheader("Visualização do Planograma (Blocagem Vertical)")

# Calcula o total para garantir a proporção correta
total_share = df_editado["Share (%)"].sum()

if total_share == 0:
    st.warning("⚠️ Adicione pelo menos um produto com Share maior que 0 para gerar o desenho.")
else:
    # A altura de cada prateleira é dividida igualmente
    altura_prateleira = 100 / qtd_prateleiras
    
    # Inicia a construção do HTML/CSS da Gôndola
    html_gondola = f"""
    <div style="
        border: 5px solid #2c3e50; 
        border-bottom: 12px solid #2c3e50; 
        width: 100%; 
        max-width: 900px; 
        height: {altura_visual}px;
        display: flex; 
        flex-direction: column; 
        background: #ecf0f1; 
        box-sizing: border-box; 
        box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
        margin: 0 auto;
        border-radius: 4px;
    ">
    """
    
    # Loop para desenhar cada prateleira
    for i in range(int(qtd_prateleiras)):
        # Adiciona a borda inferior para simular a prateleira (exceto na última, que é o chão da gôndola)
        border_bottom = "border-bottom: 8px solid #7f8c8d;" if i < int(qtd_prateleiras) - 1 else ""
        
        html_gondola += f"""
        <div style="
            {border_bottom}
            display: flex; 
            width: 100%; 
            height: {altura_prateleira}%;
            box-sizing: border-box;
        ">
        """
        
        # Loop para colocar os produtos lado a lado dentro da prateleira atual
        for index, row in df_editado.iterrows():
            share_atual = row["Share (%)"]
            if pd.notna(share_atual) and share_atual > 0:
                # Calcula a largura proporcional exata
                width_pct = (share_atual / total_share) * 100
                cor = row['Cor'] if pd.notna(row['Cor']) else "#cccccc"
                nome = row['Marca'] if pd.notna(row['Marca']) else "Item"
                
                html_gondola += f"""
                <div style="
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    background-color: {cor}; 
                    width: {width_pct}%; 
                    color: white; 
                    font-weight: bold; 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    text-shadow: 1px 1px 3px rgba(0,0,0,0.8); 
                    overflow: hidden; 
                    white-space: nowrap; 
                    box-sizing: border-box;
                    border-right: 1px solid rgba(255,255,255,0.3);
                    box-shadow: inset 0 -10px 10px rgba(0,0,0,0.1);
                ">
                    {nome} ({width_pct:.1f}%)
                </div>
                """
        # Fecha a div da prateleira
        html_gondola += "</div>" 
        
    # Fecha a div da gôndola inteira
    html_gondola += "</div>" 
    
    # Renderiza o HTML dentro do Streamlit
    st.components.v1.html(html_gondola, height=altura_visual + 20)
