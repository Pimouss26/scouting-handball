import io
import os
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
    
    df_grouped = df_raw.groupby(["Nom_Joueuse", "Competition"], as_index=False).agg({
        "Type_Poste": "first", "Poste_Precis": "first", "Pays": "first",
        "DOB": "first", "Age": "max", "Club": "first", "Taille": "max",
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

    def format_stat_ratio(reussis, totaux):
        pct = np.where(totaux > 0, (reussis / totaux) * 100, 0).round(1)
        return [f"{int(r)}/{int(t)} ({p:.1f} %)" if t > 0 else "0/0 (0 %)" for r, t, p in zip(reussis, totaux, pct)]

    # Formats ratios Champ
    df_grouped["Stat_Buts_Hors_7m"] = format_stat_ratio(df_grouped["Buts"], df_grouped["Tirs_Hors_7m"])
    df_grouped["Stat_Global_Tir"] = format_stat_ratio(df_grouped["Buts_Totaux"], df_grouped["Tirs_Totaux"])
    df_grouped["Stat_6m"] = format_stat_ratio(df_grouped["Buts_6m"], df_grouped["Tirs_6m"])
    df_grouped["Stat_9m"] = format_stat_ratio(df_grouped["Buts_9m"], df_grouped["Tirs_9m"])
    df_grouped["Stat_Wing"] = format_stat_ratio(df_grouped["Buts_Wing"], df_grouped["Tirs_Wing"])
    df_grouped["Stat_7m"] = format_stat_ratio(df_grouped["Buts_7m"], df_grouped["Tirs_7m"])
    df_grouped["Stat_FB"] = format_stat_ratio(df_grouped["Buts_FB"], df_grouped["Tirs_FB"])
    df_grouped["Stat_Brk"] = format_stat_ratio(df_grouped["Buts_Brk"], df_grouped["Tirs_Brk"])
    df_grouped["Stat_LD"] = format_stat_ratio(df_grouped["Buts_LD"], df_grouped["Tirs_LD"])

    # Formats ratios Gardiennes
    df_grouped["Stat_Global_Arrets"] = format_stat_ratio(df_grouped["Arrets_Totaux"], df_grouped["Tirs_Subis"])
    df_grouped["Stat_Arr_6m"] = format_stat_ratio(df_grouped["Arrets_6m"], df_grouped["Tirs_6m_Subis"])
    df_grouped["Stat_Arr_9m"] = format_stat_ratio(df_grouped["Arrets_9m"], df_grouped["Tirs_9m_Subis"])
    df_grouped["Stat_Arr_Wing"] = format_stat_ratio(df_grouped["Arrets_Wing"], df_grouped["Tirs_Wing_Subis"])
    df_grouped["Stat_Arr_7m"] = format_stat_ratio(df_grouped["Arrets_7m"], df_grouped["Tirs_7m_Subis"])
    df_grouped["Stat_Arr_FB"] = format_stat_ratio(df_grouped["Arrets_FB"], df_grouped["Tirs_FB_Subis"])
    df_grouped["Stat_Arr_Brk"] = format_stat_ratio(df_grouped["Arrets_Brk"], df_grouped["Tirs_Brk_Subis"])
    df_grouped["Stat_Arr_LD"] = format_stat_ratio(df_grouped["Arrets_LD"], df_grouped["Tirs_LD_Subis"])

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

# --- SÉLECTION DES SECTEURS ET CRITÈRES ---
st.sidebar.header("📊 Critères & Secteurs")

if type_poste_sel == "GARDIENNE":
    secteur_choisi = st.sidebar.selectbox("🎯 Secteur d'arrêt prioritaire", ["Tous", "Arrêts 6m", "Arrêts 9m", "Arrêts Wing", "Arrêts 7m", "Arrêts FB (Contre-attaque)", "Arrêts Brk (Percée)", "Arrêts LD (Cage vide)"])
    criteres = {"% d'Arrêts": "Pct_Arrets", "Arrêts Totaux": "Arrets_Totaux", "Arrêts / Match": "Arrets_PM", "Relances (Passes D)": "Passes_D"}
    
    mapping_secteurs = {
        "Arrêts 6m": ("Arrets_6m", "Stat_Arr_6m", "Arrêts 6m (Ratio %)"),
        "Arrêts 9m": ("Arrets_9m", "Stat_Arr_9m", "Arrêts 9m (Ratio %)"),
        "Arrêts Wing": ("Arrets_Wing", "Stat_Arr_Wing", "Arrêts Wing (Ratio %)"),
        "Arrêts 7m": ("Arrets_7m", "Stat_Arr_7m", "Arrêts 7m (Ratio %)"),
        "Arrêts FB (Contre-attaque)": ("Arrets_FB", "Stat_Arr_FB", "Arrêts FB (Ratio %)"),
        "Arrêts Brk (Percée)": ("Arrets_Brk", "Stat_Arr_Brk", "Arrêts Brk (Ratio %)"),
        "Arrêts LD (Cage vide)": ("Arrets_LD", "Stat_Arr_LD", "Arrêts LD (Ratio %)")
    }
else:
    secteur_choisi = st.sidebar.selectbox("🎯 Secteur de tir prioritaire", ["Tous", "Secteur 6m", "Secteur 9m", "Secteur Wing (Ailes)", "Secteur 7m", "Contre-attaque (FB)", "Percée (Brk)", "Buts Cage Vide (LD)"])
    criteres = {"Buts (Hors 7m)": "Buts", "Buts par Match": "Buts_PM", "Implication Totale": "Implication", "Buts sur 7m": "Buts_7m", "Assists": "Passes_D"}
    
    mapping_secteurs = {
        "Secteur 6m": ("Buts_6m", "Stat_6m", "Buts 6m (Ratio %)"),
        "Secteur 9m": ("Buts_9m", "Stat_9m", "Buts 9m (Ratio %)"),
        "Secteur Wing (Ailes)": ("Buts_Wing", "Stat_Wing", "Buts Wing (Ratio %)"),
        "Secteur 7m": ("Buts_7m", "Stat_7m", "Buts 7m (Ratio %)"),
        "Contre-attaque (FB)": ("Buts_FB", "Stat_FB", "Buts FB (Ratio %)"),
        "Percée (Brk)": ("Buts_Brk", "Stat_Brk", "Buts Brk (Ratio %)"),
        "Buts Cage Vide (LD)": ("Buts_LD", "Stat_LD", "Buts LD (Ratio %)")
    }

tri_choisi = st.sidebar.selectbox("Classer par", list(criteres.keys()))

if secteur_choisi != "Tous":
    col_tri_val, col_stat_txt, nom_col_affiche = mapping_secteurs[secteur_choisi]
    df_top = df_w.sort_values(by=col_tri_val, ascending=False).reset_index(drop=True)
else:
    col_tri_val = criteres[tri_choisi]
    df_top = df_w.sort_values(by=col_tri_val, ascending=False).reset_index(drop=True)

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

st.subheader(f"🏆 Classement — {secteur_choisi if secteur_choisi != 'Tous' else tri_choisi}")
st.dataframe(df_display.head(top_n), use_container_width=True)

# --- COMPARATEUR MULTI-JOUEUSES (CLARTÉ OPTIMISÉE) ---
st.markdown("---")
st.subheader("⚔️ Outil de Comparaison Directe (jusqu'à 10 joueuses)")

rech_txt = st.text_input("🔍 Rechercher une joueuse :", "")
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
        
        # Décalage progressif des étiquettes avec boîte de lisibilité
        offset_rad = 5 + (i * 3.5)
        for a_pos, val_num, rad_pos in zip(ang, raw_vals, v_plot):
            ax.text(a_pos, rad_pos + offset_rad, f"{int(val_num)}", color=col, fontsize=8, fontweight='bold', ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='#0b0f19', edgecolor=col, alpha=0.9, linewidth=0.5))

    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), facecolor='#151c2c', edgecolor='#334155', labelcolor='white')
    st.pyplot(fig)

# --- FICHE JOUEUSE LISIBLE ET COMPACTE ---
st.markdown("---")
st.subheader("📋 Fiche Joueuse Complète")

j_sel = st.selectbox("Sélectionner la joueuse à analyser :", df_w["Nom_Joueuse"].tolist())

if j_sel:
    rf = df_w[df_w["Nom_Joueuse"] == j_sel].iloc[0]
    
    # Infos personnelles compactes
    dob_val = str(rf["DOB"]) if str(rf["DOB"]) not in ["0", "0.0", "nan"] else ""
    dob_txt = f"née le {dob_val}" if dob_val else (f"({int(rf['Age'])} ans)" if rf['Age'] > 0 else "")
    taille_txt = f"{int(rf['Taille'])} cm" if rf['Taille'] > 0 else "Taille N/A"
    
    st.markdown(f"### **{j_sel}** — {rf['Pays']}")
    st.markdown(f"**Poste :** `{rf['Poste_Precis']}` | **Club :** `{rf['Club']}` | **Physique / Âge :** `{taille_txt} — {dob_txt}`")

    st.markdown("#### 📅 Parcours Chronologique")
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

    st.markdown("#### 📊 Analyse Graphique & Indicateurs")
    
    cat_ind = ['Assists', 'Buts', 'Sanctions (2m)', 'Tirs Bloqués', 'Implication']
    avg_ind = [df_w['Passes_D'].mean(), df_w['Buts'].mean(), df_w['Sanctions_2m'].mean(), df_w['Tirs_Bloques'].mean(), df_w['Implication'].mean()]
    val_ind = [rf['Passes_D'], rf['Buts'], rf['Sanctions_2m'], rf['Tirs_Bloques'], rf['Implication']]
    
    m_ind = max(max(val_ind), max(avg_ind), 1)
    vp_i = [(v / m_ind) * 60 + 18 for v in val_ind]
    va_i = [(v / m_ind) * 60 + 18 for v in avg_ind]
    ang_i = [n / float(len(cat_ind)) * 2 * np.pi for n in range(len(cat_ind))]

    fig_ind, ax_i = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True), facecolor='#0b0f19')
    ax_i.set_facecolor('#0b0f19')
    ax_i.set_theta_offset(np.pi / 2)
    ax_i.set_theta_direction(-1)
    plt.xticks(ang_i, cat_ind, color='#f8fafc', size=9, fontweight='bold')
    plt.yticks([], [])
    plt.ylim(0, 115)
    ax_i.grid(color='#1e293b', linestyle='--', linewidth=0.8)

    ax_i.plot(ang_i + [ang_i[0]], va_i + [va_i[0]], linewidth=1.8, linestyle='--', color='#94a3b8', label=f"Moyenne")
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
        k1.metric("Buts (Hors 7m)", rf["Stat_Buts_Hors_7m"], f"{rf['Buts_PM']} / match")
        k2.metric("Secteur 7m", rf["Stat_7m"])
        
        k3, k4 = st.columns(2)
        k3.metric("Assists", f"{int(rf['Passes_D'])}", f"{rf['PassesD_PM']} / match")
        k4.metric("Implication", f"{int(rf['Implication'])}", f"{rf['Impl_PM']} / match")

        k5, k6 = st.columns(2)
        k5.metric("Tirs Bloqués", f"{int(rf['Tirs_Bloques'])}")
        k6.metric("Sanctions (2m / R)", f"{int(rf['Sanctions_2m'])} / {int(rf['Cartons_Rouges'])}")
