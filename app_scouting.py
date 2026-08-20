import io
import os
import unicodedata
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Scouting Handball U18", page_icon="🤾‍♀️", layout="wide")

EXCEL_FILE = "data_handball.xlsx"

def clean_txt(text):
    if not text or pd.isna(text):
        return ""
    text_norm = unicodedata.normalize('NFKD', str(text))
    return text_norm.encode('ascii', 'ignore').decode('utf-8').strip()

@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame(), pd.DataFrame()
    df_raw = pd.read_excel(EXCEL_FILE, sheet_name="DATA_MATCHS").fillna(0)
    
    df_grouped = df_raw.groupby(["Nom_Joueuse", "Competition"], as_index=False).agg({
        "Type_Poste": "first",
        "Poste_Precis": "first",
        "Pays": "first",
        "Age": "max",
        "Club": "first",
        "Taille": "max",
        "Min_Jouees": ["count", "sum"],
        "Titulaire": "sum",
        "Buts_Sans_7m": "sum",
        "Buts_7m": "sum",
        "Tirs_7m": "sum",
        "Buts_Totaux": "sum",
        "Buts_6m": "sum",
        "Buts_9m": "sum",
        "Buts_Wing": "sum",
        "Buts_FB": "sum",
        "Buts_Brk": "sum",
        "Buts_LD": "sum",
        "Passes_D": "sum",
        "Tirs_Bloques": "sum",
        "Sanctions_2min": "sum",
        "Cartons_Rouges": "sum",
        "Arrets_Totaux": "sum",
        "Tirs_Subis": "sum",
        "Arrets_7m": "sum",
        "Tirs_7m_Subis": "sum",
        "Arrets_6m": "sum",
        "Arrets_9m": "sum",
        "Arrets_Wing": "sum",
        "Arrets_FB": "sum",
        "Arrets_Brk": "sum",
        "Arrets_LD": "sum"
    })
    
    df_grouped.columns = [
        "Nom_Joueuse", "Competition", "Type_Poste", "Poste_Precis", "Pays",
        "Age", "Club", "Taille", "Matchs_Joues", "Min_Totales", "Titularisations",
        "Buts", "Buts_7m", "Tirs_7m", "Buts_Totaux",
        "Buts_6m", "Buts_9m", "Buts_Wing", "Buts_FB", "Buts_Brk", "Buts_LD",
        "Passes_D", "Tirs_Bloques", "Sanctions_2m", "Cartons_Rouges",
        "Arrets_Totaux", "Tirs_Subis", "Arrets_7m", "Tirs_7m_Subis",
        "Arrets_6m", "Arrets_9m", "Arrets_Wing", "Arrets_FB", "Arrets_Brk", "Arrets_LD"
    ]
    
    df_grouped["Implication"] = df_grouped["Buts"] + df_grouped["Buts_7m"] + df_grouped["Passes_D"]
    df_grouped["Pct_Arrets"] = np.where(df_grouped["Tirs_Subis"] > 0, (df_grouped["Arrets_Totaux"] / df_grouped["Tirs_Subis"]) * 100, 0).round(1)
    df_grouped["Pct_7m"] = np.where(df_grouped["Tirs_7m"] > 0, (df_grouped["Buts_7m"] / df_grouped["Tirs_7m"]) * 100, 0).round(1)
    df_grouped["Buts_PM"] = (df_grouped["Buts"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["PassesD_PM"] = (df_grouped["Passes_D"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["Impl_PM"] = (df_grouped["Implication"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["Arrets_PM"] = (df_grouped["Arrets_Totaux"] / df_grouped["Matchs_Joues"]).round(1)

    return df_raw, df_grouped

df_raw, df = load_data()

st.title("🤾‍♀️ Hub de Détection & Scouting Handball U18")

# --- FILTRES LATÉRAUX ---
st.sidebar.header("🎯 Filtres de Recherche")

# 1. Multi-sélection Pays
all_pays = sorted([p for p in df["Pays"].unique() if str(p) not in ["0", "Inconnu", "0.0"]])
selected_pays = st.sidebar.multiselect("Pays / Sélections", all_pays, default=[])

# 2. Poule Haute / Poule Basse
poule_filter = st.sidebar.selectbox("Tableau de compétition", ["Toutes", "Poule Haute (Main Round / Finales)", "Poule Basse (President's Cup)"])

# 3. Postes
type_poste_sel = st.sidebar.selectbox("Catégorie de Poste", ["Tous", "CHAMP", "GARDIENNE"])
postes_dispos = sorted([p for p in df["Poste_Precis"].unique() if p != "Non renseigné"])
selected_postes = st.sidebar.multiselect("Poste(s) précis", postes_dispos, default=[])

# 4. Matchs min
min_matchs = st.sidebar.slider("Matchs joués min.", 1, int(df["Matchs_Joues"].max()) if not df.empty else 8, 3)

# Filtrage du dataset brut si filtre de poule
df_working = df.copy()
if poule_filter != "Toutes":
    tag = "Poule Haute" if "Haute" in poule_filter else "Poule Basse"
    joueuses_poule = df_raw[df_raw["Poule_Niveau"] == tag]["Nom_Joueuse"].unique()
    df_working = df_working[df_working["Nom_Joueuse"].isin(joueuses_poule)]

if selected_pays:
    df_working = df_working[df_working["Pays"].isin(selected_pays)]
if type_poste_sel != "Tous":
    df_working = df_working[df_working["Type_Poste"] == type_poste_sel]
if selected_postes:
    df_working = df_working[df_working["Poste_Precis"].isin(selected_postes)]
df_working = df_working[df_working["Matchs_Joues"] >= min_matchs]

# --- CRITÈRES DE CLASSEMENT AVEC SECTEURS ---
st.sidebar.header("📊 Critère de Classement")
if type_poste_sel == "GARDIENNE":
    criteres = {
        "% d'Arrêts": "Pct_Arrets", "Arrêts Totaux": "Arrets_Totaux", "Arrêts par Match": "Arrets_PM",
        "Arrêts 7m": "Arrets_7m", "Arrêts 6m": "Arrets_6m", "Arrêts 9m": "Arrets_9m",
        "Arrêts Ailes (Wing)": "Arrets_Wing", "Arrêts Contre-attaque (FB)": "Arrets_FB",
        "Arrêts Percée (Brk)": "Arrets_Brk", "Relances (Passes D)": "Passes_D"
    }
else:
    criteres = {
        "Buts (Hors 7m)": "Buts", "Buts par Match": "Buts_PM", "Implication (Buts+7m+Assists)": "Implication",
        "Buts 7m": "Buts_7m", "Assists / Passes D": "Passes_D", "Secteur 6m": "Buts_6m",
        "Secteur 9m": "Buts_9m", "Secteur Ailes (Wing)": "Buts_Wing", "Contre-attaque (FB)": "Buts_FB",
        "Percée (Brk)": "Buts_Brk", "Buts Cage Vide (LD)": "Buts_LD", "Tirs Bloqués": "Tirs_Bloques",
        "Titularisations (S)": "Titularisations", "Discipline (Moins de 2m)": "Sanctions_2m"
    }

tri_choisi = st.sidebar.selectbox("Classer par", list(criteres.keys()))
col_tri = criteres[tri_choisi]
ordre_asc = True if "Moins" in tri_choisi else False
top_n = st.sidebar.slider("Afficher le Top :", 5, 50, 15)

df_top = df_working.sort_values(by=col_tri, ascending=ordre_asc).reset_index(drop=True)
df_top.index += 1

# Affichage tableau
st.subheader(f"🏆 Top {top_n} — {tri_choisi}")
cols_base = ["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", "Titularisations", "Buts", "Buts_7m", "Passes_D", "Implication", "Sanctions_2m", "Cartons_Rouges"] if type_poste_sel != "GARDIENNE" else ["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", "Titularisations", "Arrets_Totaux", "Pct_Arrets", "Arrets_7m", "Passes_D", "Sanctions_2m"]
st.dataframe(df_top[[c for c in cols_base if c in df_top.columns]].head(top_n), use_container_width=True)

# --- MODULE DE COMPARAISON MULTI-JOUEUSES (JUSQU'À 10) ---
st.markdown("---")
st.subheader("⚔️ Outil de Comparaison Directe (jusqu'à 10 joueuses)")

joueuses_compare = st.multiselect("Sélectionner jusqu'à 10 joueuses à superposer sur le radar :", df_working["Nom_Joueuse"].tolist(), max_selections=10)
ref_choice = st.radio("Ligne de référence en pointillés :", ["Moyenne Générale", "Top 10", "Top 20"], horizontal=True)

if joueuses_compare:
    categories = ['Assists', 'Buts (hors 7m)', '7m', 'Tirs Bloqués', 'Implication', 'Sanctions 2m']
    
    # Calcul de la ligne de référence choisie
    if ref_choice == "Top 10":
        sub_ref = df_working.sort_values(by="Buts", ascending=False).head(10)
    elif ref_choice == "Top 20":
        sub_ref = df_working.sort_values(by="Buts", ascending=False).head(20)
    else:
        sub_ref = df_working

    val_ref = [sub_ref['Passes_D'].mean(), sub_ref['Buts'].mean(), sub_ref['Buts_7m'].mean(), sub_ref['Tirs_Bloques'].mean(), sub_ref['Implication'].mean(), sub_ref['Sanctions_2m'].mean()]
    
    # Échelle max
    max_stat = max(max(val_ref), 1)
    for j in joueuses_compare:
        rj = df_working[df_working["Nom_Joueuse"] == j].iloc[0]
        max_stat = max(max_stat, rj['Passes_D'], rj['Buts'], rj['Buts_7m'], rj['Tirs_Bloques'], rj['Implication'], rj['Sanctions_2m'])

    angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
    angles_plot = angles + [angles[0]]
    va_plot = [(v / max_stat) * 70 + 15 for v in val_ref] + [(val_ref[0] / max_stat) * 70 + 15]

    fig, ax = plt.subplots(figsize=(7.5, 7.5), subplot_kw=dict(polar=True), facecolor='#0b0f19')
    ax.set_facecolor('#0b0f19')
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    plt.xticks(angles, categories, color='#f8fafc', size=9.5, fontweight='bold')
    plt.yticks([], [])
    plt.ylim(0, 115)
    ax.grid(color='#1e293b', linestyle='--', linewidth=0.8)

    # Tracé Référence
    ax.plot(angles_plot, va_plot, linewidth=1.8, linestyle='--', color='#94a3b8', label=f"{ref_choice}")

    # Palette 10 couleurs distinctes
    palette = ['#22c55e', '#38bdf8', '#f59e0b', '#ec4899', '#a855f7', '#14b8a6', '#f43f5e', '#84cc16', '#eab308', '#6366f1']
    for idx_c, j_nom in enumerate(joueuses_compare):
        row_j = df_working[df_working["Nom_Joueuse"] == j_nom].iloc[0]
        raw_j = [row_j['Passes_D'], row_j['Buts'], row_j['Buts_7m'], row_j['Tirs_Bloques'], row_j['Implication'], row_j['Sanctions_2m']]
        vj_plot = [(v / max_stat) * 70 + 15 for v in raw_j] + [(raw_j[0] / max_stat) * 70 + 15]
        col_j = palette[idx_c % len(palette)]
        ax.plot(angles_plot, vj_plot, linewidth=2.2, color=col_j, label=f"{j_nom} ({row_j['Pays']})")
        ax.scatter(angles, vj_plot[:-1], color=col_j, s=30)

    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), facecolor='#151c2c', edgecolor='#334155', labelcolor='white')
    st.pyplot(fig)

# --- CONSULTATION FICHE JOUEUSE EN 1 CLIC ---
st.markdown("---")
st.subheader("📋 Fiche Détaillée & Parcours Chronologique")
j_focus = st.selectbox("Sélectionner une joueuse pour afficher son profil complet :", df_working["Nom_Joueuse"].tolist())

if j_focus:
    rf = df_working[df_working["Nom_Joueuse"] == j_focus].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Poste Officiel", rf["Poste_Precis"])
    c2.metric("Club", rf["Club"])
    c3.metric("Taille & Âge", f"{int(rf['Taille'])} cm | {int(rf['Age'])} ans")
    c4.metric("Titularisations (S)", f"{int(rf['Titularisations'])} / {int(rf['Matchs_Joues'])}")

    st.markdown("**Chronologie des matchs disputés :**")
    m_player = df_raw[df_raw["Nom_Joueuse"] == j_focus].copy()
    
    # Ordre chronologique
    order_dict = {"Preliminary": 1, "Main": 2, "President": 2, "Quarter": 3, "Semi": 4, "Final": 5, "Placement": 5}
    m_player["Ordre"] = m_player["Phase"].apply(lambda x: next((v for k, v in order_dict.items() if k in str(x)), 3))
    m_player = m_player.sort_values(by="Ordre")

    cols_m = st.columns(len(m_player))
    for idx_m, (_, r_m) in enumerate(m_player.iterrows()):
        with cols_m[idx_m]:
            badge = "🟢 W" if r_m["Resultat"] == "W" else ("🟡 D" if r_m["Resultat"] == "D" else "🔴 L")
            st.caption(f"**Match {idx_m+1}**")
            st.write(f"vs **{r_m['Adversaire']}**")
            st.write(badge)
            st.caption(f"{r_m['Buts_Totaux']} buts | {r_m['Min_Jouees']} min")
