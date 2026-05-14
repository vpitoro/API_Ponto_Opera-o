import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import fsolve

# --- Configuração da Página ---
st.set_page_config(page_title="HidroCalc API - Ponto de Operação", layout="wide")
st.title("📊 Dimensionamento de Ponto de Operação de Bombas")

# --- Barra Lateral: Entrada de Dados ---
st.sidebar.header("1. Curva Característica da Bomba")
st.sidebar.info("Insira os 10 campos solicitados (Vazão vs Altura)")

q_bomba = []
h_bomba = []

col1, col2 = st.sidebar.columns(2)
for i in range(1, 6):
    q = col1.number_input(f"Vazão {i} (m³/h)", value=float(i*0.5), key=f"q{i}")
    h = col2.number_input(f"Hman {i} (mca)", value=float(50 - i*5), key=f"h{i}")
    q_bomba.append(q)
    h_bomba.append(h)

st.sidebar.header("2. Dados do Sistema (Baseado no Excel)")
hg = st.sidebar.number_input("Altura Geométrica (m)", value=26.0)
p_servico = st.sidebar.number_input("Pressão de Serviço (mca)", value=15.0)

# --- Processamento Lógico ---
# Regressão da Bomba
coefs_bomba = np.polyfit(q_bomba, h_bomba, 2)

# Função para Curva do Sistema (Simplificada para a interface)
def calcular_curva_sistema(q_range):
    # Baseado na sua planilha: Perda de carga cresce com Q^1.852 (Hazen-Williams) ou Darcy
    # Aqui usamos uma constante de resistência k estimada dos seus dados
    k_estimado = 1.1 # Ajustável conforme o diâmetro (27.2mm e 22mm)
    return hg + p_servico + (k_estimado * (q_range**1.852))

# --- Cálculo do Ponto de Interseção ---
def encontrar_intersecao(q):
    return np.polyval(coefs_bomba, q) - calcular_curva_sistema(q)

q_op = fsolve(encontrar_intersecao, x0=np.mean(q_bomba))[0]
h_op = np.polyval(coefs_bomba, q_op)

# --- Representação Gráfica ---
q_plot = np.linspace(0, max(q_bomba)*1.2, 100)
h_bomba_plot = np.polyval(coefs_bomba, q_plot)
h_sistema_plot = calcular_curva_sistema(q_plot)

fig = go.Figure()

# Curva da Bomba
fig.add_trace(go.Scatter(x=q_plot, y=h_bomba_plot, name="Curva da Bomba", line=dict(color='blue', width=3)))

# Curva do Sistema
fig.add_trace(go.Scatter(x=q_plot, y=h_sistema_plot, name="Curva do Sistema", line=dict(color='red', width=3)))

# Ponto de Operação
fig.add_trace(go.Scatter(x=[q_op], y=[h_op], name="Ponto de Operação", 
                         mode='markers+text', text=[f"  {q_op:.2f} m³/h"],
                         marker=dict(color='black', size=12, symbol='x')))

fig.update_layout(title="Interseção Curva da Bomba vs Sistema",
                  xaxis_title="Vazão (m³/h)", yaxis_title="Altura Manométrica (mca)",
                  template="plotly_white")

# --- Exibição na Interface ---
c1, c2 = st.columns([2, 1])
with c1:
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.metric("Vazão de Operação", f"{q_op:.2f} m³/h")
    st.metric("Pressão de Operação", f"{h_op:.2f} mca")
    st.success(f"O sistema operará a {h_op:.1f} mca para vencer a altura de {hg}m + perdas.")
