import io
import os
import unicodedata
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Plateforme Scouting Handball U18", page_icon="🤾‍♀️", layout="wide")

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
        "Pays": "first",
        "Min_Jouees": ["count", "sum"],
        "Buts": "sum",
        "Passes_D": "sum",
        "Tirs_Bloques": "sum",
        "Sanctions_2min": "sum",
        "Arrets": "sum",
        "Tirs_Subis": "sum"
    })
    
    df_grouped.columns = [
        "Nom_Joueuse", "Competition", "Type_Poste", "Pays",
        "Matchs_Joues", "Min_Totales", "Buts", "Passes_D",
        "Tirs_Bloques", "Sanctions_2min", "Arrets", "Tirs_Subis"
    ]
    
    df_grouped["Implication"] = df_grouped["Buts"] + df_grouped["Passes_D"]
    df_grouped["Pct_Arrets"] = np.where(df_grouped["Tirs_Subis"] > 0, (df_grouped["Arrets"] / df_grouped["Tirs_Subis"]) * 100, 0)
    df_grouped["Buts_PM"] = (df_grouped["Buts"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["PassesD_PM"] = (df_grouped["Passes_D"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["Impl_PM"] = (df_grouped["Implication"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["Arrets_PM"] = (df_grouped["Arrets"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["Bloques_PM"] = (df_grouped["Tirs_Bloques"] / df_grouped["Matchs_Joues"]).round(1)
    df_grouped["Sanctions_PM"] = (df_grouped["Sanctions_2min"] / df_grouped["Matchs_Joues"]).round(1)

    return df_raw, df_grouped

df_raw, df = load_data()

st.title("🤾‍♀️ Hub de Détection & Scouting Handball U18")
st.markdown("Filtrez les meilleures joueuses selon vos critères statistiques et générez directement leur fiche complète.")

if df.empty:
    st.warning("Fichier de données introuvable.")
    st.stop()

# --- FILTRES ---
st.sidebar.header("🎯 Filtres de Recherche")
poste_filter = st.sidebar.selectbox("Poste", ["Tous", "CHAMP", "GARDIENNE"])
liste_pays = ["Tous"] + sorted([p for p in df["Pays"].unique() if str(p) not in ["0", "Inconnu", "0.0"]])
pays_filter = st.sidebar.selectbox("Pays / Sélection", liste_pays)
min_matchs = st.sidebar.slider("Nombre minimum de matchs joués", 1, int(df["Matchs_Joues"].max()), 3)

df_filtered = df[df["Matchs_Joues"] >= min_matchs]
if poste_filter != "Tous":
    df_filtered = df_filtered[df_filtered["Type_Poste"] == poste_filter]
if pays_filter != "Tous":
    df_filtered = df_filtered[df_filtered["Pays"] == pays_filter]

# --- TRI ---
st.sidebar.header("📊 Critère de Classement")
if poste_filter == "GARDIENNE":
    criteres = {
        "% d'Arrêts": "Pct_Arrets",
        "Arrêts Totaux": "Arrets",
        "Arrêts par Match": "Arrets_PM",
        "Passes D / Relances": "Passes_D"
    }
else:
    criteres = {
        "Meilleures Buteuses (Total)": "Buts",
        "Buts par Match": "Buts_PM",
        "Implication Totale (Buts + Passes D)": "Implication",
        "Assists / Passes Décisives": "Passes_D",
        "Tirs Bloqués (Contres)": "Tirs_Bloques",
        "Discipline (Moins de 2min)": "Sanctions_2min"
    }

tri_choisi = st.sidebar.selectbox("Classer par", list(criteres.keys()))
colonne_tri = criteres[tri_choisi]
ordre_asc = True if "Moins" in tri_choisi else False
top_n = st.sidebar.slider("Afficher le Top :", 5, 50, 10)

df_top = df_filtered.sort_values(by=colonne_tri, ascending=ordre_asc).reset_index(drop=True)
df_top.index += 1

st.subheader(f"🏆 Top {top_n} — {tri_choisi}")
cols_visibles = ["Nom_Joueuse", "Pays", "Type_Poste", "Matchs_Joues", "Buts", "Buts_PM", "Passes_D", "Implication", "Tirs_Bloques", "Sanctions_2min"] if poste_filter != "GARDIENNE" else ["Nom_Joueuse", "Pays", "Matchs_Joues", "Arrets", "Arrets_PM", "Pct_Arrets", "Passes_D", "Sanctions_2min"]
st.dataframe(df_top[cols_visibles].head(top_n), use_container_width=True)

# --- GÉNÉRATEUR PDF À LA VOLÉE ---
class ScoutingPDF(FPDF):
    def draw_kpi_card(self, x, y, w, h, title, value, subtext=""):
        self.set_fill_color(21, 28, 44)
        self.set_draw_color(30, 41, 59)
        self.rect(x, y, w, h, style='FD')
        self.set_xy(x, y + 1.8)
        self.set_font("Helvetica", "B", 6.5)
        self.set_text_color(148, 163, 184)
        self.cell(w, 3.5, clean_txt(title).upper(), align='C')
        self.set_xy(x, y + 5.5)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(34, 197, 94)
        self.cell(w, 4.5, str(value), align='C')
        if subtext:
            self.set_xy(x, y + 10)
            self.set_font("Helvetica", "", 5.5)
            self.set_text_color(203, 213, 225)
            self.cell(w, 3.5, clean_txt(subtext), align='C')

def build_pdf_in_memory(row_player, raw_matches_df):
    comp = clean_txt(row_player["Competition"])
    player = clean_txt(row_player["Nom_Joueuse"])
    pays = clean_txt(row_player["Pays"])
    poste = str(row_player["Type_Poste"]).upper()
    is_gk = (poste == "GARDIENNE")
    nb_matchs = int(row_player["Matchs_Joues"])

    # Moyennes
    avg_df = df[(df["Competition"] == row_player["Competition"]) & (df["Type_Poste"] == row_player["Type_Poste"])]
    if not is_gk:
        categories = ['Assists', 'Buts', 'Sanctions (2m)', 'Tirs Bloques', 'Implication']
        raw_p = [row_player['Passes_D'], row_player['Buts'], row_player['Sanctions_2min'], row_player['Tirs_Bloques'], row_player['Implication']]
        raw_a = [avg_df['Passes_D'].mean(), avg_df['Buts'].mean(), avg_df['Sanctions_2min'].mean(), avg_df['Tirs_Bloques'].mean(), avg_df['Implication'].mean()]
    else:
        categories = ['Assists', 'Arrets', 'Sanctions (2m)', '% Arrets']
        raw_p = [row_player['Passes_D'], row_player['Arrets'], row_player['Sanctions_2min'], row_player['Pct_Arrets']]
        raw_a = [avg_df['Passes_D'].mean(), avg_df['Arrets'].mean(), avg_df['Sanctions_2min'].mean(), avg_df['Pct_Arrets'].mean()]

    max_v = max(max(raw_p), max(raw_a), 1)
    vp = [(v / max_v) * 60 + 18 for v in raw_p] + [(raw_p[0] / max_v) * 60 + 18]
    va = [(v / max_v) * 60 + 18 for v in raw_a] + [(raw_a[0] / max_v) * 60 + 18]
    angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))] + [0]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True), facecolor='#0b0f19')
    ax.set_facecolor('#0b0f19')
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    plt.xticks(angles[:-1], categories, color='#f8fafc', size=9.5, fontweight='bold')
    plt.yticks([], [])
    plt.ylim(0, 115)
    ax.grid(color='#1e293b', linestyle='--', linewidth=0.8)
    ax.spines['polar'].set_color('#1e293b')

    ax.plot(angles, va, linewidth=1.8, linestyle='--', color='#94a3b8')
    ax.fill(angles, va, color='#94a3b8', alpha=0.10)
    ax.plot(angles, vp, linewidth=2.5, color='#22c55e')
    ax.fill(angles, vp, color='#22c55e', alpha=0.25)

    img_buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_buf, format='png', dpi=200, bbox_inches='tight', facecolor='#0b0f19')
    plt.close()
    img_buf.seek(0)

    # PDF
    pdf = ScoutingPDF(orientation='P', unit='mm', format=(120, 160))
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_fill_color(11, 15, 25)
    pdf.rect(0, 0, 120, 160, 'F')

    pdf.set_y(3.0)
    pdf.set_font("Helvetica", 'B', 13.5)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 5.5, player, align='C')

    pos_y = 8.5
    if pays and pays not in ["0", "Inconnu"]:
        pdf.set_y(pos_y)
        pdf.set_font("Helvetica", 'B', 7.5)
        pdf.set_text_color(251, 191, 36)
        pdf.cell(0, 3.5, f"[{pays.upper()}]", align='C')
        pos_y += 3.5

    pdf.set_y(pos_y)
    pdf.set_font("Helvetica", 'B', 6.5)
    pdf.set_text_color(34, 197, 94)
    pdf.cell(0, 3.5, f"{comp.upper()}  |  {poste}  |  {nb_matchs} MATCH(S)", align='C')
    pos_y += 4.0

    # Matchs
    pdf.set_y(pos_y)
    cur_x = 6
    pdf.set_font("Helvetica", "", 5.2)
    for _, row_m in raw_matches_df.iterrows():
        p_clean = str(row_m.get("Phase", "")).replace("Preliminary Round - ", "Prelim. ").replace("President's Cup - ", "Pres. Cup ")
        adv = str(row_m.get("Adversaire", ""))
        m_txt = clean_txt(f"{p_clean} (vs {adv})" if adv and adv != "0" else p_clean)
        res_code = str(row_m.get("Resultat", "W")).upper()

        txt_w = pdf.get_string_width(m_txt) + 1
        if cur_x + txt_w + 7 > 114:
            cur_x = 6
            pos_y += 3.0
        pdf.set_xy(cur_x, pos_y)
        pdf.set_text_color(56, 189, 248)
        pdf.cell(txt_w, 2.8, m_txt, align='L')

        bx, by = cur_x + txt_w, pos_y + 0.3
        pdf.set_fill_color(34, 197, 94) if res_code == "W" else (pdf.set_fill_color(234, 179, 8) if res_code == "D" else pdf.set_fill_color(239, 68, 68))
        pdf.rect(bx, by, 4.0, 2.3, style='F')
        pdf.set_xy(bx, by)
        pdf.set_font("Helvetica", "B", 4.5)
        pdf.set_text_color(11, 15, 25)
        pdf.cell(4.0, 2.3, res_code, align='C')
        cur_x += txt_w + 6.5
        pdf.set_font("Helvetica", "", 5.2)

    temp_img_name = f"temp_{abs(hash(player))}.png"
    with open(temp_img_name, "wb") as f_img:
        f_img.write(img_buf.read())
    pdf.image(temp_img_name, x=13, y=max(pos_y + 3.5, 25), w=94)
    if os.path.exists(temp_img_name):
        os.remove(temp_img_name)

    start_y = 120
    card_w, card_h, sp = 32, 16, 4
    sx = (120 - (3 * card_w + 2 * sp)) / 2
    if not is_gk:
        pdf.draw_kpi_card(sx, start_y, card_w, card_h, "Buts", f"{int(row_player['Buts'])}", f"{row_player['Buts_PM']:.1f} / match")
        pdf.draw_kpi_card(sx + card_w + sp, start_y, card_w, card_h, "Assists", f"{int(row_player['Passes_D'])}", f"{row_player['PassesD_PM']:.1f} / match")
        pdf.draw_kpi_card(sx + (card_w + sp)*2, start_y, card_w, card_h, "Implication", f"{int(row_player['Implication'])}", f"{row_player['Impl_PM']:.1f} / match")
        sx2 = (120 - (2 * card_w + sp)) / 2
        pdf.draw_kpi_card(sx2, start_y + card_h + 3, card_w, card_h, "Tirs Bloques", f"{int(row_player['Tirs_Bloques'])}", f"{row_player['Bloques_PM']:.1f} / match")
        pdf.draw_kpi_card(sx2 + card_w + sp, start_y + card_h + 3, card_w, card_h, "Sanctions", f"{int(row_player['Sanctions_2min'])}", f"{row_player['Sanctions_PM']:.1f} / match")
    else:
        pdf.draw_kpi_card(sx, start_y, card_w, card_h, "Arrets", f"{int(row_player['Arrets'])}", f"{row_player['Arrets_PM']:.1f} / match")
        pdf.draw_kpi_card(sx + card_w + sp, start_y, card_w, card_h, "% Arrets", f"{row_player['Pct_Arrets']:.1f}%", "Efficacite")
        pdf.draw_kpi_card(sx + (card_w + sp)*2, start_y, card_w, card_h, "Relances", f"{int(row_player['Passes_D'])}", f"{row_player['PassesD_PM']:.1f} / match")
        pdf.draw_kpi_card((120 - card_w) / 2, start_y + card_h + 3, card_w, card_h, "Sanctions", f"{int(row_player['Sanctions_2min'])}", f"{row_player['Sanctions_PM']:.1f} / match")

    return bytes(pdf.output())

# --- INTERFACE DE TÉLÉCHARGEMENT ---
st.markdown("---")
st.subheader("📄 Consulter et exporter le rapport d'une joueuse")

col1, col2 = st.columns([2, 1])
with col1:
    joueuse_sel = st.selectbox("Sélectionner une joueuse :", df_top["Nom_Joueuse"].head(top_n).tolist())

with col2:
    if joueuse_sel:
        row_p = df[df["Nom_Joueuse"] == joueuse_sel].iloc[0]
        raw_m = df_raw[df_raw["Nom_Joueuse"] == joueuse_sel]
        pdf_bytes = build_pdf_in_memory(row_p, raw_m)
        
        st.download_button(
            label=f"⬇️ Télécharger la fiche PDF de {joueuse_sel}",
            data=pdf_bytes,
            file_name=f"Fiche_{joueuse_sel.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
