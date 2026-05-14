import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import fsolve

st.set_page_config(page_title="Pump OPOINT Demo", layout="wide")

st.title("🚀 Pump OPoint (Bomba vs Sistema)")

# --- SIDEBAR: DADOS DO EXCEL ---
st.sidebar.header("⚙️ Parâmetros do Sistema")

with st.sidebar:
    hg_total = st.number_input("Altura Geométrica Total - Hg (m)", value=26.0)
    c_hw = st.number_input("Coeficiente C (Hazen-Williams)", value=150.0)
    
    st.subheader("Sucção")
    d_suc = st.number_input("Diâmetro Sucção (mm)", value=27.2) / 1000
    l_suc = st.number_input("Comprimento Sucção (m)", value=26.0)
    
    st.subheader("Recalque")
    d_rec = st.number_input("Diâmetro Recalque (mm)", value=27.2) / 1000
    l_rec = st.number_input("Comprimento Recalque (m)", value=23.37)

# --- ÁREA PRINCIPAL: CURVA DA BOMBA ---
st.subheader("📊 Dados da Curva da Bomba (Catálogo)")
col1, col2 = st.columns(2)

# Seus dados reais do arquivo CSV/Excel
q_bomba = [2.4, 2.1, 1.8, 1.6, 1.3, 1.1, 0.8, 0.4, 0.2, 3.4]
h_bomba = [3.0, 6.0, 12.0, 18.0, 24.0, 28.0, 36.0, 42.0, 48.0, 22.0]

with col1:
    q_input = [st.number_input(f"Q{i+1} (m³/h)", value=float(q_bomba[i]), key=f"q{i}") for i in range(10)]
with col2:
    h_input = [st.number_input(f"H{i+1} (mca)", value=float(h_bomba[i]), key=f"h{i}") for i in range(10)]

# --- CÁLCULOS ---

# 1. Ajuste Curva da Bomba (Polinômio 2º Grau)
coefs_b = np.polyfit(q_input, h_input, 2)

# 2. Função de Perda de Carga (Hazen-Williams conforme seu Excel)
def calcular_hf_total(Q_m3h):
    if Q_m3h <= 0: return 0
    # Conversão m3/h para m3/s para a fórmula padrão
    Q_m3s = Q_m3h / 3600
    
    # hf = 10.646 * (Q/C)^1.852 * L / D^4.87
    def hw(L, D, Qs):
        return 10.646 * (Qs/c_hw)**1.852 * (L / (D**4.87))
    
    hf_s = hw(l_suc, d_suc, Q_m3s)
    hf_r = hw(l_rec, d_rec, Q_m3s)
    return hf_s + hf_r

# 3. Equação para encontrar o ponto (Bomba - Sistema = 0)
def eq_operacao(Q):
    H_b = np.polyval(coefs_b, Q)
    H_s = hg_total + calcular_hf_total(Q)
    return H_b - H_s

# Resolver
q_op = fsolve(eq_operacao, x0=1.5)[0]
h_op = hg_total + calcular_hf_total(q_op)

# --- GRÁFICO ---
q_range = np.linspace(0.1, max(q_input)*1.1, 100)
h_b_range = np.polyval(coefs_b, q_range)
h_s_range = [hg_total + calcular_hf_total(q) for q in q_range]

fig = go.Figure()
fig.add_trace(go.Scatter(x=q_range, y=h_b_range, name="Bomba (Ajustada)", line=dict(color='blue')))
fig.add_trace(go.Scatter(x=q_range, y=h_s_range, name="Sistema (Hazen-Williams)", line=dict(color='red')))
fig.add_trace(go.Scatter(x=[q_op], y=[h_op], mode="markers+text", name="Ponto de Operação",
                         text=[f"Q={q_op:.2f} m³/h"], textposition="top center", marker=dict(size=12, color='black')))

st.plotly_chart(fig, use_container_width=True)

# --- PAINEL DE RESULTADOS ---
c1, c2, c3 = st.columns(3)
c1.metric("Vazão Real Estimada", f"{q_op:.3f} m³/h")
c2.metric("Hman Total", f"{h_op:.2f} mca")
c3.metric("Hg (Nível)", f"{hg_total} m")
