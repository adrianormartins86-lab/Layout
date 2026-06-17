import streamlit as st
import pandas as pd
import numpy as np

# Configuração inicial
st.set_page_config(page_title="Planograma por Categoria", layout="wide", page_icon="🛒")

st.title("🛒 Planograma Inteligente por Categoria")
st.write("Selecione a categoria. Os produtos serão ranqueados pelo maior preço e alocados fisicamente nas réguas.")

# ==========================================
# 1. BANCO DE DADOS (Simulando um ERP)
# ==========================================
# Aqui você pode no futuro conectar com o seu banco SQL ou importar um CSV
if 'df_bd' not in st.session_state:
    st.session_state.df_bd = pd.DataFrame({
        "Categoria": ["Sucos", "Sucos", "Sucos", "Sucos", "Sucos", "Laticínios", "Laticínios"],
        "EAN": ["78901", "78902", "78903", "78904", "78905", "78906", "78907"],
        "Produto": ["Suco Integral Uva 1.5L", "Suco Laranja 1L", "Suco Maçã 1L", "Néctar Pêssego 1L", "Suco Caixinha 200ml", "Leite A", "Queijo B"],
        "Preço (R$)": [22.90, 14.50, 15.00, 7.50, 2.50, 5.00, 45.00], # Usado para ordenação (Cima para Baixo)
        "Vendas (R$)": [8000.0, 5000.0, 3000.0, 6000.0, 2000.0, 15000.0, 3000.0], # Usado para definir o % de Espaço
        "Largura (cm)": [10.0, 8.5, 8.5, 7.0, 5.0, 7.0, 15.0],
        "Cor": ["#5c3a21", "#e67e22", "#e74c3c", "#f1c40f", "#f39c12", "#ecf0f1", "#f1c40f"]
    })

# ==========================================
# 2. BARRA LATERAL E FILTROS
# ==========================================
st.sidebar.header("Configurações do Módulo")

# Filtro de Categoria
categorias_disponiveis = st.session_state.df_bd["Categoria"].unique()
categoria_selecionada = st.sidebar.selectbox("Filtrar Categoria:", categorias_disponiveis)

st.sidebar.markdown("---")
largura_modulo_m = st.sidebar.selectbox("Largura do Módulo (m)", options=[0.8, 1.0, 1.2, 1.33], index=1)
qtd_prateleiras = st.sidebar.number_input("Quantidade de Réguas", min_value=1, max_value=12, value=5)
altura_visual = st.sidebar.slider("Altura do Desenho (pixels)", min_value=400, max_value=1200, value=600, step=50)

# ==========================================
# 3. MOTOR DE CÁLCULO E ALOCAÇÃO
# ==========================================
largura_modulo_cm = largura_modulo_m * 100
espaco_total_modulo_cm = largura_modulo_cm * qtd_prateleiras

# Filtra a categoria e ordena pelo PREÇO (Maior para o Menor)
df_filtrado = st.session_state.df_bd[st.session_state.df_bd["Categoria"] == categoria_selecionada].copy()
df_filtrado = df_filtrado.sort_values(by="Preço (R$)", ascending=False)

total_vendas_cat = df_filtrado["Vendas (R$)"].sum()

if total_vendas_cat > 0:
    # Calcula Share e Frentes
    df_filtrado["Share (%)"] = (df_filtrado["Vendas (R$)"] / total_vendas_cat) * 100
    df_filtrado["Espaço Recomendado (cm)"] = (df_filtrado["Share (%)"] / 100) * espaco_total_modulo_cm
    
    # Arredonda para baixo para ter o número exato de frentes físicas que cabem
    df_filtrado["Frentes"] = np.floor(df_filtrado["Espaço Recomendado (cm)"] / df_filtrado["Largura (cm)"]).astype(int)
    
    # Garante no mínimo 1 frente se o produto tem venda
    df_filtrado["Frentes"] = np.where((df_filtrado["Frentes"] == 0) & (df_filtrado["Vendas (R$)"] > 0), 1, df_filtrado["Frentes"])

    # --- O ALGORITMO DE PRATELEIRAS (Quebra Automática) ---
    # Cria uma lista de dicionários para representar o espaço físico de cada régua
    prateleiras = [{"espaco_livre_cm": largura_modulo_cm, "itens_alocados": []} for _ in range(int(qtd_prateleiras))]
    
    indice_prateleira_atual = 0

    # Pega cada produto (já ordenado do mais caro pro mais barato)
    for idx, row in df_filtrado.iterrows():
        qtd_frentes = row["Frentes"]
        largura_item = row["Largura (cm)"]
        
        # Tenta colocar frente por frente na gôndola
        for _ in range(qtd_frentes):
            if indice_prateleira_atual >= qtd_prateleiras:
                break # Acabou o espaço do módulo inteiro
                
            # Se a frente couber na prateleira atual, coloca ela
            if prateleiras[indice_prateleira_atual]["espaco_livre_cm"] >= largura_item:
                prateleiras[indice_prateleira_atual]["itens_alocados"].append(row)
                prateleiras[indice_prateleira_atual]["espaco_livre_cm"] -= largura_item
            else:
                # Se não couber, pula para a prateleira de baixo
                indice_prateleira_atual += 1
                if indice_prateleira_atual < qtd_prateleiras:
                    if prateleiras[indice_prateleira_atual]["espaco_livre_cm"] >= largura_item:
                        prateleiras[indice_prateleira_atual]["itens_alocados"].append(row)
                        prateleiras[indice_prateleira_atual]["espaco_livre_cm"] -= largura_item

    # ==========================================
    # 4. VISUALIZAÇÃO DOS DADOS E DESENHO
    # ==========================================
    st.subheader(f"📊 Espaço Recomendado - {categoria_selecionada}")
    st.dataframe(
        df_filtrado[["Produto", "Preço (R$)", "Vendas (R$)", "Share (%)", "Frentes"]],
        use_container_width=True, hide_index=True,
        column_config={
            "Share (%)": st.column_config.ProgressColumn("Share Ideal", format="%.1f%%", min_value=0, max_value=100),
        }
    )

    st.markdown("---")
    st.subheader("🎨 Planograma Físico (Ordem de Preço Descrescente)")
    
    altura_prateleira = 100 / qtd_prateleiras
    
    # Base da Gôndola
    html_gondola = f"""
    <div style="
        border: 4px solid #34495e; 
        border-bottom: 12px solid #2c3e50; 
        width: 100%; 
        max-width: 1000px; 
        height: {altura_visual}px;
        display: flex; 
        flex-direction: column; 
        background: #f8f9fa; 
        box-sizing: border-box; 
        margin: 0 auto;
    ">
    """
    
    # Desenha as prateleiras e as frentes reais que foram calculadas no algoritmo
    for i, prat in enumerate(prateleiras):
        border_bottom = "border-bottom: 6px solid #95a5a6;" if i < qtd_prateleiras - 1 else ""
        
        html_gondola += f"""
        <div style="
            {border_bottom}
            display: flex; 
            width: 100%; 
            height: {altura_prateleira}%;
            box-sizing: border-box;
            align-items: flex-end; /* Produtos encostados na base da prateleira */
            padding-left: 2px;
        ">
        """
        
        for item in prat["itens_alocados"]:
            # A largura percentual visual no HTML é baseada na largura do módulo
            width_pct = (item["Largura (cm)"] / largura_modulo_cm) * 100
            cor = item["Cor"]
            nome = item["Produto"].split()[0] # Pega só o primeiro nome pra caber na caixinha
            preco = f"R${item['Preço (R$)']:.2f}"
            
            html_gondola += f"""
            <div style="
                background-color: {cor}; 
                width: {width_pct}%; 
                height: 80%; /* Altura simulada do produto */
                color: white; 
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                font-family: Arial, sans-serif;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid rgba(0,0,0,0.2);
                border-radius: 2px 2px 0 0;
                box-sizing: border-box;
                text-align: center;
                overflow: hidden;
            ">
                <span>{nome}</span>
                <span style="font-size: 9px;">{preco}</span>
            </div>
            """
        html_gondola += "</div>"
    
    html_gondola += "</div>"
    st.components.v1.html(html_gondola, height=altura_visual + 20)

else:
    st.warning("Nenhum dado de venda encontrado para esta categoria.")
