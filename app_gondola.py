import streamlit as st
import pandas as pd
import numpy as np

# Configuração inicial da página
st.set_page_config(page_title="Gerador de Planograma 2.0", layout="wide", page_icon="🛒")

st.title("🛒 Gerenciador de Categorias & Planograma")
st.write("Insira os dados físicos do módulo e dos produtos. O sistema calculará o espaço ideal baseado nas vendas.")

# ==========================================
# 1. BARRA LATERAL (Configurações Físicas do Módulo)
# ==========================================
st.sidebar.header("1. Estrutura do Módulo")

# Selectbox para larguras padrões de mercado
largura_modulo_m = st.sidebar.selectbox(
    "Largura do Módulo (Metros)", 
    options=[0.8, 1.0, 1.2, 1.33], 
    index=1 # Default 1.0m
)

# Profundidade da prateleira (útil para cálculos futuros de estoque/profundidade)
profundidade_modulo_cm = st.sidebar.number_input("Profundidade da Régua (cm)", min_value=20, max_value=100, value=50, step=5)

# Quantidade de réguas no módulo
qtd_prateleiras = st.sidebar.number_input("Quantidade de Réguas", min_value=1, max_value=12, value=5)

st.sidebar.markdown("---")
st.sidebar.header("Ajuste Visual")
altura_visual = st.sidebar.slider("Altura do Desenho (pixels)", min_value=400, max_value=1000, value=500, step=50)

# ==========================================
# 2. BANCO DE PRODUTOS E VENDAS
# ==========================================
st.subheader("2. Banco de Produtos, Dimensões e Vendas")

# Inicializa os dados padrão na primeira vez que o app roda
if 'df_produtos' not in st.session_state:
    st.session_state.df_produtos = pd.DataFrame({
        "EAN": ["7891000001", "7891000002", "7891000003"],
        "Produto/Marca": ["Leite Integral 1L", "Leite Desnatado 1L", "Bebida Láctea 1L"],
        "Largura (cm)": [7.0, 7.0, 6.5],
        "Altura (cm)": [16.0, 16.0, 15.0],
        "Profundidade (cm)": [7.0, 7.0, 6.5],
        "Vendas (R$)": [15000.0, 5000.0, 2500.0],
        "Cor": ["#e63946", "#1d3557", "#2a9d8f"]
    })

st.info("💡 Edite a tabela abaixo. O **Share Ideal** e a quantidade de **Frentes** serão calculados automaticamente!")

# Tabela editável para o usuário
df_editado = st.data_editor(
    st.session_state.df_produtos,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "EAN": st.column_config.TextColumn("Cód. Barras", required=True),
        "Produto/Marca": st.column_config.TextColumn("Nome do Produto", required=True),
        "Largura (cm)": st.column_config.NumberColumn("Largura (cm)", min_value=0.1, format="%.1f"),
        "Altura (cm)": st.column_config.NumberColumn("Altura (cm)", min_value=0.1, format="%.1f"),
        "Profundidade (cm)": st.column_config.NumberColumn("Profundidade (cm)", min_value=0.1, format="%.1f"),
        "Vendas (R$)": st.column_config.NumberColumn("Vendas / Demanda", min_value=0.0, format="R$ %.2f"),
        "Cor": st.column_config.TextColumn("Cor Visual (Hex)", required=True)
    }
)

# Salva o estado atualizado
st.session_state.df_produtos = df_editado

# ==========================================
# 3. MOTOR DE CÁLCULO (Share e Frentes Físicas)
# ==========================================
# Converte a largura do módulo para centímetros
largura_modulo_cm = largura_modulo_m * 100

# Calcula o Total de Vendas
total_vendas = df_editado["Vendas (R$)"].sum()

# Cria um dataframe de resultados baseado nos cálculos
df_resultados = df_editado.copy()

if total_vendas > 0:
    # 1. Calcula o Share de Vendas (%)
    df_resultados["Share (%)"] = (df_resultados["Vendas (R$)"] / total_vendas) * 100
    
    # 2. Calcula o espaço linear que esse produto merece na régua (em cm)
    df_resultados["Espaço Linear Recomendado (cm)"] = largura_modulo_cm * (df_resultados["Share (%)"] / 100)
    
    # 3. Calcula quantas frentes (faces) físicas cabem nesse espaço
    # Se a largura do produto for > 0, divide o espaço recomendado pela largura do produto
    df_resultados["Frentes (Calculadas)"] = np.where(
        df_resultados["Largura (cm)"] > 0,
        df_resultados["Espaço Linear Recomendado (cm)"] / df_resultados["Largura (cm)"],
        0
    )
    
    # Arredonda para 1 casa decimal para visualização
    df_resultados["Frentes (Calculadas)"] = df_resultados["Frentes (Calculadas)"].round(1)

else:
    df_resultados["Share (%)"] = 0
    df_resultados["Espaço Linear Recomendado (cm)"] = 0
    df_resultados["Frentes (Calculadas)"] = 0

# Exibe o resumo dos cálculos em um mini-dashboard
st.markdown("---")
st.subheader("📊 Resultados do Cálculo de Espaço")

col1, col2, col3 = st.columns(3)
col1.metric("Largura do Módulo", f"{largura_modulo_cm} cm")
col2.metric("Total de Vendas", f"R$ {total_vendas:,.2f}")
col3.metric("Espaço Linear Total", f"{largura_modulo_cm * qtd_prateleiras} cm")

# Mostra apenas as colunas de resultado
st.dataframe(
    df_resultados[["Produto/Marca", "Vendas (R$)", "Share (%)", "Espaço Linear Recomendado (cm)", "Frentes (Calculadas)"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Share (%)": st.column_config.ProgressColumn("Share Ideal", format="%.1f%%", min_value=0, max_value=100),
        "Frentes (Calculadas)": st.column_config.NumberColumn("Frentes Sugeridas", format="%.1f")
    }
)


# ==========================================
# 4. MOTOR DE DESENHO (Visualização Visual)
# ==========================================
st.markdown("---")
st.subheader("🎨 Visualização do Planograma")

if total_vendas == 0:
    st.warning("⚠️ Adicione vendas maiores que 0 aos produtos para gerar o planograma.")
else:
    # A altura de cada prateleira é dividida igualmente
    altura_prateleira = 100 / qtd_prateleiras
    
    # Inicia a construção do HTML/CSS da Gôndola
    html_gondola = f"""
    <div style="
        border: 5px solid #2c3e50; 
        border-bottom: 12px solid #2c3e50; 
        width: 100%; 
        max-width: 1000px; 
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
    
    # Loop para desenhar cada prateleira (Blocagem Vertical)
    for i in range(int(qtd_prateleiras)):
        # Adiciona a borda inferior para simular a prateleira
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
        
        # Desenha os produtos com base no Share Calculado
        for index, row in df_resultados.iterrows():
            share_atual = row["Share (%)"]
            frentes = row["Frentes (Calculadas)"]
            
            if pd.notna(share_atual) and share_atual > 0:
                width_pct = share_atual
                cor = row['Cor'] if pd.notna(row['Cor']) else "#cccccc"
                nome = row['Produto/Marca'] if pd.notna(row['Produto/Marca']) else "Item"
                
                html_gondola += f"""
                <div style="
                    display: flex; 
                    flex-direction: column;
                    align-items: center; 
                    justify-content: center; 
                    background-color: {cor}; 
                    width: {width_pct}%; 
                    color: white; 
                    font-weight: bold; 
                    font-size: 14px;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    text-shadow: 1px 1px 3px rgba(0,0,0,0.8); 
                    overflow: hidden; 
                    white-space: nowrap; 
                    box-sizing: border-box;
                    border-right: 1px solid rgba(255,255,255,0.3);
                    box-shadow: inset 0 -10px 10px rgba(0,0,0,0.1);
                ">
                    <span>{nome}</span>
                    <span style="font-size: 12px; font-weight: normal; margin-top: 4px;">{frentes} Frentes</span>
                </div>
                """
        # Fecha a div da prateleira
        html_gondola += "</div>" 
        
    # Fecha a div da gôndola inteira
    html_gondola += "</div>" 
    
    # Renderiza o HTML dentro do Streamlit
    st.components.v1.html(html_gondola, height=altura_visual + 20)
