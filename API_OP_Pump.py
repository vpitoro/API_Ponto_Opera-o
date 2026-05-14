import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import fsolve

st.set_page_config(page_title="Ponto de Operação - Darcy-Weisbach", layout="wide")

st.title("💧 Ponto de Operação da Bomba - Sistema de Irrigação")

# --- SIDEBAR: DADOS TÉCNICOS ---
st.sidebar.header("📐 Geometria do Sistema")
hg = st.sidebar.number_input("Altura Geométrica Total - Hg (m)", value=26.0)
rugosidade = st.sidebar.number_input("Rugosidade do Material - ε (mm)", value=0.01) / 1000 

with st.sidebar.expander("Sucção", expanded=True):
    d_suc = st.number_input("Diâmetro Sucção (mm)", value=27.2) / 1000
    l_suc = st.number_input("Comprimento Sucção (m)", value=26.0)
    k_loc_s = st.number_input("Perdas Locais (K) - Sucção", value=1.5)

with st.sidebar.expander("Recalque", expanded=True):
    d_rec = st.number_input("Diâmetro Recalque (mm)", value=27.2) / 1000
    l_rec = st.number_input("Comprimento Recalque (m)", value=23.37)
    k_loc_r = st.number_input("Perdas Locais (K) - Recalque", value=3.5)

# --- SEÇÃO OCULTÁVEL: DADOS DA BOMBA ---
# O expander permite "esconder" os 20 campos de entrada
with st.expander("🛠️ Configurar Pontos da Curva da Bomba (Catálogo)", expanded=False):
    st.info("Insira os pontos de Vazão (m³/h) e Altura (mca) conforme o catálogo do fabricante.")
    
    q_bomba_ref = [2.4, 2.1, 1.8, 1.6, 1.3, 1.1, 0.8, 0.4, 0.2, 0.0]
    h_bomba_ref = [3.0, 6.0, 12.0, 18.0, 24.0, 28.0, 36.0, 42.0, 48.0, 55.0]
    
    col1, col2 = st.columns(2)
    q_in = []
    h_in = []
    
    for i in range(10):
        with col1:
            q_val = st.number_input(f"Vazão Q{i+1} (m³/h)", value=q_bomba_ref[i], key=f"q{i}")
            q_in.append(q_val)
        with col2:
            h_val = st.number_input(f"Altura H{i+1} (mca)", value=h_bomba_ref[i], key=f"h{i}")
            h_in.append(h_val)

# --- LÓGICA DE CÁLCULO ---

def calcular_perda_carga_total(Q_m3h, L, D, eps, K_local):
    if Q_m3h <= 0: return 0
    
    Q = Q_m3h / 3600 # m3/s
    V = (4 * Q) / (np.pi * D**2)
    visc_cin = 1.002e-6
    g = 9.81
    
    # Reynolds
    Re = (V * D) / visc_cin
    
    # Fator de Atrito (Swamee-Jain)
    if Re < 2000:
        f = 64 / Re
    else:
        f = 0.25 / (np.log10((eps/(3.7*D)) + (5.74/(Re**0.9))))**2
    
    # Perda Distribuída + Local
    hf_dist = f * (L / D) * (V**2 / (2 * g))
    hf_loc = K_local * (V**2 / (2 * g))
    
    return hf_dist + hf_loc

def h_sistema(Q):
    perda_s = calcular_perda_carga_total(Q, l_suc, d_suc, rugosidade, k_loc_s)
    perda_r = calcular_perda_carga_total(Q, l_rec, d_rec, rugosidade, k_loc_r)
    return hg + perda_s + perda_r

# Regressão da Bomba
coefs = np.polyfit(q_in, h_in, 2)

# Ponto de Interseção
def objetivo(Q):
    return np.polyval(coefs, Q) - h_sistema(Q)

try:
    # Busca o ponto onde a curva da bomba cruza a do sistema
    q_op = fsolve(objetivo, x0=max(q_in)/2)[0]
    h_op = h_sistema(q_op)
except:
    q_op, h_op = 0, hg

# --- VISUALIZAÇÃO ---
st.subheader("📊 Gráfico de Performance do Sistema")

q_plot = np.linspace(0, max(q_in)*1.1 if max(q_in) > 0 else 10, 100)
h_b_plot = np.polyval(coefs, q_plot)
h_s_plot = [h_sistema(q) for q in q_plot]

fig = go.Figure()
fig.add_trace(go.Scatter(x=q_plot, y=h_b_plot, name="Curva da Bomba", line=dict(color='#1f77b4', width=3)))
fig.add_trace(go.Scatter(x=q_plot, y=h_s_plot, name="Curva do Sistema", line=dict(color='#ff7f0e', width=3)))

# Destaque do Ponto de Operação
fig.add_trace(go.Scatter(
    x=[q_op], y=[h_op],
    mode="markers+text",
    name="Ponto de Operação",
    text=[f"Q={q_op:.2f} | H={h_op:.1f}"],
    textposition="top center",
    marker=dict(size=14, color='black', symbol='diamond')
))

fig.update_layout(
    xaxis_title="Vazão (m³/h)",
    yaxis_title="Altura Manométrica (mca)",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

st.plotly_chart(fig, use_container_width=True)

# Métricas em destaque
c1, c2 = st.columns(2)
c1.metric("Vazão de Operação", f"{q_op:.3f} m³/h")
c2.metric("Altura Manométrica (Hman)", f"{h_op:.2f} mca")
