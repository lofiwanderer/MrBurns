import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ===== PERFORMANCE OPTIMIZATIONS =====
np.seterr(divide='ignore', invalid='ignore')  # Disable Numpy warnings
pd.options.mode.chained_assignment = None  # Disable Pandas SettingWithCopyWarning

# ============== AI AGENTS ==============
class PatternDetector:
    def detect(self, msi_values):
        """Enhanced pattern detection using rolling volatility"""
        if len(msi_values) < 15:
            return {}
        
        series = pd.Series(msi_values)
        
        # Use .iloc for positional indexing
        last_val = series.iloc[-1] if len(series) >= 1 else 0
        fifth_last = series.iloc[-5] if len(series) >= 5 else 0
        
        return {
            'volatility': round(np.std(series.tail(10)), 2),
            'trend': 'Up' if last_val > fifth_last else 'Down',
            'anomalies': len(series[series > series.mean() + 2*series.std()])
        }

class ForecastEnhancer:
    def enhance(self, current_forecast, history):
        """Adds confidence intervals to original forecast"""
        vol = np.std(history[-10:]) if len(history) >=10 else 1
        return {
            'original': current_forecast,
            'low': [x - vol*0.7 for x in current_forecast],
            'high': [x + vol*1.2 for x in current_forecast]
        }

def get_msi_slope(df, window=3):
        if len(df) < window + 1:
            return 0.0
        y = df["msi"].iloc[-(window+1):].values
        x = np.arange(len(y))
        slope = np.polyfit(x, y, 1)[0]
        return round(slope, 2)



# ============== CORE APP ==============
st.set_page_config(page_title="CYA Quantum Tracker", layout="wide", page_icon="🔥")

# Custom CSS for modern UI
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0a0a2a; }
[data-testid="stHeader"] { background: rgba(0,0,0,0.5); }
[data-testid="stToolbar"] { right: 2rem; }
[data-testid="stMetric"] { background: #000033; border-radius: 10px; }
.st-bq { color: #00f7ff !important; }
.st-cb { background-color: #000033 !important; }
</style>
""", unsafe_allow_html=True)

# ================ SESSION STATE =====================
if "roundsc" not in st.session_state:
    st.session_state.roundsc = []
if "ga_pattern" not in st.session_state:
    st.session_state.ga_pattern = None
if "forecast_msi" not in st.session_state:
    st.session_state.forecast_msi = []

# ================ MODERN SIDEBAR ==================
with st.sidebar:
    st.header("⚙️ CONFIGURATION")
    WINDOW_SIZE = st.slider("MSI Window Size", 5, 100, 20)
    PINK_THRESHOLD = st.number_input("💎 Pink Threshold", value=10.0)
    STRICT_RTT = st.checkbox("🔒 Strict RTT Mode", value=False)
    if st.button("🔄 Full Reset", help="Clear all historical data"):
        st.session_state.roundsc = []
        st.session_state.ga_pattern = None
        st.session_state.forecast_msi = []
        st.rerun()
# =================== ROUND ENTRY ========================
with st.container(border=True):
    col1, col2 = st.columns([3,1])
    with col1:
        mult = st.number_input("🎯 Enter Round Multiplier", min_value=0.01, step=0.01)
    with col2:
        if st.button("🚀 Add Round", use_container_width=True):
            score = 2 if mult >= PINK_THRESHOLD else (1 if mult >= 2.0 else -1)
            st.session_state.roundsc.append({
                "timestamp": datetime.now(),
                "multiplier": mult,
                "score": score
            })

# =================== MAIN ANALYSIS ========================
df = pd.DataFrame(st.session_state.roundsc)

if not df.empty:


    
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["type"] = df["multiplier"].apply(lambda x: "Pink" if x >= PINK_THRESHOLD else ("Purple" if x >= 2 else "Blue"))
    df["msi"] = df["score"].rolling(WINDOW_SIZE).sum()  # Original calculation preserved
    df["momentum"] = df["score"].cumsum()

    # ======= MDI Calculation =======
    mdi_value = None
    mdi_note = "N/A"
    
    if len(df) >= 6:
        msi_delta = df["msi"].iloc[-1] - df["msi"].iloc[-6]
        mom_delta = df["momentum"].iloc[-1] - df["momentum"].iloc[-6]
    
        if mom_delta != 0:
            mdi_value = round(msi_delta / mom_delta, 2)
            if mdi_value > 1.2:
                mdi_note = "⬆️ Upward Divergence-should go down"
            elif mdi_value < -1.2:
                mdi_note = "⬇️ Downward Divergence-should go up"
            else:
                mdi_note = "⚖️ Neutral Divergence"
                
    # ============== ENHANCED VISUALIZATION ==============
    def create_msi_chart(df):
        
        
        
        # Create modern Plotly chart
        fig = go.Figure()
        if df.empty:
            return fig
        
        # Convert timestamps to relative time deltas
        time_deltas = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()/60  # Minutes


        # Burst Zone (>=6)
        # Add zones first so MSI line draws on top
        fig.add_trace(go.Scatter(
            x=time_deltas, y=df['msi'].where(df['msi'] >= 6, None ),
            fill='tozeroy',
            fillcolor='rgba(255,105,180,0.3)',
            name='Burst Zone',
            line=dict(width=0),
            visible=True,
            showlegend=True,
            hoverinfo='skip',
            mode='none'  # Hide line for pure fill
        ))
        
        # Surge Zone (3 < x <6)
        fig.add_trace(go.Scatter(
            x=time_deltas, y=df['msi']. where (df['msi'] >= 3, df['msi'] < 6),
            fill='tozeroy',
            fillcolor='rgba(0,255,255,0.3)',
            name='Surge Zone',
            line=dict(width=0),
            visible=True,
            showlegend=True,
            hoverinfo='skip',
            mode='none',
            
        ))
        
            
        # Pullback Zone (<=-3)
        fig.add_trace(go.Scatter(
        x=time_deltas, y=df['msi']. where (df['msi'] <= -3, None),
        fill='tozeroy',
        fillcolor='rgba(255,51,51,0.3)',
        name='Pullback Zone',
        line=dict(width=0),
        visible=True,
        showlegend=True,
        hoverinfo='skip',
        mode='none',
        
        ))
        
        # Main MSI line
        fig.add_trace(go.Scatter(
            x=time_deltas,
            y=df['msi'],
            name='MSI',
            line=dict(color='#00f7ff', width=3),
            customdata=df['timestamp'],
            hovertemplate='<b>%{customdata|%H:%M:%S}</b><br>MSI: %{y:.2f}<extra></extra>'
        ))

        # ===== 1. Zero Axis Line =====
        fig.add_hline(
            y=0, 
            line_dash="dash", 
            line_color="white",
            line_width=2,
            opacity=0.8,
            annotation_text="0", 
            annotation_position="bottom right"
        )
        
        # ===== 2. Pullback Trap Detection =====
        pullback_zones = []
        for i in range(2, len(df)):
            m1, m2, m3 = df['multiplier'].iloc[i-2:i+1].values
            msi_now = df['msi'].iloc[i]
            try:
                if msi_now >= 2:
                    three_blues = m1 < 2.0 and m2 < 2.0 and m3 < 2.0
                    two_desc = m2 < 2.0 and m3 < 2.0 and m2 > m3
                
                    if three_blues or two_desc:
                        # Convert timestamp to relative minutes
                        center = time_deltas.iloc[i]
                        pullback_zones.append((
                            max(0, center - 0.5),  # x0
                            center + 0.5           # x1
                        ))
            except IndexError:
                continue
    
        # Add pullback zones as shapes
        for zone in pullback_zones:
            fig.add_vrect(
                x0=zone[0], x1=zone[1],
                fillcolor="red", opacity=0.15,
                layer="above", line_width=0
            )
            
        
        # Add enhanced forecast if available
        if st.session_state.forecast_msi and len(df) > 3:
            try:
                enhancer = ForecastEnhancer()
                enhanced = enhancer.enhance(st.session_state.forecast_msi, df['msi'].values[-10:])
                
                forecast_times = [time_deltas.iloc[-1] + i*5 for i in [1,2,3]]  # 5-min intervals
                
                fig.add_trace(go.Scatter(
                    x=forecast_times,
                    y=enhanced['original'],
                    name='Forecast',
                    line=dict(color='#ff00ff', width=2, dash='dot'),
                    error_y=dict(
                        type='data',
                        symmetric=False,
                        array=[h-l for h,l in zip(enhanced['high'], enhanced['low'])],
                        arrayminus=[o-l for o,l in zip(enhanced['original'], enhanced['low'])]
                    )
                ))
            except Exception as e:
                st.error(f"Forecast error: {str(e)}")
            
         # Layout configuration
        fig.update_layout(
            xaxis=dict(
                title='Minutes Since First Round',
                tickformat='.0f',
                dtick=1,  # 1-minute intervals
                gridcolor='rgba(255,255,255,0.1)',
                rangeslider=dict(visible=True)
            ),
            yaxis=dict(title='MSI Value'),
            showlegend=True,
            height=500,  # Set fixed height
            legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        
        ))
        
        # Dynamic zoom for recent activity
        if len(time_deltas) > 10:
            last_time = time_deltas.iloc[-1]
            fig.update_xaxes(range=[max(0, last_time-15), last_time+5])
        return fig  # Properly indented inside function
# Display chart header
    st.subheader("🌌 MSI Tactical Display")
    
    # Create and display chart
    msi_chart = create_msi_chart(df)
    st.plotly_chart(msi_chart, use_container_width=True)

    # Log
    st.subheader("Round Log (Editable)")
    edited = st.data_editor(df.tail(30), use_container_width=True, num_rows="dynamic")
    st.session_state.roundsc = edited.to_dict('records')
     
    # ============== ENHANCED FORECAST BUBBLE ==============
    if len(df) >= WINDOW_SIZE + 3:
        try:
            avg_score = np.nanmean(df["score"].iloc[-WINDOW_SIZE:])
            if not np.isnan(avg_score):
                st.session_state.forecast_msi = [
                    round(df["msi"].iloc[-1] + avg_score*(i+1), 2) 
                    for i in range(3)
                ]
        except:
            st.session_state.forecast_msi = None
            
        with st.container(border=True):
            st.subheader("🔮 Quantum Forecast Bubble")
            detector = PatternDetector()
            patterns = detector.detect(df['msi'].values)
            
            cols = st.columns(3)
            cols[0].metric("Current Volatility", f"{patterns.get('volatility', 0)}σ")
            cols[1].metric("Trend Direction", patterns.get('trend', 'N/A'))
            cols[2].metric("Anomaly Count", patterns.get('anomalies', 0))
            
            enhancer = ForecastEnhancer()
            enhanced = enhancer.enhance(st.session_state.forecast_msi, df['msi'].values)
            
            st.write("```")
            st.write("Original Forecast:", st.session_state.forecast_msi)
            st.write("Safe Zone:", [f"{x:.2f}" for x in enhanced['low']])
            st.write("Aggressive Zone:", [f"{x:.2f}" for x in enhanced['high']])
            st.write("```")

    # ============== RISK MANAGEMENT PANEL ==============
    with st.expander("🛡️ Risk Management Suite", expanded=True):
        wins = len(df[df['multiplier'] >= 2])
        losses = len(df) - wins
        risk_ratio = wins/(losses+1e-9)
        
        cols = st.columns(3)
        cols[0].metric("Win Rate", f"{(wins / (len(df) + 1e-9) * 100):.1f}%")  # Fixed parenthesis
        cols[1].metric("Risk/Reward", f"1:{risk_ratio:.1f}")
        cols[2].progress(
            min(1, risk_ratio/3), 
            text=f"Confidence Level: {min(100, risk_ratio*33):.0f}%"
        )
        
    # ============== ORIGINAL FUNCTIONALITY PRESERVED ==============
    # Entry Decision
    st.subheader("Entry Decision Assistant")
    latest_msi = df["msi"].iloc[-1]
    # === Visual Slope Display ===
    msi_slope = get_msi_slope(df)
    
    slope_arrow = "↗️" if msi_slope > 0.1 else "↘️" if msi_slope < -0.1 else "➡️"
    slope_color = "green" if msi_slope > 0.1 else "red" if msi_slope < -0.1 else "gray"
    
    st.markdown(f"<span style='color:{slope_color}; font-size: 20px;'>MSI Slope: {slope_arrow} {msi_slope}</span>", unsafe_allow_html=True)

    if latest_msi >= 6:
        st.success("✅ PINK Entry Zone")
    elif 3 <= latest_msi < 6:
        st.info("🟣 PURPLE Surge Opportunity")
    elif latest_msi <= -3:
        st.warning("❌ Pullback Danger — Avoid")
    else:
        st.info("⏳ Neutral — Wait and Observe")

    st.info(f"🧭 MDI: `{mdi_value}` — {mdi_note}")
    # ... [Your existing MDI, projections, and other original code here] ...

else:
    st.info("🎮 Enter your first round to begin analysis")
