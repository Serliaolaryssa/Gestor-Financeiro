import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px



st.set_page_config(page_title="Gestor Financeiro", layout="wide")

# ==========================================
# 🔒 SISTEMA DE LOGIN (SOMENTE VOCÊ ACESSA)
# ==========================================
SENHA_SECRETA = "Lucas@0929" # <--- Mude isso para a senha que você quiser!

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.markdown("<h1 style='text-align: center;'>🔒 Acesso Restrito</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        senha_digitada = st.text_input("Digite sua senha para acessar seu Gestor Financeiro:", type="password")
        if st.button("Entrar", use_container_width=True):
            if senha_digitada == SENHA_SECRETA:
                st.session_state["logado"] = True
                st.rerun() # Recarrega a página para mostrar o app
            else:
                st.error("❌ Senha incorreta!")
    
    # O st.stop() é a mágica: ele proíbe que o resto do código abaixo dele seja lido 
    # até que a senha esteja certa.
    st.stop()

DATA_FILE = 'dados_financeiros.json'

def carregar_dados():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_dados(dados):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def formata_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.set_page_config(page_title="Gestor Financeiro", layout="wide")

st.markdown("""
<link rel="stylesheet" type="text/css" href="https://unpkg.com/@phosphor-icons/web@2.0.3/src/regular/style.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"], 
    [data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .card-list-obs { font-size: 0.85rem; color: #888; margin-top: 4px; }
    .card-list-alert { font-size: 0.85rem; color: #e74c3c; margin-top: 4px; font-weight: bold; }
    .ph { font-size: 1.2rem; vertical-align: middle; margin-right: 8px; }
</style>
""", unsafe_allow_html=True)

db = carregar_dados()

st.sidebar.title("🗓️ Seletor de Mês")
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
ano_atual = st.sidebar.number_input("Ano", min_value=2020, max_value=2100, value=2024, step=1)
mes_nome = st.sidebar.selectbox("Mês", meses, index=0)
mes_selecionado = f"{mes_nome}-{ano_atual}"

if mes_selecionado not in db:
    db[mes_selecionado] = {
        "renda_fixa": [], "cartoes": [], "despesas_variaveis": [],
        "parcelamentos": [], "investimentos": [], "limites_cartoes": {}
    }

if "limites_cartoes" not in db[mes_selecionado]:
    db[mes_selecionado]["limites_cartoes"] = {}

mes_data = db[mes_selecionado]

def calcular_totais():
    renda = sum(item['valor'] for item in mes_data['renda_fixa'])
    desp_cartoes = sum(item['valor'] for item in mes_data['cartoes'])
    desp_variaveis = sum(item['valor'] for item in mes_data['despesas_variaveis'])
    desp_parcelamentos = sum(item['valor'] for item in mes_data['parcelamentos'])
    desp_investimentos = sum(item['valor'] for item in mes_data['investimentos'])
    total_despesas = desp_cartoes + desp_variaveis + desp_parcelamentos + desp_investimentos
    saldo = renda - total_despesas
    return renda, desp_cartoes, desp_variaveis, desp_parcelamentos, desp_investimentos, total_despesas, saldo

renda, desp_cartoes, desp_variaveis, desp_parcelamentos, desp_investimentos, total_despesas, saldo = calcular_totais()

st.sidebar.markdown("---")
if renda > 0:
    if saldo < 0:
        st.sidebar.error("🚨 ALERTA CRÍTICO: Seu saldo está negativo!")
    elif saldo == 0:
        st.sidebar.warning("🚨 ALERTA: Seu saldo zerou!")
    elif saldo <= (renda * 0.15):
        st.sidebar.warning(f"⚠️ AVISO: Saldo perto de zero! Restam apenas {formata_moeda(saldo)}.")
else:
    st.sidebar.info("Adicione uma renda para ativar os alertas de saldo.")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Remover Mês Atual", use_container_width=True):
    if mes_selecionado in db:
        del db[mes_selecionado]
        salvar_dados(db)
        st.rerun()

def renderizar_lista(titulo, chave_json, icone):
    st.markdown(f"### <i class='ph {icone}'></i> {titulo}", unsafe_allow_html=True)
    lista = mes_data[chave_json]
    
    if not lista:
        st.info("Nenhum registro adicionado.")
        return

    for i, item in enumerate(lista):
        col1, col2 = st.columns([4, 1])
        with col1:
            desc = item['descricao']
            val = formata_moeda(item['valor'])
            st.markdown(f"**{desc}** — {val}")
            
            if item.get('importante'):
                st.markdown("<div class='card-list-alert'>⚠️ ATENÇÃO: Despesa Importante/Fixa!</div>", unsafe_allow_html=True)
            
            if chave_json == "cartoes" and 'cartao' in item:
                st.markdown(f"<div class='card-list-obs'>Cartão: {item['cartao']}</div>", unsafe_allow_html=True)
                
            if item.get('observacao'):
                st.markdown(f"<div class='card-list-obs'>Obs: {item['observacao']}</div>", unsafe_allow_html=True)

            if chave_json == "parcelamentos" and 'total_parcelas' in item:
                st.markdown("<div class='card-list-obs'>Progresso de Pagamento:</div>", unsafe_allow_html=True)
                total_p = item['total_parcelas']
                atual_p = item.get('parcela_atual', 0)
                
                cols_cb = st.columns(min(total_p, 12))
                nova_parcela_atual = atual_p
                for p_index in range(total_p):
                    col_idx = p_index % 12
                    num_p = p_index + 1
                    is_checked = p_index < atual_p
                    cb = cols_cb[col_idx].checkbox(f"{num_p}/{total_p}", value=is_checked, key=f"cb_{mes_selecionado}_{i}_{num_p}")
                    if cb and not is_checked:
                        nova_parcela_atual = num_p
                    elif not cb and is_checked and num_p == atual_p:
                        nova_parcela_atual = num_p - 1

                if nova_parcela_atual != atual_p:
                    mes_data[chave_json][i]['parcela_atual'] = nova_parcela_atual
                    salvar_dados(db)
                    st.rerun()
        
        with col2:
            if st.button("Remover", key=f"del_{chave_json}_{i}", use_container_width=True):
                mes_data[chave_json].pop(i)
                salvar_dados(db)
                st.rerun()
        st.markdown("<hr style='margin: 8px 0; border-color: rgba(128,128,128,0.2);'>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Dashboard", "💵 Renda", "💳 Cartões & Limites", "💸 Gastos Variáveis", "📦 Parcelamentos", "📈 Investimentos"])

with tabs[0]:
    col1, col2, col3 = st.columns(3)
    col1.metric("Renda Total", formata_moeda(renda))
    col2.metric("Despesas Totais", formata_moeda(total_despesas))
    col3.metric("Saldo do Mês", formata_moeda(saldo))
    
    st.markdown("---")
    
    if total_despesas > 0 or renda > 0:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("### Distribuição de Despesas")
            if total_despesas > 0:
                df_desp = pd.DataFrame({
                    "Categoria": ["Cartões", "Variáveis", "Parcelamentos", "Investimentos"],
                    "Valor": [desp_cartoes, desp_variaveis, desp_parcelamentos, desp_investimentos]
                })
                df_desp = df_desp[df_desp["Valor"] > 0]
                fig = px.pie(df_desp, values='Valor', names='Categoria', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhuma despesa para exibir no gráfico.")
            
        with col_graf2:
            st.markdown("### Receitas vs Despesas")
            if renda > 0 or total_despesas > 0:
                df_balanco = pd.DataFrame({
                    "Categoria": ["Renda Total", "Despesas Totais"],
                    "Valor": [renda, total_despesas]
                })
                fig2 = px.pie(df_balanco, values='Valor', names='Categoria', hole=0.4, color_discrete_sequence=['#2ecc71', '#e74c3c'])
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Adicione rendas ou despesas para visualizar os gráficos de pizza.")

with tabs[1]:
    with st.form("form_renda", clear_on_submit=True):
        st.subheader("Adicionar Renda")
        desc = st.text_input("Descrição (Ex: Salário)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        obs = st.text_input("Observação (Opcional)")
        if st.form_submit_button("Adicionar"):
            if desc and valor > 0:
                mes_data['renda_fixa'].append({"descricao": desc, "valor": valor, "observacao": obs})
                salvar_dados(db)
                st.rerun()
    renderizar_lista("Listagem de Rendas", "renda_fixa", "ph-wallet")

with tabs[2]:
    st.subheader("Configurar Limite de Cartão")
    col_c1, col_c2, col_c3 = st.columns([2, 2, 1])
    nome_cartao_limite = col_c1.text_input("Nome do Cartão (Ex: Santander)")
    valor_limite = col_c2.number_input("Limite Total (R$)", min_value=0.0, format="%.2f")
    if col_c3.button("Salvar Limite", use_container_width=True):
        if nome_cartao_limite:
            mes_data["limites_cartoes"][nome_cartao_limite] = valor_limite
            salvar_dados(db)
            st.rerun()

    if mes_data["limites_cartoes"]:
        st.markdown("### Situação dos Limites")
        cols_limites = st.columns(len(mes_data["limites_cartoes"]))
        for idx, (c_nome, c_limite) in enumerate(mes_data["limites_cartoes"].items()):
            gastos_cartao = sum(item['valor'] for item in mes_data['cartoes'] if item.get('cartao') == c_nome)
            limite_disp = c_limite - gastos_cartao
            with cols_limites[idx % len(cols_limites)]:
                st.metric(f"💳 {c_nome}", formata_moeda(limite_disp), f"Gasto: {formata_moeda(gastos_cartao)} / Limite: {formata_moeda(c_limite)}")

    st.markdown("---")
    with st.form("form_cartao", clear_on_submit=True):
        st.subheader("Adicionar Gasto no Cartão")
        cartoes_disponiveis = list(mes_data["limites_cartoes"].keys())
        if cartoes_disponiveis:
            cartao_sel = st.selectbox("Selecione o Cartão", cartoes_disponiveis)
        else:
            cartao_sel = st.text_input("Nome do Cartão")
        desc = st.text_input("Com o que gastei? (Ex: Comida, Mercado)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        obs = st.text_input("Observação (Opcional)")
        importante = st.checkbox("⚠️ Marcar como despesa importante")
        if st.form_submit_button("Adicionar Gasto"):
            if desc and valor > 0 and cartao_sel:
                mes_data['cartoes'].append({"descricao": desc, "valor": valor, "cartao": cartao_sel, "observacao": obs, "importante": importante})
                salvar_dados(db)
                st.rerun()
    renderizar_lista("Listagem de Gastos no Cartão", "cartoes", "ph-credit-card")

with tabs[3]:
    with st.form("form_variaveis", clear_on_submit=True):
        st.subheader("Adicionar Gasto Variável")
        desc = st.text_input("Descrição (Ex: Feira, Farmácia)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        obs = st.text_input("Observação (Opcional)")
        importante = st.checkbox("⚠️ Marcar como despesa importante")
        if st.form_submit_button("Adicionar"):
            if desc and valor > 0:
                mes_data['despesas_variaveis'].append({"descricao": desc, "valor": valor, "observacao": obs, "importante": importante})
                salvar_dados(db)
                st.rerun()
    renderizar_lista("Listagem de Gastos Variáveis", "despesas_variaveis", "ph-receipt")

with tabs[4]:
    with st.form("form_parcelamento", clear_on_submit=True):
        st.subheader("Adicionar Parcelamento")
        desc = st.text_input("Descrição do Item (Ex: Geladeira)")
        valor_parcela = st.number_input("Valor da Parcela (R$)", min_value=0.0, format="%.2f")
        total_p = st.number_input("Total de Parcelas", min_value=1, max_value=60, value=12, step=1)
        parcela_atual = st.number_input("Parcelas Já Pagas", min_value=0, max_value=int(total_p), value=0, step=1)
        obs = st.text_input("Observação (Opcional)")
        importante = st.checkbox("⚠️ Marcar como despesa importante")
        if st.form_submit_button("Adicionar Parcelamento"):
            if desc and valor_parcela > 0:
                mes_data['parcelamentos'].append({"descricao": desc, "valor": valor_parcela, "total_parcelas": int(total_p), "parcela_atual": int(parcela_atual), "observacao": obs, "importante": importante})
                salvar_dados(db)
                st.rerun()
    renderizar_lista("Listagem de Parcelamentos", "parcelamentos", "ph-calendar-check")

with tabs[5]:
    with st.form("form_investimento", clear_on_submit=True):
        st.subheader("Adicionar Investimento")
        desc = st.text_input("Descrição (Ex: Tesouro Direto)")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        obs = st.text_input("Observação (Opcional)")
        if st.form_submit_button("Adicionar"):
            if desc and valor > 0:
                mes_data['investimentos'].append({"descricao": desc, "valor": valor, "observacao": obs})
                salvar_dados(db)
                st.rerun()
    renderizar_lista("Listagem de Investimentos", "investimentos", "ph-trend-up")