import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import fsolve

st.set_page_config(page_title="Hidráulica Pro - Darcy-Weisbach", layout="wide")

st.title("💧 Ponto de Operação: Equação Universal de Darcy-Weisbach")

# --- SIDEBAR: DADOS TÉCNICOS ---
st.sidebar.header("📐 Geometria do Sistema")
hg = st.sidebar.number_input("Altura Geométrica Total - Hg (m)", value=26.0)
rugosidade = st.sidebar.number_input("Rugosidade do Material - ε (mm)", value=0.01) / 1000 # PVC é ~0.01mm

with st.sidebar.expander("Sucção", expanded=True):
    d_suc = st.number_input("Diâmetro Sucção (mm)", value=27.2) / 1000
    l_suc = st.number_input("Comprimento Sucção (m)", value=26.0)
    k_loc_s = st.number_input("Perdas Locais (K) - Sucção", value=1.5)

with st.sidebar.expander("Recalque", expanded=True):
    d_rec = st.number_input("Diâmetro Recalque (mm)", value=27.2) / 1000
    l_rec = st.number_input("Comprimento Recalque (m)", value=23.37)
    k_loc_r = st.number_input("Perdas Locais (K) - Recalque", value=3.5)

# --- ÁREA PRINCIPAL: 20 CAMPOS DA BOMBA ---
st.subheader("🛠️ Curva da Bomba (Catálogo)")
st.info("Insira os 10 pontos de Vazão e Altura Manométrica.")

q_bomba = [2.4, 2.1, 1.8, 1.6, 1.3, 1.1, 0.8, 0.4, 0.2, 0.0]
h_bomba = [3.0, 6.0, 12.0, 18.0, 24.0, 28.0, 36.0, 42.0, 48.0, 55.0]

col1, col2 = st.columns(2)
q_in = []
h_in = []

for i in range(10):
    with col1:
        q_val = st.number_input(f"Vazão Q{i+1} (m³/h)", value=q_bomba[i], key=f"q{i}")
        q_in.append(q_val)
    with col2:
        h_val = st.number_input(f"Altura H{i+1} (mca)", value=h_bomba[i], key=f"h{i}")
        h_in.append(h_val)

# --- LÓGICA DE CÁLCULO DARCY-WEISBACH ---

def calcular_perda_carga_darcy(Q_m3h, L, D, eps):
    if Q_m3h <= 0: return 0
    
    # 1. Conversões
    Q = Q_m3h / 3600 # m3/s
    V = (4 * Q) / (np.pi * D**2)
    visc_cin = 1.002e-6 # Água a 20°C
    
    # 2. Reynolds
    Re = (V * D) / visc_cin
    
    # 3. Fator de Atrito (f) - Swamee-Jain (Aproximação direta de Colebrook)
    if Re < 2000:
        f = 64 / Re # Regime Laminar
    else:
        # Regime Turbulento
        f = 0.25 / (np.log10((eps/(3.7*D)) + (5.74/(Re**0.9))))**2
    
    # 4. Darcy-Weisbach: hf = f * (L/D) * (V²/2g)
    g = 9.81
    hf_distribuida = f * (L / D) * (V**2 / (2 * g))
    
    # 5. Perdas Locais: h_loc = K * (V²/2g)
    # (Opcional, se quiser incluir os acessórios da sua planilha)
    # hf_local = k_local * (V**2 / (2 * g))
    
    return hf_distribuida

def h_sistema(Q):
    perda_s = calcular_perda_carga_darcy(Q, l_suc, d_suc, rugosidade)
    perda_r = calcular_perda_carga_darcy(Q, l_rec, d_rec, rugosidade)
    return hg + perda_s + perda_r

# Ajuste da Bomba (Regressão)
coefs = np.polyfit(q_in, h_in, 2)

# Ponto de Interseção
def objetivo(Q):
    return np.polyval(coefs, Q) - h_sistema(Q)

try:
    q_op = fsolve(objetivo, x0=max(q_in)/2)[0]
    h_op = h_sistema(q_op)
except:
    q_op, h_op = 0, hg

# --- VISUALIZAÇÃO ---
q_plot = np.linspace(0, max(q_in)*1.1, 100)
h_b_plot = np.polyval(coefs, q_plot)
h_s_plot = [h_sistema(q) for q in q_plot]

fig = go.Figure()
fig.add_trace(go.Scatter(x=q_plot, y=h_b_plot, name="Curva da Bomba (Darcy)", line=dict(color='blue')))
fig.add_trace(go.Scatter(x=q_plot, y=h_s_plot, name="Curva do Sistema (Darcy)", line=dict(color='red')))
fig.add_trace(go.Scatter(x=[q_op], y=[h_op], mode="markers+text", 
                         text=[f"Ponto de Operação"], textposition="top right",
                         marker=dict(size=12, color='black')))

st.plotly_chart(fig, use_container_width=True)

st.success(f"Ponto de Operação Encontrado: Vazão = {q_op:.3f} m³/h | Hman = {h_op:.2f} mca")
