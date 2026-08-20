import io
import os
import unicodedata
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Hub Scouting Handball U18", page_icon="🤾‍♀️", layout="wide")

EXCEL_FILE = "data_handball.xlsx"

def clean_txt(text):
    if not text or pd.isna(text):
        return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode('utf-8').strip()

@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame(), pd.DataFrame()
    df_raw = pd.read_excel(EXCEL_FILE, sheet_name="DATA_MATCHS").fillna(0)
    
    df_grouped = df_raw.groupby(["Nom_Joueuse", "Competition"], as_index=False).agg({
        "Type_Poste": "first", "Poste_Precis": "first", "Pays": "first",
        "Age": "max", "Club": "first", "Taille": "max",
        "Min_Jouees": ["count", "sum"], "Titulaire": "sum",
        "Buts_Sans_7m": "sum", "Buts_7m": "sum", "Tirs_7m": "sum", "Buts_Totaux": "sum",
        "Buts_6m": "sum", "Buts_9m": "sum", "Buts_Wing": "sum", "Buts_FB": "sum", "Buts_Brk": "sum", "Buts_LD": "sum",
        "Passes_D": "sum", "Tirs_Bloques": "sum", "Sanctions_2min": "sum", "Cartons_Rouges": "sum",
        "Arrets_Totaux": "sum", "Tirs_Subis": "sum", "Arrets_7m": "sum",
        "Arrets_6m": "sum", "Arrets_9m": "sum", "Arrets_Wing": "sum", "Arrets_FB": "sum", "Arrets_Brk": "sum", "Arrets_LD": "sum"
    })
    
    df_grouped.columns = [
        "Nom_Joueuse", "Competition", "Type_Poste", "Poste_Precis", "Pays",
        "Age", "Club", "Taille", "Matchs_Joues", "Min_Totales", "Titularisations",
        "Buts", "Buts_7m", "Tirs_7m", "Buts_Totaux",
        "Buts_6m", "Buts_9m", "Buts_Wing", "Buts_FB", "Buts_Brk", "Buts_LD",
        "Passes_D", "Tirs_Bloques", "Sanctions_2m", "Cartons_Rouges",
        "Arrets_Totaux", "Tirs_Subis", "Arrets_7m",
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
all_pays = sorted([p for p in df["Pays"].unique() if str(p) not in ["0", "Inconnu", "0.0"]])
selected_pays = st.sidebar.multiselect("Pays / Sélections", all_pays, default=[])
poule_filter = st.sidebar.selectbox("Tableau", ["Toutes", "Poule Haute (Main Round / Finales)", "Poule Basse (President's Cup)"])
type_poste_sel = st.sidebar.selectbox("Catégorie de Poste", ["Tous", "CHAMP", "GARDIENNE"])

postes_uniques = sorted([p for p in df["Poste_Precis"].unique() if p not in ["Non renseigné", "0", 0]])
selected_postes = st.sidebar.multiselect("Poste(s) précis", postes_uniques, default=[])

min_matchs = st.sidebar.slider("Matchs joués min.", 1, int(df["Matchs_Joues"].max()) if not df.empty else 8, 3)

# Filtrage
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

# --- SECTEURS & CRITÈRES DE CLASSEMENT ---
st.sidebar.header("📊 Critères & Secteurs")

if type_poste_sel == "GARDIENNE":
    secteur_choisi = st.sidebar.selectbox("🎯 Secteur d'arrêt prioritaire", ["Tous", "Arrêts 6m", "Arrêts 9m", "Arrêts Wing", "Arrêts 7m", "Arrêts FB (Contre-attaque)", "Arrêts Brk (Percée)", "Arrêts LD (Cage vide)"])
    criteres = {"% d'Arrêts": "Pct_Arrets", "Arrêts Totaux": "Arrets_Totaux", "Arrêts / Match": "Arrets_PM", "Relances (Passes D)": "Passes_D"}
    sect_col = {"Arrêts 6m": "Arrets_6m", "Arrêts 9m": "Arrets_9m", "Arrêts Wing": "Arrets_Wing", "Arrêts 7m": "Arrets_7m", "Arrêts FB (Contre-attaque)": "Arrets_FB", "Arrêts Brk (Percée)": "Arrets_Brk", "Arrêts LD (Cage vide)": "Arrets_LD"}.get(secteur_choisi)
else:
    secteur_choisi = st.sidebar.selectbox("🎯 Secteur de tir prioritaire", ["Tous", "Secteur 6m", "Secteur 9m", "Secteur Wing (Ailes)", "Secteur 7m", "Contre-attaque (FB)", "Percée (Brk)", "Buts Cage Vide (LD)"])
    criteres = {"Buts (Hors 7m)": "Buts", "Buts par Match": "Buts_PM", "Implication Totale": "Implication", "Buts sur 7m": "Buts_7m", "Assists": "Passes_D", "Titularisations (S)": "Titularisations"}
    sect_col = {"Secteur 6m": "Buts_6m", "Secteur 9m": "Buts_9m", "Secteur Wing (Ailes)": "Buts_Wing", "Secteur 7m": "Buts_7m", "Contre-attaque (FB)": "Buts_FB", "Percée (Brk)": "Buts_Brk", "Buts Cage Vide (LD)": "Buts_LD"}.get(secteur_choisi)

tri_choisi = st.sidebar.selectbox("Classer par", list(criteres.keys()))
col_finale = sect_col if sect_col else criteres[tri_choisi]
top_n = st.sidebar.slider("Afficher le Top :", 5, 50, 15)

df_top = df_w.sort_values(by=col_finale, ascending=False).reset_index(drop=True)
df_top.index += 1

st.subheader(f"🏆 Classement — {secteur_choisi if sect_col else tri_choisi}")
cols_tab = ["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", "Titularisations", "Buts", "Buts_7m", "Passes_D", "Implication", "Sanctions_2m"] if type_poste_sel != "GARDIENNE" else ["Nom_Joueuse", "Pays", "Poste_Precis", "Matchs_Joues", "Titularisations", "Arrets_Totaux", "Pct_Arrets", "Arrets_7m", "Passes_D", "Sanctions_2m"]
st.dataframe(df_top[[c for c in cols_tab if c in df_top.columns]].head(top_n), use_container_width=True)

# --- COMPARATEUR MULTI-JOUEUSES AVEC RECHERCHE ET LABELS ---
st.markdown("---")
st.subheader("⚔️ Outil de Comparaison Directe (jusqu'à 10 joueuses)")

rech_txt = st.text_input("🔍 Rechercher une joueuse pour l'ajouter à la comparaison :", "")
options_j = df_w[df_w["Nom_Joueuse"].str.contains(rech_txt, case=False, na=False)]["Nom_Joueuse"].tolist() if rech_txt else df_w["Nom_Joueuse"].tolist()

joueuses_compare = st.multiselect("Joueuses sélectionnées :", options_j, default=options_j[:2] if len(options_j) >= 2 and not rech_txt else [], max_selections=10)
ref_choice = st.radio("Ligne de référence :", ["Moyenne Générale", "Top 10", "Top 20"], horizontal=True)

if joueuses_compare:
    cat_comp = ['Assists', 'Buts (hors 7m)', '7m', 'Tirs Bloqués', 'Implication']
    sub_ref = df_w.sort_values(by="Buts", ascending=False).head(10 if ref_choice == "Top 10" else (20 if ref_choice == "Top 20" else len(df_w)))
    val_ref = [sub_ref['Passes_D'].mean(), sub_ref['Buts'].mean(), sub_ref['Buts_7m'].mean(), sub_ref['Tirs_Bloques'].mean(), sub_ref['Implication'].mean()]
    
    max_val = max(max(val_ref), 1)
    for j in joueuses_compare:
        rj = df_w[df_w["Nom_Joueuse"] == j].iloc[0]
        max_val = max(max_val, rj['Passes_D'], rj['Buts'], rj['Buts_7m'], rj['Tirs_Bloques'], rj['Implication'])

    ang = [n / float(len(cat_comp)) * 2 * np.pi for n in range(len(cat_comp))]
    ang_p = ang + [ang[0]]

    fig, ax = plt.subplots(figsize=(7.5, 7.5), subplot_kw=dict(polar=True), facecolor='#0b0f19')
    ax.set_facecolor('#0b0f19')
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    plt.xticks(ang, cat_comp, color='#f8fafc', size=9.5, fontweight='bold')
    plt.yticks([], [])
    plt.ylim(0, 115)
    ax.grid(color='#1e293b', linestyle='--', linewidth=0.8)

    va_p = [(v / max_val) * 70 + 18 for v in val_ref] + [(val_ref[0] / max_val) * 70 + 18]
    ax.plot(ang_p, va_p, linewidth=1.6, linestyle='--', color='#94a3b8', label=ref_choice)

    pal = ['#22c55e', '#38bdf8', '#f59e0b', '#ec4899', '#a855f7', '#14b8a6', '#f43f5e', '#84cc16', '#eab308', '#6366f1']
    for i, j_nom in enumerate(joueuses_compare):
        rj = df_w[df_w["Nom_Joueuse"] == j_nom].iloc[0]
        raw_vals = [rj['Passes_D'], rj['Buts'], rj['Buts_7m'], rj['Tirs_Bloques'], rj['Implication']]
        v_plot = [(v / max_val) * 70 + 18 for v in raw_vals]
        col = pal[i % len(pal)]
        ax.plot(ang_p, v_plot + [v_plot[0]], linewidth=2.2, color=col, label=f"{j_nom} ({rj['Pays']})")
        ax.scatter(ang, v_plot, color=col, s=35)
        for a_pos, val_num, rad_pos in zip(ang, raw_vals, v_plot):
            ax.text(a_pos, rad_pos + 6, f"{int(val_num)}", color=col, fontsize=8, fontweight='bold', ha='center', va='center')

    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), facecolor='#151c2c', edgecolor='#334155', labelcolor='white')
    st.pyplot(fig)

# --- FICHE JOUEUSE INTÉGRÉE & ANALYSE GRAPHIQUE ---
st.markdown("---")
st.subheader("📋 Fiche Joueuse Complète & Parcours")

j_sel = st.selectbox("Choisir une joueuse :", df_w["Nom_Joueuse"].tolist())

if j_sel:
    rf = df_w[df_w["Nom_Joueuse"] == j_sel].iloc[0]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Poste Officiel", rf["Poste_Precis"] if rf["Poste_Precis"] != "Non renseigné" else "Non renseigné")
    c2.metric("Club", rf["Club"] if rf["Club"] != "Non renseigné" else "Non renseigné")
    taille_txt = f"{int(rf['Taille'])} cm" if rf['Taille'] > 0 else "N/A"
    age_txt = f"{int(rf['Age'])} ans" if rf['Age'] > 0 else "N/A"
    c3.metric("Taille & Âge", f"{taille_txt} | {age_txt}")
    c4.metric("Titularisations (S)", f"{int(rf['Titularisations'])} / {int(rf['Matchs_Joues'])}")

    st.markdown("#### 📅 Parcours Chronologique du Tournoi")
    m_player = df_raw[df_raw["Nom_Joueuse"] == j_sel].copy()
    
    order_map = {"Preliminary": 1, "Main": 2, "President": 2, "Quarter": 3, "Semi": 4, "Final": 5, "Placement": 5}
    m_player["Ordre"] = m_player["Phase"].apply(lambda x: next((v for k, v in order_map.items() if k in str(x)), 3))
    m_player = m_player.sort_values(by="Ordre")

    cols_m = st.columns(max(len(m_player), 1))
    for idx_m, (_, r_m) in enumerate(m_player.iterrows()):
        with cols_m[idx_m]:
            badge = "🟢 W" if r_m["Resultat"] == "W" else ("🟡 D" if r_m["Resultat"] == "D" else "🔴 L")
            st.caption(f"**Match {idx_m+1}**")
            st.write(f"vs **{r_m['Adversaire']}**")
            st.write(badge)
            st.caption(f"{r_m['Buts_Totaux']} buts | {r_m['Min_Jouees']} min")

    st.markdown("#### 📊 Analyse Graphique & Indicateurs Clés")
    
    # Graphique radar individuel
    cat_ind = ['Assists', 'Buts', 'Sanctions (2m)', 'Tirs Bloqués', 'Implication']
    avg_ind = [df_w['Passes_D'].mean(), df_w['Buts'].mean(), df_w['Sanctions_2m'].mean(), df_w['Tirs_Bloques'].mean(), df_w['Implication'].mean()]
    val_ind = [rf['Passes_D'], rf['Buts'], rf['Sanctions_2m'], rf['Tirs_Bloques'], rf['Implication']]
    
    m_ind = max(max(val_ind), max(avg_ind), 1)
    vp_i = [(v / m_ind) * 60 + 18 for v in val_ind]
    va_i = [(v / m_ind) * 60 + 18 for v in avg_ind]
    ang_i = [n / float(len(cat_ind)) * 2 * np.pi for n in range(len(cat_ind))]

    fig_ind, ax_i = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True), facecolor='#0b0f19')
    ax_i.set_facecolor('#0b0f19')
    ax_i.set_theta_offset(np.pi / 2)
    ax_i.set_theta_direction(-1)
    plt.xticks(ang_i, cat_ind, color='#f8fafc', size=9.5, fontweight='bold')
    plt.yticks([], [])
    plt.ylim(0, 115)
    ax_i.grid(color='#1e293b', linestyle='--', linewidth=0.8)

    ax_i.plot(ang_i + [ang_i[0]], va_i + [va_i[0]], linewidth=1.8, linestyle='--', color='#94a3b8', label=f"Moyenne ({rf['Competition']})")
    ax_i.fill(ang_i + [ang_i[0]], va_i + [va_i[0]], color='#94a3b8', alpha=0.10)
    ax_i.scatter(ang_i, va_i, color='#94a3b8', s=25)

    ax_i.plot(ang_i + [ang_i[0]], vp_i + [vp_i[0]], linewidth=2.5, color='#22c55e', label=j_sel)
    ax_i.fill(ang_i + [ang_i[0]], vp_i + [vp_i[0]], color='#22c55e', alpha=0.25)
    ax_i.scatter(ang_i, vp_i, color='#22c55e', s=45)

    for a_pos, v_p, v_a, r_p, r_a in zip(ang_i, val_ind, avg_ind, vp_i, va_i):
        ax_i.text(a_pos, r_p + 9, f"{int(v_p)}", color='#22c55e', fontsize=8.5, fontweight='bold', ha='center', va='center', bbox=dict(boxstyle='round,pad=0.2', facecolor='#0b0f19', edgecolor='#22c55e', alpha=0.85))
        ax_i.text(a_pos, max(r_a - 9, 4), f"{v_a:.1f}", color='#cbd5e1', fontsize=7, ha='center', va='center', bbox=dict(boxstyle='round,pad=0.2', facecolor='#0b0f19', edgecolor='#475569', alpha=0.80))

    ax_i.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15), facecolor='#151c2c', edgecolor='#334155', labelcolor='white')

    col_g, col_k = st.columns([1.2, 1])
    with col_g:
        st.pyplot(fig_ind)
    with col_k:
        st.markdown(f"### 📌 KPIs — {j_sel}")
        k1, k2 = st.columns(2)
        k1.metric("Buts (Hors 7m)", f"{int(rf['Buts'])}", f"{rf['Buts_PM']} / match")
        k2.metric("Buts 7m", f"{int(rf['Buts_7m'])} / {int(rf['Tirs_7m'])}", f"{rf['Pct_7m']}%")
        
        k3, k4 = st.columns(2)
        k3.metric("Assists", f"{int(rf['Passes_D'])}", f"{rf['PassesD_PM']} / match")
        k4.metric("Implication", f"{int(rf['Implication'])}", f"{rf['Impl_PM']} / match")

        k5, k6 = st.columns(2)
        k5.metric("Tirs Bloqués", f"{int(rf['Tirs_Bloques'])}")
        k6.metric("Sanctions (2m / R)", f"{int(rf['Sanctions_2m'])} / {int(rf['Cartons_Rouges'])}")
