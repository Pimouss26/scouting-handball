import io
import os
import re
import unicodedata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Centre de Base de Données BBH", page_icon="🤾‍♀️", layout="wide")

# --- GESTION DE LA NAVIGATION ---
if "competition_active" not in st.session_state:
    st.session_state["competition_active"] = None

# --- PAGE D'ACCUEIL / PORTAIL BBH ---
if st.session_state["competition_active"] is None:
    st.markdown("""
        <style>
        .card-bbh {
            background: linear-gradient(135deg, rgba(225, 29, 72, 0.12), rgba(15, 23, 42, 0.75));
            border: 1.5px solid #e11d48;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            text-align: center;
        }
        .card-bbh h4 {
            color: #ffffff;
            margin: 0;
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        .stButton>button {
            border: 1px solid #e11d48 !important;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            border-color: #f43f5e !important;
            color: #f43f5e !important;
            box-shadow: 0 0 10px rgba(225, 29, 72, 0.35);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>⚫⚪ Centre de Base de Données BBH</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 1.1rem; margin-bottom: 35px;'>Plateforme Centrale de Performance & Détection — <span style='color: #f43f5e; font-weight: 600;'>Brest Bretagne Handball</span></p>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🌍 Sélections Nationales Jeunes")
        st.markdown('<div class="card-bbh"><h4>Championnat du Monde U18</h4></div>', unsafe_allow_html=True)
        if st.button("Accéder à la base U18 ➔", key="btn_u18", use_container_width=True):
            st.session_state["competition_active"] = "U18"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### 🏆 Coupes d'Europe (EHF)")
        st.markdown('<div class="card-bbh"><h4>EHF Champions League</h4></div>', unsafe_allow_html=True)
        if st.button("Accéder à l'EHF Champions League ➔", key="btn_cl", use_container_width=True):
            st.session_state["competition_active"] = "EHF CL"
            st.rerun()

    with col2:
        st.markdown("### 🇫🇷 Championnat de France")
        st.markdown('<div class="card-bbh"><h4>Ligue Butagaz Énergie (LBE)</h4></div>', unsafe_allow_html=True)
        if st.button("Accéder à la base LBE ➔", key="btn_lbe", use_container_width=True):
            st.session_state["competition_active"] = "LBE"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### 🇪🇺 European League")
        st.markdown('<div class="card-bbh"><h4>EHF European League</h4></div>', unsafe_allow_html=True)
        if st.button("Accéder à l'EHF European League ➔", key="btn_el", use_container_width=True):
            st.session_state["competition_active"] = "EHF EL"
            st.rerun()

    st.stop()

# --- CONFIGURATION DU FICHIER SELON LA COMPÉTITION ---
comp_active = st.session_state["competition_active"]

config_fichiers = {
    "U18": {"excel": "data_u18.xlsx", "titre": "Championnat du Monde U18", "has_3x3": True},
    "LBE": {"excel": "data_lbe.xlsx", "titre": "Ligue Butagaz Énergie", "has_3x3": False},
    "EHF CL": {"excel": "data_ehf_cl.xlsx", "titre": "EHF Champions League", "has_3x3": False},
    "EHF EL": {"excel": "data_ehf_el.xlsx", "titre": "EHF European League", "has_3x3": False}
}

info_comp = config_fichiers[comp_active]
EXCEL_FILE = info_comp["excel"]

# Repli automatique si data_u18.xlsx s'appelle encore data_handball.xlsx
if comp_active == "U18" and not os.path.exists(EXCEL_FILE) and os.path.exists("data_handball.xlsx"):
    EXCEL_FILE = "data_handball.xlsx"

# Bouton de retour au portail dans la barre latérale
if st.sidebar.button("⬅️ Retour au Centre BBH", use_container_width=True):
    st.session_state["competition_active"] = None
    st.rerun()

st.sidebar.markdown(f"**Compétition :** `{info_comp['titre']}`")
st.sidebar.markdown("---")

if not os.path.exists(EXCEL_FILE):
    st.title(f"🤾‍♀️ {info_comp['titre']}")
    st.warning(f"Le fichier `{EXCEL_FILE}` n'est pas encore présent sur le serveur.")
    st.info("Dépose le fichier Excel correspondant sur GitHub pour activer la consultation.")
    st.stop()

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data(fichier):
    df_raw = pd.read_excel(fichier, sheet_name="DATA_MATCHS").fillna(0)
    
    colonnes_requises = {
        "Nom_Joueuse": "Inconnu", "Competition": info_comp["titre"], "Type_Poste": "CHAMP",
        "Poste_Precis": "Non renseigné", "Pays": "Inconnu", "DOB": "-", "Age": 0, "Club": "Non renseigné",
        "Taille": 0, "Min_Jouees": 20, "Titulaire": 0, "Poule_Niveau": "Phase Régulière", "Phase": "-",
        "Adversaire": "Adversaire", "Resultat": "W",
        "Buts_Sans_7m": 0, "Buts_Totaux": 0, "Tirs_Totaux": 0,
        "Buts_6m": 0, "Tirs_6m": 0, "Buts_9m": 0, "Tirs_9m": 0,
        "Buts_Wing": 0, "Tirs_Wing": 0, "Buts_7m": 0, "Tirs_7m": 0,
        "Buts_FB": 0, "Tirs_FB": 0, "Buts_Brk": 0, "Tirs_Brk": 0, "Buts_LD": 0, "Tirs_LD": 0,
        "Passes_D": 0, "Tirs_Bloques": 0, "Sanctions_2min": 0, "Cartons_Rouges": 0,
        "Arrets_Totaux": 0, "Tirs_Subis": 0, "Arrets_6m": 0, "Tirs_6m_Subis": 0,
        "Arrets_9m": 0, "Tirs_9m_Subis": 0, "Arrets_Wing": 0, "Tirs_Wing_Subis": 0,
        "Arrets_7m": 0, "Tirs_7m_Subis": 0, "Arrets_FB": 0, "Tirs_FB_Subis": 0,
        "Arrets_Brk": 0, "Tirs_Brk_Subis": 0, "Arrets_LD": 0, "Tirs_LD_Subis": 0
    }
    
    for col, default_val in colonnes_requises.items():
        if col not in df_raw.columns:
            df_raw[col] = default_val

    def get_valid_first(series):
        for v in series:
            s_v = str(v).strip()
            if s_v not in ["0", "0.0", "nan", "-", "None", ""]:
                return s_v
        return "-"

    df_grouped = df_raw.groupby(["Nom_Joueuse", "Competition"], as_index=False).agg({
        "Type_Poste": "first", "Poste_Precis": "first", "Pays": "first",
        "DOB": get_valid_first, "Age": "max", "Club": get_valid_first, "Taille": "max",
        "Min_Jouees": ["count", "sum"], "Titulaire": "sum",
        "Buts_Sans_7m": "sum", "Buts_Totaux": "sum", "Tirs_Totaux": "sum",
        "Buts_6m": "sum", "Tirs_6m": "sum",
        "Buts_9m": "sum", "Tirs_9m": "sum",
        "Buts_Wing": "sum", "Tirs_Wing": "sum",
        "Buts_7m": "sum", "Tirs_7m": "sum",
        "Buts_FB": "sum", "Tirs_FB": "sum",
        "Buts_Brk": "sum", "Tirs_Brk": "sum",
        "Buts_LD": "sum", "Tirs_LD": "sum",
        "Passes_D": "sum", "Tirs_Bloques": "sum", "Sanctions_2min": "sum", "Cartons_Rouges": "sum",
        "Arrets_Totaux": "sum", "Tirs_Subis": "sum",
        "Arrets_6m": "sum", "Tirs_6m_Subis": "sum",
        "Arrets_9m": "sum", "Tirs_9m_Subis": "sum",
        "Arrets_Wing": "sum", "Tirs_Wing_Subis": "sum",
        "Arrets_7m": "sum", "Tirs_7m_Subis": "sum",
        "Arrets_FB": "sum", "Tirs_FB_Subis": "sum",
        "Arrets_Brk": "sum", "Tirs_Brk_Subis": "sum",
        "Arrets_LD": "sum", "Tirs_LD_Subis": "sum"
    })
    
    df_grouped.columns = [
        "Nom_Joueuse", "Competition", "Type_Poste", "Poste_Precis", "Pays",
        "DOB", "Age", "Club", "Taille", "Matchs_Joues", "Min_Totales", "Titularisations",
        "Buts", "Buts_Totaux", "Tirs_Totaux",
        "Buts_6m", "Tirs_6m", "Buts_9m", "Tirs_9m",
        "Buts_Wing", "Tirs_Wing", "Buts_7m", "Tirs_7m",
        "Buts_FB", "Tirs_FB", "Buts_Brk", "Tirs_Brk", "Buts_LD", "Tirs_LD",
        "Passes_D", "Tirs_Bloques", "Sanctions_2m", "Cartons_Rouges",
        "Arrets_Totaux", "Tirs_Subis",
        "Arrets_6m", "Tirs_6m_Subis", "Arrets_9m", "Tirs_9m_Subis",
        "Arrets_Wing", "Tirs_Wing_Subis", "Arrets_7m", "Tirs_7m_Subis",
        "Arrets_FB", "Tirs_FB_Subis", "Arrets_Brk", "Tirs_Brk_Subis",
        "Arrets_LD", "Tirs_LD_Subis"
    ]
    
    df_grouped["Tirs_Hors_7m"] = np.maximum(df_grouped["Tirs_Totaux"] - df_grouped["Tirs_7m"], df_grouped["Buts"])

    df_grouped["Pct_Hors_7m"] = np.where(df_grouped["Tirs_Hors_7m"] > 0, (df_grouped["Buts"] / df_grouped["Tirs_Hors_7m"]) * 100, 0).round(1)
    df_grouped["Pct_Global_Tir"] = np.where(df_grouped["Tirs_Totaux"] > 0, (df_grouped["Buts_Totaux"] / df_grouped["Tirs_Totaux"]) * 100, 0).round(1)
    df_grouped["Pct_6m"] = np.where(df_grouped["Tirs_6m"] > 0, (df_grouped["Buts_6m"] / df_grouped["Tirs_6m"]) * 100, 0).round(1)
    df_grouped["Pct_9m"] = np.where(df_grouped["Tirs_9m"] > 0, (df_grouped["Buts_9m"] / df_grouped["Tirs_9m"]) * 100, 0).round(1)
    df_grouped["Pct_Wing"] = np.where(df_grouped["Tirs_Wing"] > 0, (df_grouped["Buts_Wing"] / df_grouped["Tirs_Wing"]) * 100, 0).round(1)
    df_grouped["Pct_7m"] = np.where(df_grouped["Tirs_7m"] > 0, (df_grouped["Buts_7m"] / df_grouped["Tirs_7m"]) * 100, 0).round(1)
    df_grouped["Pct_FB"] = np.where(df_grouped["Tirs_FB"] > 0, (df_grouped["Buts_FB"] / df_grouped["Tirs_FB"]) * 100, 0).round(1)
    df_grouped["Pct_Brk"] = np.where(df_grouped["Tirs_Brk"] > 0, (df_grouped["Buts_Brk"] / df_grouped["Tirs_Brk"]) * 100, 0).round(1)
    df_grouped["Pct_LD"] = np.where(df_grouped["Tirs_LD"] > 0, (df_grouped["Buts_LD"] / df_grouped["Tirs_LD"]) * 100, 0).round(1)

    df_grouped["Pct_Arrets_Totaux"] = np.where(df_grouped["Tirs_Subis"] > 0, (df_grouped["Arrets_Totaux"] / df_grouped["Tirs_Subis"]) * 100, 0).round(1)
    df_grouped["Pct_Arr_6m"] = np.where(df_grouped["Tirs_6m_Subis"] > 0, (df_grouped["Arrets_6m"] / df_grouped["Tirs_6m_Subis"]) * 100, 0).round(1)
    df_grouped["Pct_Arr_9m"] = np.where(df_grouped["Tirs_9m_Subis"] > 0, (df_grouped["Arrets_9m"] / df_grouped["Tirs_9m_Subis"]) * 100, 0).round(1)
    df_grouped["Pct_Arr_Wing"] = np.where(df_grouped["Tirs_Wing_Subis"] > 0, (df_grouped["Arrets_Wing"] / df_grouped["Tirs_Wing_Subis"]) * 100, 0).round(1)
    df_grouped["Pct_Arr_7m"] = np.where(df_grouped["Tirs_7m_Subis"] > 0, (df_grouped["Arrets_7m"] / df_grouped["Tirs_7m_Subis"]) * 100, 0).round(1)
    df_grouped["Pct_Arr_FB"] = np.where(df_grouped["Tirs_FB_Subis"] > 0, (df_grouped["Arrets_FB"] / df_grouped["Tirs_FB_Subis"]) * 100, 0).round(1)
    df_grouped["Pct_Arr_Brk"] = np.where(df_grouped["Tirs_Brk_Subis"] > 0, (df_grouped["Arrets_Brk"] / df_grouped["Tirs_Brk_Subis"]) * 100, 0).round(1)
    df_grouped["Pct_Arr_LD"] = np.where(df_grouped["Tirs_LD_Subis"] > 0, (df_grouped["Arrets_LD"] / df_grouped["Tirs_LD_Subis"]) * 100, 0).round(1)

    def format_stat_ratio(reussis, totaux, pct):
        return [f"{int(r)}/{int(t)} ({p:.1f} %)" if t > 0 else f"{int(r)}/0 (0 %)" for r, t, p in zip(reussis, totaux, pct)]

    df_grouped["Stat_Buts_Hors_7m"] = format_stat_ratio(df_grouped["Buts"], df_grouped["Tirs_Hors_7m"], df_grouped["Pct_Hors_7m"])
    df_grouped["Stat_Global_Tir"] = format_stat_ratio(df_grouped["Buts_Totaux"], df_grouped["Tirs_Totaux"], df_grouped["Pct_Global_Tir"])
    df_grouped["Stat_6m"] = format_stat_ratio(df_grouped["Buts_6m"], df_grouped["Tirs_6m"], df_grouped["Pct_6m"])
    df_grouped["Stat_9m"] = format_stat_ratio(df_grouped["Buts_9m"], df_grouped["Tirs_9m"], df_grouped["Pct_9m"])
    df_grouped["Stat_Wing"] = format_stat_ratio(df_grouped["Buts_Wing"], df_grouped["Tirs_Wing"], df_grouped["Pct_Wing"])
    df_grouped["Stat_7m"] = format_stat_ratio(df_grouped["Buts_7m"], df_grouped["Tirs_7m"], df_grouped["Pct_7m"])
    df_grouped["Stat_FB"] = format_stat_ratio(df_grouped["Buts_FB"], df_grouped["Tirs_FB"], df_grouped["Pct_FB"])
    df_grouped["Stat_Brk"] = format_stat_ratio(df_grouped["Buts_Brk"], df_grouped["Tirs_Brk"], df_grouped["Pct_Brk"])
    df_grouped["Stat_LD"] = format_stat_ratio(df_grouped["Buts_LD"], df_grouped["Tirs_LD"], df_grouped["Pct_LD"])

    df_grouped["Stat_Global_Arrets"] = format_stat_ratio(df_grouped["Arrets_Totaux"], df_grouped["Tirs_Subis"], df_grouped["Pct_Arrets_Totaux"])
    df_grouped["Stat_Arr_6m"] = format_stat_ratio(df_grouped["Arrets_6m"], df_grouped["Tirs_6m_Subis"], df_grouped["Pct_Arr_6m"])
    df_grouped["Stat_Arr_9m"] = format_stat_ratio(df_grouped["Arrets_9m"], df_grouped["Tirs_9m_Subis"], df_grouped["Pct_Arr_9m"])
    df_grouped["Stat_Arr_Wing"] = format_stat_ratio(df_grouped["Arrets_Wing"], df_grouped["Tirs_Wing_Subis"], df_grouped["Pct_Arr_Wing"])
    df_grouped["Stat_Arr_7m"] = format_stat_ratio(df_grouped["Arrets_7m"], df_grouped["Tirs_7m_Subis"], df_grouped["Pct_Arr_7m"])
    df_grouped["Stat_Arr_FB"] = format_stat_ratio(df_grouped["Arrets_FB"], df_grouped["Tirs_FB_Subis"], df_grouped["Pct_Arr_FB"])
    df_grouped["Stat_Arr_Brk"] = format_stat_ratio(df_grouped["Arrets_Brk"], df_grouped["Tirs_Brk_Subis"], df_grouped["Pct_Arr_Brk"])
    df_grouped["Stat_Arr_LD"] = format_stat_ratio(df_grouped["Arrets_LD"], df_grouped["Tirs_LD_Subis"], df_grouped["Pct_Arr_LD"])

    df_grouped["Implication"] = df_grouped["Buts"] + df_grouped["Buts_7m"] + df_grouped["Passes_D"]
    df_grouped["Buts_PM"] = (df_grouped["Buts"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["PassesD_PM"] = (df_grouped["Passes_D"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["Impl_PM"] = (df_grouped["Implication"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["Arrets_PM"] = (df_grouped["Arrets_Totaux"] / df_grouped["Matchs_Joues"]).round(1)

    def extraire_annee(val_dob):
        s = str(val_dob).strip()
        if len(s) >= 4 and s[-4:].isdigit():
            return int(s[-4:])
        return None

    df_grouped["Annee_Naissance"] = df_grouped["DOB"].apply(extraire_annee)

    return df_raw, df_grouped

df_raw, df = load_data(EXCEL_FILE)

st.title(f"🤾‍♀️ Hub Scouting — {info_comp['titre']}")

if df.empty:
    st.warning("Aucune donnée disponible.")
    st.stop()

# --- FILTRES LATÉRAUX ---
st.sidebar.header("🎯 Filtres de Recherche")
label_equipe = "Équipe / Club" if comp_active == "LBE" else "Pays / Sélections"
all_pays = sorted([p for p in df["Pays"].unique() if str(p) not in ["0", "Inconnu", "0.0"]])
selected_pays = st.sidebar.multiselect(label_equipe, all_pays, default=[])

annees_dispos = sorted([int(a) for a in df["Annee_Naissance"].dropna().unique() if a > 1980])
if annees_dispos:
    selected_annees = st.sidebar.multiselect("Année(s) de naissance", annees_dispos, default=[])
else:
    selected_annees = []

poule_filter = st.sidebar.selectbox("Phase / Tableau", ["Toutes", "Poule Haute (Main Round / Finales)", "Poule Basse (President's Cup)"])
type_poste_sel = st.sidebar.selectbox("Catégorie de Poste", ["Tous", "CHAMP", "GARDIENNE"])

postes_uniques = sorted([p for p in df["Poste_Precis"].unique() if str(p) not in ["Non renseigné", "0", "0.0"]])
selected_postes = st.sidebar.multiselect("Poste(s) précis", postes_uniques, default=[])

max_m = int(df["Matchs_Joues"].max()) if not df.empty else 1
min_matchs = st.sidebar.slider("Matchs joués min.", 1, max(max_m, 1), 1)

df_w = df.copy()
if poule_filter != "Toutes":
    tag = "Poule Haute" if "Haute" in poule_filter else "Poule Basse"
    j_poule = df_raw[df_raw["Poule_Niveau"] == tag]["Nom_Joueuse"].unique()
    df_w = df_w[df_w["Nom_Joueuse"].isin(j_poule)]

if selected_pays:
    df_w = df_w[df_w["Pays"].isin(selected_pays)]
if selected_annees:
    df_w = df_w[df_w["Annee_Naissance"].isin(selected_annees)]
if type_poste_sel != "Tous":
    df_w = df_w[df_w["Type_Poste"] == type_poste_sel]
if selected_postes:
    df_w = df_w[df_w["Poste_Precis"].isin(selected_postes)]
df_w = df_w[df_w["Matchs_Joues"] >= min_matchs]

# --- CRITÈRES & SECTEURS ---
st.sidebar.header("📊 Critères & Secteurs")

if type_poste_sel == "GARDIENNE":
    criteres = {"Arrêts Totaux": ("Arrets_Totaux", "Pct_Arrets_Totaux"), "Arrêts / Match": ("Arrets_PM", "Pct_Arrets_Totaux"), "Relances (Passes D)": ("Passes_D", "Passes_D")}
    tri_choisi = st.sidebar.selectbox("Classer par", list(criteres.keys()))
    
    if info_comp["has_3x3"]:
        secteur_choisi = st.sidebar.selectbox("🎯 Secteur d'arrêt prioritaire", ["Tous", "Arrêts 6m", "Arrêts 9m", "Arrêts Wing", "Arrêts 7m", "Arrêts FB (Contre-attaque)", "Arrêts Brk (Percée)", "Arrêts LD (Cage vide)"])
    else:
        secteur_choisi = "Tous"
    
    mapping_secteurs = {
        "Arrêts 6m": ("Arrets_6m", "Pct_Arr_6m", "Stat_Arr_6m", "Arrêts 6m (Ratio %)"),
        "Arrêts 9m": ("Arrets_9m", "Pct_Arr_9m", "Stat_Arr_9m", "Arrêts 9m (Ratio %)"),
        "Arrêts Wing": ("Arrets_Wing", "Pct_Arr_Wing", "Stat_Arr_Wing", "Arrêts Wing (Ratio %)"),
        "Arrêts 7m": ("Arrets_7m", "Pct_Arr_7m", "Stat_Arr_7m", "Arrêts 7m (Ratio %)"),
        "Arrêts FB (Contre-attaque)": ("Arrets_FB", "Pct_Arr_FB", "Stat_Arr_FB", "Arrêts FB (Ratio %)"),
        "Arrêts Brk (Percée)": ("Arrets_Brk", "Pct_Arr_Brk", "Stat_Arr_Brk", "Arrêts Brk (Ratio %)"),
        "Arrêts LD (Cage vide)": ("Arrets_LD", "Pct_Arr_LD", "Stat_Arr_LD", "Arrêts LD (Ratio %)")
    }
else:
    criteres = {"Buts (Hors 7m)": ("Buts", "Pct_Hors_7m"), "Buts par Match": ("Buts_PM", "Pct_Hors_7m"), "Implication Totale": ("Implication", "Implication"), "Buts sur 7m": ("Buts_7m", "Pct_7m"), "Assists": ("Passes_D", "Passes_D")}
    tri_choisi = st.sidebar.selectbox("Classer par", list(criteres.keys()))
    
    if info_comp["has_3x3"]:
        secteur_choisi = st.sidebar.selectbox("🎯 Secteur de tir prioritaire", ["Tous", "Secteur 6m", "Secteur 9m", "Secteur Wing (Ailes)", "Secteur 7m", "Contre-attaque (FB)", "Percée (Brk)", "Buts Cage Vide (LD)"])
    else:
        secteur_choisi = "Tous"
    
    mapping_secteurs = {
        "Secteur 6m": ("Buts_6m", "Pct_6m", "Stat_6m", "Buts 6m (Ratio %)"),
        "Secteur 9m": ("Buts_9m", "Pct_9m", "Stat_9m", "Buts 9m (Ratio %)"),
        "Secteur Wing (Ailes)": ("Buts_Wing", "Pct_Wing", "Stat_Wing", "Buts Wing (Ratio %)"),
        "Secteur 7m": ("Buts_7m", "Pct_7m", "Stat_7m", "Buts 7m (Ratio %)"),
        "Contre-attaque (FB)": ("Buts_FB", "Pct_FB", "Stat_FB", "Buts FB (Ratio %)"),
        "Percée (Brk)": ("Buts_Brk", "Pct_Brk", "Stat_Brk", "Buts Brk (Ratio %)"),
        "Buts Cage Vide (LD)": ("Buts_LD", "Pct_LD", "Stat_LD", "Buts LD (Ratio %)")
    }

mode_tri = st.sidebar.radio("Type de classement :", ["Par Volume (Quantité)", "Par Efficacité (Meilleur Ratio %)"], horizontal=True)

if secteur_choisi != "Tous":
    col_vol, col_pct, col_stat_txt, nom_col_affiche = mapping_secteurs[secteur_choisi]
    col_tri_active = col_pct if "Efficacité" in mode_tri else col_vol
    df_top = df_w.sort_values(by=col_tri_active, ascending=False).reset_index(drop=True)
else:
    col_vol, col_pct = criteres[tri_choisi]
    col_tri_active = col_pct if "Efficacité" in mode_tri else col_vol
    df_top = df_w.sort_values(by=col_tri_active, ascending=False).reset_index(drop=True)

top_n = st.sidebar.slider("Afficher le Top :", 5, 50, 15)
df_top.index += 1

if type_poste_sel == "GARDIENNE":
    if secteur_choisi != "Tous":
        cols_tableau = ["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", col_stat_txt, "Stat_Global_Arrets", "Passes_D", "Sanctions_2m"]
        df_display = df_top[cols_tableau].rename(columns={col_stat_txt: nom_col_affiche, "Stat_Global_Arrets": "Arrêts Totaux (Ratio %)"})
    else:
        cols_tableau = ["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", "Stat_Global_Arrets", "Stat_Arr_7m", "Passes_D", "Sanctions_2m"]
        df_display = df_top[cols_tableau].rename(columns={"Stat_Global_Arrets": "Arrêts Totaux (Ratio %)", "Stat_Arr_7m": "Arrêts 7m (Ratio %)"})
else:
    if secteur_choisi != "Tous":
        cols_tableau = ["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", col_stat_txt, "Stat_Buts_Hors_7m", "Stat_Global_Tir", "Passes_D", "Implication", "Sanctions_2m"]
        df_display = df_top[cols_tableau].rename(columns={col_stat_txt: nom_col_affiche, "Stat_Buts_Hors_7m": "Buts hors 7m (Ratio %)", "Stat_Global_Tir": "Tirs Totaux (Ratio %)"})
    else:
        cols_tableau = ["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", "Stat_Buts_Hors_7m", "Stat_7m", "Stat_Global_Tir", "Passes_D", "Implication", "Sanctions_2m"]
        df_display = df_top[cols_tableau].rename(columns={"Stat_Buts_Hors_7m": "Buts hors 7m (Ratio %)", "Stat_7m": "7m (Ratio %)", "Stat_Global_Tir": "Tirs Totaux (Ratio %)"})

st.subheader(f"🏆 Classement — {secteur_choisi if secteur_choisi != 'Tous' else tri_choisi} ({'Meilleur Ratio %' if 'Efficacité' in mode_tri else 'Plus grand nombre'})")
st.dataframe(df_display.head(top_n), use_container_width=True)

# --- COMPARATEUR MULTI-JOUEUSES ---
st.markdown("---")
st.subheader("⚔️ Outil de Comparaison Directe (jusqu'à 10 joueuses)")

all_j_names = df_w["Nom_Joueuse"].tolist()

if "ms_selection_compare" not in st.session_state:
    st.session_state["ms_selection_compare"] = all_j_names[:2] if len(all_j_names) >= 2 else []

def callback_ajouter_joueuse():
    choix = st.session_state.get("cand_comp_select", "")
    if choix and choix != "Aucun résultat":
        courant = list(st.session_state.get("ms_selection_compare", []))
        if choix not in courant:
            if len(courant) < 10:
                courant.append(choix)
                st.session_state["ms_selection_compare"] = courant

def callback_vider_selection():
    st.session_state["ms_selection_compare"] = []

c_rech1, c_rech2, c_btn1, c_btn2 = st.columns([1.6, 1.6, 0.8, 0.8])
with c_rech1:
    txt_rech_comp = st.text_input("🔍 Rechercher une joueuse par nom/pays :", "", key="rech_comp_input")

with c_rech2:
    if txt_rech_comp:
        candidats = [j for j in all_j_names if txt_rech_comp.lower() in j.lower()]
    else:
        candidats = all_j_names
    st.selectbox("Joueuse trouvée :", candidats if candidats else ["Aucun résultat"], key="cand_comp_select")

with c_btn1:
    st.write("")
    st.write("")
    st.button("➕ Ajouter", on_click=callback_ajouter_joueuse, key="btn_add_player")

with c_btn2:
    st.write("")
    st.write("")
    st.button("🗑️ Vider", on_click=callback_vider_selection, key="btn_clear_players")

col_sel_c, col_ref_c = st.columns([2, 1])
with col_sel_c:
    selected_comp = st.multiselect(
        "Joueuses actuellement comparées :",
        all_j_names,
        key="ms_selection_compare",
        max_selections=10
    )

with col_ref_c:
    ref_choice = st.radio("Ligne de référence :", ["Moyenne Générale", "Top 10", "Top 20"], horizontal=True, key="ref_choice_radio")

if selected_comp:
    cat_comp = ['Assists', 'Buts (hors 7m)', '7m', 'Tirs Bloqués', 'Implication']
    sub_ref = df_w.sort_values(by="Buts", ascending=False).head(10 if ref_choice == "Top 10" else (20 if ref_choice == "Top 20" else len(df_w)))
    val_ref = [sub_ref['Passes_D'].mean(), sub_ref['Buts'].mean(), sub_ref['Buts_7m'].mean(), sub_ref['Tirs_Bloques'].mean(), sub_ref['Implication'].mean()]
    
    max_val = max(max(val_ref), 1)
    for j in selected_comp:
        sub_j = df_w[df_w["Nom_Joueuse"] == j]
        if not sub_j.empty:
            rj = sub_j.iloc[0]
            max_val = max(max_val, rj['Passes_D'], rj['Buts'], rj['Buts_7m'], rj['Tirs_Bloques'], rj['Implication'])

    ang = [n / float(len(cat_comp)) * 2 * np.pi for n in range(len(cat_comp))]
    ang_p = ang + [ang[0]]

    fig, ax = plt.subplots(figsize=(5.2, 5.2), subplot_kw=dict(polar=True), facecolor='#0b0f19')
    ax.set_facecolor('#0b0f19')
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    plt.xticks(ang, cat_comp, color='#f8fafc', size=9.5, fontweight='bold')
    plt.yticks([], [])
    plt.ylim(0, 125)
    ax.grid(color='#1e293b', linestyle='--', linewidth=0.8)

    va_p = [(v / max_val) * 70 + 18 for v in val_ref] + [(val_ref[0] / max_val) * 70 + 18]
    ax.plot(ang_p, va_p, linewidth=1.8, linestyle='--', color='#94a3b8', label=f"{ref_choice}")
    ax.scatter(ang, va_p[:-1], color='#94a3b8', s=30, zorder=4)

    pal = ['#22c55e', '#38bdf8', '#f59e0b', '#ec4899', '#a855f7', '#14b8a6', '#f43f5e', '#84cc16', '#eab308', '#6366f1']
    
    for i, j_nom in enumerate(selected_comp):
        sub_j = df_w[df_w["Nom_Joueuse"] == j_nom]
        if sub_j.empty:
            continue
        rj = sub_j.iloc[0]
        raw_vals = [rj['Passes_D'], rj['Buts'], rj['Buts_7m'], rj['Tirs_Bloques'], rj['Implication']]
        v_plot = [(v / max_val) * 70 + 18 for v in raw_vals]
        col = pal[i % len(pal)]
        ax.plot(ang_p, v_plot + [v_plot[0]], linewidth=2.0, color=col, label=f"{j_nom} ({rj['Pays']})")
        ax.scatter(ang, v_plot, color=col, s=30, zorder=5)

    col_chart, col_leg_tab = st.columns([1.1, 1.2])
    with col_chart:
        st.pyplot(fig)
    with col_leg_tab:
        st.markdown("##### 🔢 Tableau Comparatif Direct")
        df_comp_tab = df_w[df_w["Nom_Joueuse"].isin(selected_comp)][["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", "Stat_Buts_Hors_7m", "Stat_7m", "Passes_D", "Implication", "Tirs_Bloques", "Sanctions_2m"]].reset_index(drop=True)
        df_comp_tab.columns = ["Joueuse", label_equipe, "Poste", "Matchs", "Buts (hors 7m)", "7m", "Assists", "Implication", "Contres", "2m"]
        st.dataframe(df_comp_tab, use_container_width=True)

# --- FICHE JOUEUSE ---
st.markdown("---")
st.subheader("📋 Fiche Joueuse Complète")

c_rf1, c_rf2 = st.columns([1.5, 2])
with c_rf1:
    txt_rech_fiche = st.text_input("🔍 Rechercher une joueuse :", "", key="rech_fiche_input")

with c_rf2:
    if txt_rech_fiche:
        options_fiche = [j for j in all_j_names if txt_rech_fiche.lower() in j.lower()]
    else:
        options_fiche = all_j_names
    
    j_sel = st.selectbox("Sélectionner le profil à afficher :", options_fiche if options_fiche else all_j_names, key="select_fiche_joueuse")

if j_sel:
    sub_rf = df_w[df_w["Nom_Joueuse"] == j_sel]
    if not sub_rf.empty:
        rf = sub_rf.iloc[0]
        raw_sub = df_raw[df_raw["Nom_Joueuse"] == j_sel]
        dob_cands = [str(d).strip() for d in raw_sub["DOB"] if str(d).strip() not in ["0", "0.0", "nan", "-", "None", ""]]
        dob_raw = dob_cands[0] if dob_cands else (str(rf["DOB"]).strip() if str(rf["DOB"]).strip() not in ["0", "0.0", "nan", "-", "None", ""] else "")
        
        age_val = int(rf['Age']) if rf['Age'] > 0 else 0
        if dob_raw and age_val > 0:
            age_str = f"{age_val} ans (DOB: {dob_raw})"
        elif dob_raw:
            age_str = f"DOB: {dob_raw}"
        elif age_val > 0:
            age_str = f"{age_val} ans"
        else:
            age_str = "Âge / DOB N/A"

        taille_txt = f"{int(rf['Taille'])} cm" if rf['Taille'] > 0 else "Taille N/A"
        
        st.markdown(f"### **{j_sel}** — {rf['Pays']}")
        st.markdown(f"**Poste :** `{rf['Poste_Precis']}` | **Club :** `{rf['Club']}` | **Physique & Âge :** `{taille_txt} — {age_str}`")

        st.markdown("#### 📅 Parcours Match par Match")
        m_player = raw_sub.copy()

        cols_m = st.columns(max(len(m_player), 1))
        for idx_m, (_, r_m) in enumerate(m_player.iterrows()):
            with cols_m[idx_m]:
                badge = "🟢 W" if r_m["Resultat"] == "W" else ("🟡 D" if r_m["Resultat"] == "D" else "🔴 L")
                st.caption(f"**{r_m['Phase']}**")
                st.write(f"vs **{r_m['Adversaire']}**")
                st.write(badge)
                st.caption(f"{r_m['Buts_Totaux']} buts | {r_m['Min_Jouees']} min")

        st.markdown("#### 📊 Indicateurs & KPIs")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Buts (Hors 7m)", rf["Stat_Buts_Hors_7m"], f"{rf['Buts_PM']} / match")
        k2.metric("Secteur 7m", rf["Stat_7m"])
        k3.metric("Assists", f"{int(rf['Passes_D'])}", f"{rf['PassesD_PM']} / match")
        k4.metric("Implication", f"{int(rf['Implication'])}", f"{rf['Impl_PM']} / match")

# --- MODULE CAGE 3x3 (Uniquement si disponible pour la compétition) ---
if info_comp["has_3x3"]:
    st.markdown("---")
    st.subheader("🥅 Secteurs d'Arrêt Gardiennes — Cartographie 3x3")

    def load_cages_data(fichier):
        if not os.path.exists(fichier):
            return pd.DataFrame(), f"Le fichier '{fichier}' est introuvable."
        try:
            df_c = pd.read_excel(fichier, sheet_name="SECTEURS_GARDIENNES").fillna("0/0")
            return df_c, None
        except Exception as e:
            return pd.DataFrame(), f"Erreur de lecture de l'onglet SECTEURS_GARDIENNES : {e}"

    df_cages, err_cages = load_cages_data(EXCEL_FILE)

    if err_cages:
        st.error(f"⚠️ {err_cages}")
    elif df_cages.empty:
        st.info("Données de secteurs de cage indisponibles.")
    else:
        df_paires = df_cages[["Nom_Joueuse", "Pays"]].drop_duplicates().sort_values(by=["Pays", "Nom_Joueuse"])
        
        c_gks1, c_gks2 = st.columns([1.5, 2])
        with c_gks1:
            rech_gk_txt = st.text_input("🔍 Rechercher une gardienne (Nom ou Pays) :", "", key="rech_gk_cage")
        
        with c_gks2:
            if rech_gk_txt:
                term = rech_gk_txt.strip().lower()
                df_filtre = df_paires[
                    df_paires["Nom_Joueuse"].astype(str).str.lower().str.contains(term) | 
                    df_paires["Pays"].astype(str).str.lower().str.contains(term)
                ]
            else:
                df_filtre = df_paires

            options_gk = [f"{row['Nom_Joueuse']} ({row['Pays']})" for _, row in df_filtre.iterrows()]
            
            if not options_gk:
                st.warning("Aucune gardienne trouvée pour cette recherche.")
                gk_selectionnee_label = None
            else:
                gk_selectionnee_label = st.selectbox("Sélectionner la gardienne :", options_gk)

        if gk_selectionnee_label:
            nom_gk_choisi = gk_selectionnee_label.rsplit(" (", 1)[0]
            pays_gk_choisi = gk_selectionnee_label.rsplit(" (", 1)[1].rstrip(")")

            df_gk = df_cages[(df_cages["Nom_Joueuse"] == nom_gk_choisi) & (df_cages["Pays"] == pays_gk_choisi)]
            
            zones_cles = [
                ("Haut_Gauche", "Haut_Centre", "Haut_Droit"),
                ("Milieu_Gauche", "Milieu_Centre", "Milieu_Droit"),
                ("Bas_Gauche", "Bas_Centre", "Bas_Droit")
            ]
            
            matrice_stats = []
            tot_arrets = 0
            tot_tirs = 0

            for ligne in zones_cles:
                ligne_stats = []
                for col_cle in ligne:
                    arr_zone = 0
                    tir_zone = 0
                    for val in df_gk[col_cle]:
                        m = re.match(r"^(\d+)/(\d+)", str(val).strip())
                        if m:
                            arr_zone += int(m.group(1))
                            tir_zone += int(m.group(2))
                    
                    pct = (arr_zone / tir_zone * 100) if tir_zone > 0 else 0.0
                    tot_arrets += arr_zone
                    tot_tirs += tir_zone
                    ligne_stats.append((arr_zone, tir_zone, pct))
                matrice_stats.append(ligne_stats)

            pct_global_gk = (tot_arrets / tot_tirs * 100) if tot_tirs > 0 else 0.0

            st.markdown(f"#### **{nom_gk_choisi}** — {pays_gk_choisi}")
            st.caption(f"Efficacité globale sur les tirs cadrés : **{tot_arrets}/{tot_tirs} ({pct_global_gk:.1f} %)**")

            fig_cage, ax_c = plt.subplots(figsize=(6.5, 4.5), facecolor='#0b0f19')
            ax_c.set_facecolor('#0b0f19')

            for r_idx in range(3):
                for c_idx in range(3):
                    arr, tir, p = matrice_stats[r_idx][c_idx]
                    
                    if tir == 0:
                        bg_color = '#1e293b'
                    elif p >= 40:
                        bg_color = '#065f46'
                    elif p >= 25:
                        bg_color = '#0e7490'
                    elif p >= 15:
                        bg_color = '#b45309'
                    else:
                        bg_color = '#991b1b'

                    rect = plt.Rectangle((c_idx, 2 - r_idx), 1, 1, facecolor=bg_color, edgecolor='#f8fafc', linewidth=2, alpha=0.85)
                    ax_c.add_patch(rect)

                    ax_c.text(c_idx + 0.5, 2 - r_idx + 0.62, f"{arr}/{tir}", color='white', fontsize=12, fontweight='bold', ha='center', va='center')
                    ax_c.text(c_idx + 0.5, 2 - r_idx + 0.38, f"{p:.1f} %", color='#fef08a' if p >= 30 else '#e2e8f0', fontsize=10.5, fontweight='bold', ha='center', va='center')

        cadre_exterieur = plt.Rectangle((0, 0), 3, 3, fill=False, edgecolor='#ef4444', linewidth=6)
        ax_c.add_patch(cadre_exterieur)

        ax_c.set_xlim(-0.1, 3.1)
        ax_c.set_ylim(-0.1, 3.1)
        ax_c.axis('off')

        c_view1, c_view2 = st.columns([1.3, 1])
        with c_view1:
            st.pyplot(fig_cage)
        with c_view2:
            st.markdown("##### 📌 Légende & Performance par Hauteur")
            
            haut_arr = sum(matrice_stats[0][i][0] for i in range(3))
            haut_tir = sum(matrice_stats[0][i][1] for i in range(3))
            
            mil_arr = sum(matrice_stats[1][i][0] for i in range(3))
            mil_tir = sum(matrice_stats[1][i][1] for i in range(3))
            
            bas_arr = sum(matrice_stats[2][i][0] for i in range(3))
            bas_tir = sum(matrice_stats[2][i][1] for i in range(3))

            st.metric("Secteur Haut (Lucarnes / Tête)", f"{haut_arr}/{haut_tir}", f"{(haut_arr/haut_tir*100) if haut_tir>0 else 0:.1f} %")
            st.metric("Secteur Milieu (Hanches / Rebonds)", f"{mil_arr}/{mil_tir}", f"{(mil_arr/mil_tir*100) if mil_tir>0 else 0:.1f} %")
            st.metric("Secteur Bas (Pieds)", f"{bas_arr}/{bas_tir}", f"{(bas_arr/bas_tir*100) if bas_tir>0 else 0:.1f} %")
