import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import fsolve

st.set_page_config(page_title="Calculadora Hidráulica Pro", layout="wide")

st.title("📊 Ponto de Operação de Bomba - Darcy-Weisbach")

# --- SIDEBAR: DADOS DO SISTEMA ---
st.sidebar.header("1. Geometria e Tubulação")

with st.sidebar.expander("Tubulação de Sucção", expanded=True):
    h_suc = st.number_input("Altura de Sucção (m)", value=2.0)
    L_suc = st.number_input("Comprimento Sucção (m)", value=5.0)
    D_suc = st.number_input("Diâmetro Sucção (mm)", value=50.0) / 1000
    k_suc_loc = st.number_input("Coef. Perdas Locais Sucção", value=1.5)

with st.sidebar.expander("Tubulação de Recalque", expanded=True):
    h_rec = st.number_input("Altura de Recalque (m)", value=15.0)
    L_rec = st.number_input("Comprimento Recalque (m)", value=100.0)
    D_rec = st.number_input("Diâmetro Recalque (mm)", value=40.0) / 1000
    k_rec_loc = st.number_input("Coef. Perdas Locais Recalque", value=3.0)

st.sidebar.header("2. Propriedades do Fluido")
rugosidade = st.sidebar.number_input("Rugosidade (mm)", value=0.01) / 1000
viscosidade = 1.002e-6 # Água a 20°C

# --- ÁREA PRINCIPAL: CURVA DA BOMBA ---
st.subheader("📝 Curva da Bomba (Inserir até 10 pontos)")
col1, col2 = st.columns(2)

q_pontos = []
h_pontos = []

with col1:
    st.write("**Vazão (m³/h)**")
    for i in range(10):
        val = st.number_input(f"Q{i+1}", value=float(i*2), key=f"q{i}")
        q_pontos.append(val)

with col2:
    st.write("**Altura Manométrica (mca)**")
    # Valores exemplo para a curva não começar zerada
    default_h = [30, 28, 25, 22, 18, 15, 10, 5, 2, 0]
    for i in range(10):
        val = st.number_input(f"H{i+1}", value=float(default_h[i]), key=f"h{i}")
        h_pontos.append(val)

# --- CÁLCULOS ---
# 1. Regressão da Bomba: H = aQ² + bQ + c
coefs_bomba = np.polyfit(q_pontos, h_pontos, 2)

# 2. Função para K (Darcy)
def calcular_K(L, D, e, visc, Q_m3h):
    if Q_m3h <= 0: return 0
    Q = Q_m3h / 3600
    V = (4 * Q) / (np.pi * D**2)
    Re = (V * D) / visc
    # Swamee-Jain para fator de atrito f
    f = 0.25 / (np.log10((e/(3.7*D)) + (5.74/(Re**0.9))))**2
    K_atrito = (8 * f * L) / (np.pi**2 * 9.81 * D**5)
    return K_atrito * (3600**2) # Converte para m/(m3/h)^2

# Hg Total
Hg = h_suc + h_rec

# Função do Sistema: H_sys = Hg + (K_suc + K_rec) * Q^2
def curva_sistema(Q):
    K_s = calcular_K(L_suc, D_suc, rugosidade, viscosidade, Q)
    K_r = calcular_K(L_rec, D_rec, rugosidade, viscosidade, Q)
    return Hg + (K_s + K_r) * (Q**2)

# 3. Encontrar Interseção
def equacao_ponto_otimo(Q):
    H_bomba = coefs_bomba[0]*Q**2 + coefs_bomba[1]*Q + coefs_bomba[2]
    return H_bomba - curva_sistema(Q)

q_op = fsolve(equacao_ponto_otimo, np.mean(q_pontos))[0]
h_op = curva_sistema(q_op)

# --- GRÁFICO ---
q_plot = np.linspace(0, max(q_pontos)*1.2, 100)
h_bomba_plot = np.polyval(coefs_bomba, q_plot)
h_sys_plot = [curva_sistema(q) for q in q_plot]

fig = go.Figure()
fig.add_trace(go.Scatter(x=q_plot, y=h_bomba_plot, name="Curva da Bomba", line=dict(color='blue')))
fig.add_trace(go.Scatter(x=q_plot, y=h_sys_plot, name="Curva do Sistema", line=dict(color='red')))
fig.add_trace(go.Scatter(x=[q_op], y=[h_op], name="Ponto de Operação", mode="markers+text",
                         text=[f"Q:{q_op:.2f} | H:{h_op:.2f}"], textposition="top center",
                         marker=dict(size=12, color='black')))

fig.update_layout(xaxis_title="Vazão (m³/h)", yaxis_title="H (mca)", hovermode="x")

# --- RESULTADOS ---
st.divider()
res1, res2, res3 = st.columns(3)
res1.metric("Vazão de Operação", f"{q_op:.2f} m³/h")
res2.metric("Hman de Operação", f"{h_op:.2f} mca")
res3.metric("Altura Geométrica (Hg)", f"{Hg:.2f} m")

st.plotly_chart(fig, use_container_width=True)
