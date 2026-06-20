"""
AMBROSIO — Interface Web (Streamlit)
Execute com: streamlit run app.py
"""

import sys
import os
from pathlib import Path

# Garante que o diretório raiz do projeto está no path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import tempfile
from src.reader import extrair_lote_pgtos, extrair_itau
from src.comparator import comparar_pagamentos
from src.reporter import gerar_relatorio

# ── Configuração da página ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AMBROSIO",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Estilos ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .header-box {
        background: linear-gradient(135deg, #1F3864 0%, #2E5490 100%);
        border-radius: 12px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        color: white;
    }
    .header-box h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-box p {
        font-size: 1rem;
        opacity: 0.8;
        margin: 0.4rem 0 0 0;
    }

    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-left: 4px solid #1F3864;
        margin-bottom: 1rem;
    }
    .metric-card.ok    { border-left-color: #22c55e; }
    .metric-card.warn  { border-left-color: #f59e0b; }
    .metric-card.error { border-left-color: #ef4444; }

    .metric-label { font-size: 0.78rem; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #111827; }

    .upload-area {
        background: #f8fafc;
        border: 2px dashed #cbd5e1;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }

    .status-ok       { color: #16a34a; font-weight: 600; }
    .status-div      { color: #dc2626; font-weight: 600; }
    .status-warn     { color: #d97706; font-weight: 600; }

    .stButton>button {
        background: linear-gradient(135deg, #1F3864, #2E5490);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton>button:hover { opacity: 0.9; }

    .chat-user {
        background: #eff6ff;
        border-radius: 12px 12px 4px 12px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        text-align: right;
        color: #1e40af;
        font-weight: 500;
    }
    .chat-bot {
        background: #f1f5f9;
        border-radius: 12px 12px 12px 4px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
        color: #1e293b;
    }

    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
    <h1>💼 AMBROSIO</h1>
    <p>Conferência automática de pagamentos · DB1 Group</p>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "df_resultado" not in st.session_state:
    st.session_state.df_resultado = None
if "historico_chat" not in st.session_state:
    st.session_state.historico_chat = []

# ── Seção 1: Upload ────────────────────────────────────────────────────────────
st.subheader("📤 Carregar arquivos")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Lote de Pagamentos**")
    arquivo_lote = st.file_uploader("0-LOTES PGTOS", type=["pdf"], key="lote", label_visibility="collapsed")
    if arquivo_lote:
        st.success(f"✔ {arquivo_lote.name}")

with col2:
    st.markdown("**Extrato Itaú**")
    arquivo_itau = st.file_uploader("0-ITAU", type=["pdf"], key="itau", label_visibility="collapsed")
    if arquivo_itau:
        st.success(f"✔ {arquivo_itau.name}")

st.markdown("")
_, col_btn, _ = st.columns([2, 1, 2])
with col_btn:
    processar = st.button("⚖️ Processar", disabled=not (arquivo_lote and arquivo_itau))

# ── Processamento ──────────────────────────────────────────────────────────────
if processar and arquivo_lote and arquivo_itau:
    with st.spinner("Lendo e comparando os arquivos..."):
        with tempfile.TemporaryDirectory() as tmpdir:
            path_lote = Path(tmpdir) / arquivo_lote.name
            path_itau = Path(tmpdir) / arquivo_itau.name
            path_lote.write_bytes(arquivo_lote.read())
            path_itau.write_bytes(arquivo_itau.read())

            df_lote = extrair_lote_pgtos(path_lote)
            df_itau = extrair_itau(path_itau)
            df_resultado = comparar_pagamentos(df_lote, df_itau)
            st.session_state.df_resultado = df_resultado
            st.session_state.historico_chat = []

# ── Resultados ─────────────────────────────────────────────────────────────────
if st.session_state.df_resultado is not None:
    df = st.session_state.df_resultado

    total      = len(df)
    ok         = len(df[df["status"] == "OK"])
    divergente = len(df[df["status"] == "DIVERGENTE"])
    nao_achado = total - ok - divergente
    total_dif  = df["diferenca"].fillna(0).sum()

    st.markdown("---")
    st.subheader("📊 Resumo")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class="metric-card ok">
            <div class="metric-label">Sem divergência</div>
            <div class="metric-value">{ok}</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card error">
            <div class="metric-label">Divergentes</div>
            <div class="metric-value">{divergente}</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class="metric-card warn">
            <div class="metric-label">Não encontrados</div>
            <div class="metric-value">{nao_achado}</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        dif_fmt = f"R$ {abs(total_dif):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        cor_card = "error" if abs(total_dif) > 0.01 else "ok"
        st.markdown(f"""<div class="metric-card {cor_card}">
            <div class="metric-label">Diferença total</div>
            <div class="metric-value">{dif_fmt}</div>
        </div>""", unsafe_allow_html=True)

    # ── Tabela ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    aba_todas, aba_div = st.tabs(["📋 Todos os registros", "⚠️ Apenas divergências"])

    def formatar_df_exibicao(df_in):
        df_ex = df_in.copy()
        for col in ["valor_lote", "valor_itau", "diferenca"]:
            if col in df_ex.columns:
                df_ex[col] = df_ex[col].apply(
                    lambda v: f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".") if pd.notna(v) else "-"
                )
        df_ex = df_ex.rename(columns={
            "favorecido_lote": "Favorecido (Lote)",
            "valor_lote": "Valor Lote",
            "favorecido_itau": "Favorecido (Itaú)",
            "valor_itau": "Valor Itaú",
            "diferenca": "Diferença",
            "status": "Status",
            "score_similaridade": "Similaridade %"
        })
        return df_ex.fillna("-")

    with aba_todas:
        st.dataframe(formatar_df_exibicao(df), use_container_width=True, height=400)

    with aba_div:
        df_div = df[df["status"] != "OK"]
        if df_div.empty:
            st.success("✅ Nenhuma divergência encontrada!")
        else:
            st.dataframe(formatar_df_exibicao(df_div), use_container_width=True, height=400)

    # ── Download ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⬇️ Baixar relatório")

    with tempfile.TemporaryDirectory() as tmpdir:
        caminho_rel = gerar_relatorio(df, Path(tmpdir))
        with open(caminho_rel, "rb") as f:
            dados_excel = f.read()

    st.download_button(
        label="📥 Baixar relatorio_divergencias.xlsx",
        data=dados_excel,
        file_name="relatorio_divergencias.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ── Chat RAG ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("💬 Pergunte sobre os pagamentos")
    st.caption("Exemplos: 'Qual fornecedor teve maior diferença?' · 'Quantos pagamentos ficaram pendentes?' · 'Liste os divergentes'")

    for msg in st.session_state.historico_chat:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bot">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

    with st.form("form_chat", clear_on_submit=True):
        pergunta = st.text_input("Sua pergunta", placeholder="Ex: qual foi a maior divergência?", label_visibility="collapsed")
        enviar = st.form_submit_button("Enviar")

    if enviar and pergunta.strip():
        st.session_state.historico_chat.append({"role": "user", "content": pergunta})

        # Monta contexto com os dados reais
        contexto = df.to_string(index=False)
        total_str = f"Total: {total} registros. OK: {ok}. Divergentes: {divergente}. Não encontrados: {nao_achado}. Diferença total: R$ {total_dif:.2f}."

        import anthropic
        cliente = anthropic.Anthropic()
        resposta = cliente.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=(
                "Você é o AMBROSIO, assistente financeiro da DB1 Group. "
                "Responda perguntas sobre os dados de conciliação de pagamentos abaixo. "
                "Seja objetivo, use valores em reais (R$) e responda sempre em português. "
                f"\n\nResumo: {total_str}"
                f"\n\nDados completos:\n{contexto}"
            ),
            messages=[
                {"role": "user", "content": pergunta}
            ]
        )

        texto_resposta = resposta.content[0].text
        st.session_state.historico_chat.append({"role": "assistant", "content": texto_resposta})
        st.rerun()

else:
    st.info("📂 Carregue os dois arquivos PDF acima e clique em **Processar** para começar.")
