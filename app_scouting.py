import io
import os
import re
import unicodedata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Hub Scouting Handball U18", page_icon="🤾‍♀️", layout="wide")

EXCEL_FILE = "data_handball.xlsx"

@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame(), pd.DataFrame()
    
    df_raw = pd.read_excel(EXCEL_FILE, sheet_name="DATA_MATCHS").fillna(0)
    
    colonnes_requises = {
        "Nom_Joueuse": "Inconnu", "Competition": "Championnat du monde U18", "Type_Poste": "CHAMP",
        "Poste_Precis": "Non renseigné", "Pays": "Inconnu", "DOB": "-", "Age": 0, "Club": "Non renseigné",
        "Taille": 0, "Min_Jouees": 20, "Titulaire": 0, "Poule_Niveau": "Poule Haute", "Phase": "-",
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

    return df_raw, df_grouped

df_raw, df = load_data()

st.title("🤾‍♀️ Hub de Détection & Scouting Handball U18")

if df.empty:
    st.warning("Données indisponibles.")
    st.stop()

# --- FILTRES LATÉRAUX ---
st.sidebar.header("🎯 Filtres de Recherche")
all_pays = sorted([p for p in df["Pays"].unique() if str(p) not in ["0", "Inconnu", "0.0"]])
selected_pays = st.sidebar.multiselect("Pays / Sélections", all_pays, default=[])
poule_filter = st.sidebar.selectbox("Tableau", ["Toutes", "Poule Haute (Main Round / Finales)", "Poule Basse (President's Cup)"])
type_poste_sel = st.sidebar.selectbox("Catégorie de Poste", ["Tous", "CHAMP", "GARDIENNE"])

postes_uniques = sorted([p for p in df["Poste_Precis"].unique() if str(p) not in ["Non renseigné", "0", "0.0"]])
selected_postes = st.sidebar.multiselect("Poste(s) précis", postes_uniques, default=[])
min_matchs = st.sidebar.slider("Matchs joués min.", 1, int(df["Matchs_Joues"].max()) if not df.empty else 8, 3)

df_w = df.copy()
if poule_filter != "Toutes":
    tag = "Poule Haute" if "Haute" in poule_filter else "Poule Basse"
    j_poule = df_raw[df_raw["Poule_Niveau"] == tag]["Nom_Joueuse"].unique()
    df_w = df_w[df_w["Nom_Joueuse"].isin(j_poule)]

if selected_pays:
    df_w = df_w[df_w["Pays"].isin(selected_pays)]
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
    
    secteur_choisi = st.sidebar.selectbox("🎯 Secteur d'arrêt prioritaire", ["Tous", "Arrêts 6m", "Arrêts 9m", "Arrêts Wing", "Arrêts 7m", "Arrêts FB (Contre-attaque)", "Arrêts Brk (Percée)", "Arrêts LD (Cage vide)"])
    
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
    
    secteur_choisi = st.sidebar.selectbox("🎯 Secteur de tir prioritaire", ["Tous", "Secteur 6m", "Secteur 9m", "Secteur Wing (Ailes)", "Secteur 7m", "Contre-attaque (FB)", "Percée (Brk)", "Buts Cage Vide (LD)"])
    
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

# --- COMPARATEUR MULTI-JOUEUSES AVEC RECHERCHE ET AJOUT CUMULATIF ---
st.markdown("---")
st.subheader("⚔️ Outil de Comparaison Directe (jusqu'à 10 joueuses)")

all_j_names = df_w["Nom_Joueuse"].tolist()

if "compare_pool" not in st.session_state:
    st.session_state.compare_pool = all_j_names[:2] if len(all_j_names) >= 2 else []

# Zone de recherche et d'ajout pour le comparateur
c_rech1, c_rech2, c_btn = st.columns([1.5, 1.5, 0.8])
with c_rech1:
    txt_rech_comp = st.text_input("🔍 Rechercher une joueuse par nom/pays :", "", key="rech_comp_input")

with c_rech2:
    if txt_rech_comp:
        candidats = [j for j in all_j_names if txt_rech_comp.lower() in j.lower()]
    else:
        candidats = all_j_names
    
    cand_sel = st.selectbox("Joueuse trouvée :", candidats if candidats else ["Aucun résultat"], key="cand_comp_select")

with c_btn:
    st.write("")
    st.write("")
    if st.button("➕ Ajouter", key="btn_add_player") and cand_sel != "Aucun résultat":
        if cand_sel not in st.session_state.compare_pool:
            if len(st.session_state.compare_pool) < 10:
                st.session_state.compare_pool.append(cand_sel)
                st.rerun()
            else:
                st.warning("Maximum 10 joueuses.")

col_sel_c, col_ref_c = st.columns([2, 1])
with col_sel_c:
    valid_pool = [j for j in st.session_state.compare_pool if j in all_j_names]
    selected_comp = st.multiselect("Joueuses actuellement comparées :", all_j_names, default=valid_pool, max_selections=10, key="multi_comp_key")
    st.session_state.compare_pool = selected_comp

with col_ref_c:
    ref_choice = st.radio("Ligne de référence :", ["Moyenne Générale", "Top 10", "Top 20"], horizontal=True)

if selected_comp:
    cat_comp = ['Assists', 'Buts (hors 7m)', '7m', 'Tirs Bloqués', 'Implication']
    sub_ref = df_w.sort_values(by="Buts", ascending=False).head(10 if ref_choice == "Top 10" else (20 if ref_choice == "Top 20" else len(df_w)))
    val_ref = [sub_ref['Passes_D'].mean(), sub_ref['Buts'].mean(), sub_ref['Buts_7m'].mean(), sub_ref['Tirs_Bloques'].mean(), sub_ref['Implication'].mean()]
    
    max_val = max(max(val_ref), 1)
    for j in selected_comp:
        rj = df_w[df_w["Nom_Joueuse"] == j].iloc[0]
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

    for a_pos, v_ref_num, r_pos in zip(ang, val_ref, va_p[:-1]):
        ax.text(
            a_pos, max(r_pos - 8.0, 5.0), f"{v_ref_num:.1f}",
            color='#cbd5e1', fontsize=7.5, fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='#0f172a', edgecolor='#475569', alpha=0.95),
            zorder=6
        )

    pal = ['#22c55e', '#38bdf8', '#f59e0b', '#ec4899', '#a855f7', '#14b8a6', '#f43f5e', '#84cc16', '#eab308', '#6366f1']
    
    for i, j_nom in enumerate(selected_comp):
        rj = df_w[df_w["Nom_Joueuse"] == j_nom].iloc[0]
        raw_vals = [rj['Passes_D'], rj['Buts'], rj['Buts_7m'], rj['Tirs_Bloques'], rj['Implication']]
        v_plot = [(v / max_val) * 70 + 18 for v in raw_vals]
        col = pal[i % len(pal)]
        ax.plot(ang_p, v_plot + [v_plot[0]], linewidth=2.0, color=col, label=f"{j_nom} ({rj['Pays']})")
        ax.scatter(ang, v_plot, color=col, s=30, zorder=5)

        ang_shift = (i - (len(selected_comp) - 1) / 2.0) * 0.05
        for a_base, val_num, rad_pos in zip(ang, raw_vals, v_plot):
            a_pos = a_base + ang_shift
            r_label = rad_pos + 6.5 + (i % 2) * 5.0
            ax.text(
                a_pos, r_label, f"{int(val_num)}",
                color=col, fontsize=7.0, fontweight='bold', ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.12', facecolor='#0b0f19', edgecolor=col, alpha=0.92, linewidth=0.5),
                zorder=10
            )

    col_chart, col_leg_tab = st.columns([1.1, 1.2])
    with col_chart:
        st.pyplot(fig)
    with col_leg_tab:
        st.markdown("##### 🔢 Tableau Comparatif Direct")
        df_comp_tab = df_w[df_w["Nom_Joueuse"].isin(selected_comp)][["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", "Stat_Buts_Hors_7m", "Stat_7m", "Passes_D", "Implication", "Tirs_Bloques", "Sanctions_2m"]].reset_index(drop=True)
        df_comp_tab.columns = ["Joueuse", "Pays", "Poste", "Matchs", "Buts (hors 7m)", "7m", "Assists", "Implication", "Contres", "2m"]
        st.dataframe(df_comp_tab, use_container_width=True)

# --- FICHE JOUEUSE AVEC RECHERCHE RAPIDE ---
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
    rf = df_w[df_w["Nom_Joueuse"] == j_sel].iloc[0]
    
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

    st.markdown("#### 📅 Parcours Chronologique")
    m_player = raw_sub.copy()

    def score_chronologique(phase_str):
        p = str(phase_str)
        if "Prelim" in p or "Preliminary" in p:
            m_r = re.search(r"(\d+)\.\s*round", p, re.I)
            r_num = int(m_r.group(1)) if m_r else 1
            return 10 + r_num
        elif "Main Round" in p or "President" in p:
            m_r = re.search(r"(\d+)\.\s*round", p, re.I)
            r_num = int(m_r.group(1)) if m_r else 1
            return 20 + r_num
        elif "Quarter" in p:
            return 30
        elif "Semi" in p:
            return 40
        elif "Final" in p or "place" in p or "Placement" in p:
            return 50
        return 99

    m_player["Chrono_Score"] = m_player["Phase"].apply(score_chronologique)
    m_player = m_player.sort_values(by="Chrono_Score")

    def formater_tour(phase_raw):
        p = str(phase_raw)
        p = p.replace("Preliminary Round - ", "Prelim. ")
        p = p.replace("President's Cup - ", "Pres. Cup ")
        p = p.replace("President Cup - ", "Pres. Cup ")
        p = p.replace("Quarter-final", "1/4 Finale")
        p = p.replace("Quarterfinals", "1/4 Finale")
        p = p.replace("Semi-final", "1/2 Finale")
        p = p.replace("Semifinals", "1/2 Finale")
        p = p.replace("Final Round, ", "")
        p = p.replace("Final Round - ", "")
        return p.strip()

    cols_m = st.columns(max(len(m_player), 1))
    for idx_m, (_, r_m) in enumerate(m_player.iterrows()):
        with cols_m[idx_m]:
            tour_label = formater_tour(r_m["Phase"])
            badge = "🟢 W" if r_m["Resultat"] == "W" else ("🟡 D" if r_m["Resultat"] == "D" else "🔴 L")
            st.caption(f"**{tour_label}**")
            st.write(f"vs **{r_m['Adversaire']}**")
            st.write(badge)
            st.caption(f"{r_m['Buts_Totaux']} buts | {r_m['Min_Jouees']} min")

    st.markdown("#### 📊 Analyse Graphique & Indicateurs")
    
    cat_ind = ['Assists', 'Buts', 'Sanctions (2m)', 'Tirs Bloqués', 'Implication']
    avg_ind = [df_w['Passes_D'].mean(), df_w['Buts'].mean(), df_w['Sanctions_2m'].mean(), df_w['Tirs_Bloques'].mean(), df_w['Implication'].mean()]
    val_ind = [rf['Passes_D'], rf['Buts'], rf['Sanctions_2m'], rf['Tirs_Bloques'], rf['Implication']]
    
    m_ind = max(max(val_ind), max(avg_ind), 1)
    vp_i = [(v / m_ind) * 60 + 18 for v in val_ind]
    va_i = [(v / m_ind) * 60 + 18 for v in avg_ind]
    ang_i = [n / float(len(cat_ind)) * 2 * np.pi for n in range(len(cat_ind))]

    fig_ind, ax_i = plt.subplots(figsize=(4.8, 4.8), subplot_kw=dict(polar=True), facecolor='#0b0f19')
    ax_i.set_facecolor('#0b0f19')
    ax_i.set_theta_offset(np.pi / 2)
    ax_i.set_theta_direction(-1)
    plt.xticks(ang_i, cat_ind, color='#f8fafc', size=9.5, fontweight='bold')
    plt.yticks([], [])
    plt.ylim(0, 120)
    ax_i.grid(color='#1e293b', linestyle='--', linewidth=0.8)

    ax_i.plot(ang_i + [ang_i[0]], va_i + [va_i[0]], linewidth=1.8, linestyle='--', color='#94a3b8', label=f"Moyenne ({rf['Competition']})")
    ax_i.fill(ang_i + [ang_i[0]], va_i + [va_i[0]], color='#94a3b8', alpha=0.10)
    ax_i.scatter(ang_i, va_i, color='#94a3b8', s=25)

    ax_i.plot(ang_i + [ang_i[0]], vp_i + [vp_i[0]], linewidth=2.5, color='#22c55e', label=j_sel)
    ax_i.fill(ang_i + [ang_i[0]], vp_i + [vp_i[0]], color='#22c55e', alpha=0.25)
    ax_i.scatter(ang_i, vp_i, color='#22c55e', s=45)

    for a_pos, v_p, v_a, r_p, r_a in zip(ang_i, val_ind, avg_ind, vp_i, va_i):
        ax_i.text(a_pos, r_p + 9, f"{int(v_p)}", color='#22c55e', fontsize=8.0, fontweight='bold', ha='center', va='center', bbox=dict(boxstyle='round,pad=0.2', facecolor='#0b0f19', edgecolor='#22c55e', alpha=0.85))
        ax_i.text(a_pos, max(r_a - 9, 4), f"{v_a:.1f}", color='#cbd5e1', fontsize=7.0, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.2', facecolor='#0b0f19', edgecolor='#475569', alpha=0.80))

    ax_i.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, facecolor='#151c2c', edgecolor='#334155', labelcolor='white')

    col_g, col_k = st.columns([1.1, 1.2])
    with col_g:
        st.pyplot(fig_ind)
    with col_k:
        st.markdown(f"### 📌 KPIs — {j_sel}")
        k1, k2 = st.columns(2)
        k1.metric("Buts (Hors 7m)", rf["Stat_Buts_Hors_7m"], f"{rf['Buts_PM']} / match")
        k2.metric("Secteur 7m", rf["Stat_7m"])
        
        k3, k4 = st.columns(2)
        k3.metric("Assists", f"{int(rf['Passes_D'])}", f"{rf['PassesD_PM']} / match")
        k4.metric("Implication", f"{int(rf['Implication'])}", f"{rf['Impl_PM']} / match")

        k5, k6 = st.columns(2)
        k5.metric("Tirs Bloqués", f"{int(rf['Tirs_Bloques'])}")
        k6.metric("Sanctions (2m / R)", f"{int(rf['Sanctions_2m'])} / {int(rf['Cartons_Rouges'])}")
