import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Momentum Tracker v2", layout="wide")

st.title("Momentum Tracker App v2: MSI + Sniper + RTT")

# Session states for data
if "rounds" not in st.session_state:
    st.session_state.rounds = []

# MSI Config
WINDOW_SIZE = st.sidebar.slider("MSI Window Size", 10, 100, 20)
PINK_THRESHOLD = st.sidebar.number_input("Pink Threshold (default = 10.0x)", value=10.0)
STRICT_RTT = st.sidebar.checkbox("Strict RTT Mode", value=True)

# Manual input
st.subheader("Manual Round Entry")
multiplier = st.number_input("Enter multiplier", min_value=0.01, step=0.01)
if st.button("Add Round"):
    st.session_state.rounds.append({
        "timestamp": datetime.now(),
        "multiplier": multiplier,
        "score": 2 if multiplier >= PINK_THRESHOLD else (1 if multiplier >= 2 else -1)
    })

# Convert to DataFrame
df = pd.DataFrame(st.session_state.rounds)
if not df.empty:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["msi"] = df["score"].rolling(WINDOW_SIZE).sum()
    df["type"] = df["multiplier"].apply(lambda x: "Pink" if x >= PINK_THRESHOLD else ("Purple" if x >= 2 else "Blue"))

    st.subheader("Round Log")
    st.dataframe(df.tail(30), use_container_width=True)

    # Plot MSI
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(df["timestamp"], df["msi"], label="MSI", color="black")
    ax.axhline(0, color="gray", linestyle="--")
    ax.fill_between(df["timestamp"], df["msi"], where=(df["msi"] >= 6), color="pink", alpha=0.3, label="Burst Zone")
    ax.fill_between(df["timestamp"], df["msi"], where=(df["msi"] <= -6), color="red", alpha=0.2, label="Red Zone")
    ax.fill_between(df["timestamp"], df["msi"], where=((df["msi"] > 0) & (df["msi"] < 6)), color="purple", alpha=0.1, label="Surge Zone")
    ax.legend()
    ax.set_title("Momentum Score Index (MSI)")
    st.pyplot(fig)

    # Sniper Logic
    st.subheader("Sniper Pink Projections")
    df["projected_by"] = None
    projections = []
    for i, row in df.iterrows():
        if row["type"] == "Pink":
            for j, prior in df.iloc[:i].iterrows():
                diff = (row["timestamp"] - prior["timestamp"]).total_seconds() / 60
                if prior["type"] == "Pink":
                    if 8 <= diff <= 12 or 18 <= diff <= 22:
                        df.at[i, "projected_by"] = prior["timestamp"].strftime("%H:%M:%S")
                        projections.append((prior["timestamp"], row["timestamp"]))

    st.write(df[df["type"] == "Pink"].tail(20)[["timestamp", "multiplier", "projected_by"]])

    # Entry Recommendation
    latest_msi = df["msi"].iloc[-1]
    latest_type = df["type"].iloc[-1]
    st.subheader("Entry Decision Assistant")
    if latest_msi >= 6:
        st.success("PINK Entry Zone")
    elif 3 <= latest_msi < 6:
        st.info("PURPLE Entry Zone")
    elif latest_msi <= -3:
        st.warning("Pullback Zone - Avoid Entry")
    else:
        st.info("Neutral Zone - Wait")

else:
    st.info("Enter rounds to begin analysis.")
