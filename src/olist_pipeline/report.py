"""Graphiques du rapport (français et anglais) et résultats chiffrés, à partir de la couche marts.

- docs/livraison/figures/<langue>/*.png
- docs/livraison/resultats.md (régénéré à chaque exécution)

    docker compose run --rm -v ./docs:/app/docs dagster python -m olist_pipeline.report
"""

from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .config import PROJECT_DIR, WAREHOUSE_PATH  # noqa: E402

DELIVERY_DIR = PROJECT_DIR / "docs" / "livraison"
FIGURES_DIR = DELIVERY_DIR / "figures"
INK, INK_SECONDARY, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"   # palette des projets précédents
MUTED = "#b9b8b3"
# Catégories qui correspondent à l'offre de Maison Caju (linge de maison, décoration, maison)
CLIENT_CATEGORIES = {"bed_bath_table", "furniture_decor", "housewares", "home_construction", "home_comfort_2",
                     "home_appliances", "furniture_living_room", "kitchen_dining_laundry_garden_furniture"}

LABELS = {
    "fr": {
        "q1_title": "Q1 · Chiffre d'affaires par catégorie (top 12, 2016-2018)",
        "q1_x": "Chiffre d'affaires (millions de BRL)", "q1_legend": "Univers de Maison Caju",
        "q1b_title": "Q1 · Chiffre d'affaires mensuel : le Black Friday 2017 est le record",
        "q1b_y": "Millions de BRL", "black_friday": "Black Friday\n(nov. 2017)",
        "q1c_title": "Q1 · Trois États font 63 % du chiffre d'affaires",
        "q1c_x": "Part du chiffre d'affaires",
        "q2_title": "Q2 · Après le premier achat, presque aucun client ne revient",
        "q2_x": "Mois après le premier achat", "q2_y": "Part de la cohorte qui recommande",
        "q3_title": "Q3 · Au-delà de 3 jours de retard, la note s'effondre",
        "q3_y": "Note moyenne (1 à 5)", "q3_low": "{:.0%} d'avis\nà 1-2 étoiles",
        "q4_title": "Q4 · Plus de versements, panier plus gros (carte bancaire)",
        "q4_y": "Panier moyen (BRL)", "q4_x": "Nombre de versements", "q4_orders": "{:,} commandes",
        "q5_title": "Q5 · Le fret pèse jusqu'à deux fois plus dans le Nord et le Nord-Est",
        "q5_x": "Fret / prix des articles",
        "delay": ["15 j d'avance\nou +", "8-14 j\nd'avance", "0-7 j\nd'avance", "1-3 j\nde retard",
                  "4-7 j\nde retard", "8-14 j\nde retard", "15 j de\nretard ou +"],
        "pct": lambda v: f"{v:.0%}".replace("%", " %"), "thousands": " ",
        "pct1": lambda v: f"{v:.1%}".replace(".", ",").replace("%", " %"),
        "pct2": lambda v: f"{v:.2%}".replace(".", ",").replace("%", " %"),
    },
    "en": {
        "q1_title": "Q1 · Revenue by category (top 12, 2016-2018)",
        "q1_x": "Revenue (BRL million)", "q1_legend": "Maison Caju's product range",
        "q1b_title": "Q1 · Monthly revenue: Black Friday 2017 is the record",
        "q1b_y": "BRL million", "black_friday": "Black Friday\n(Nov 2017)",
        "q1c_title": "Q1 · Three states generate 63% of revenue",
        "q1c_x": "Share of revenue",
        "q2_title": "Q2 · After the first purchase, almost no customer comes back",
        "q2_x": "Months after first purchase", "q2_y": "Share of the cohort ordering again",
        "q3_title": "Q3 · Beyond 3 days late, ratings collapse",
        "q3_y": "Average rating (1 to 5)", "q3_low": "{:.0%} of\n1-2 star reviews",
        "q4_title": "Q4 · More instalments, bigger baskets (credit card)",
        "q4_y": "Average order value (BRL)", "q4_x": "Number of instalments", "q4_orders": "{:,} orders",
        "q5_title": "Q5 · Freight weighs up to twice as much in the North and Northeast",
        "q5_x": "Freight / item price",
        "delay": ["15+ days\nearly", "8-14 days\nearly", "0-7 days\nearly", "1-3 days\nlate",
                  "4-7 days\nlate", "8-14 days\nlate", "15+ days\nlate"],
        "pct": lambda v: f"{v:.0%}", "thousands": ",",
        "pct1": lambda v: f"{v:.1%}", "pct2": lambda v: f"{v:.2%}",
    },
}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_SECONDARY, "axes.titlecolor": INK,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": INK_SECONDARY, "ytick.color": INK_SECONDARY, "font.size": 9, "legend.frameon": False,
})

# Régions du Brésil (IBGE), pour colorer le fret par grande région
REGIONS = {
    "Nord": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"], "Nord-Est": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centre-Ouest": ["DF", "GO", "MT", "MS"], "Sud-Est": ["ES", "MG", "RJ", "SP"], "Sud": ["PR", "RS", "SC"],
}
REGION_EN = {"Nord": "North", "Nord-Est": "Northeast", "Centre-Ouest": "Center-West", "Sud-Est": "Southeast", "Sud": "South"}
REGION_COLORS = {"Nord": ORANGE, "Nord-Est": YELLOW, "Centre-Ouest": AQUA, "Sud-Est": BLUE, "Sud": "#7b5ea7"}


def load(con) -> dict[str, pd.DataFrame]:
    q = lambda sql: con.execute(sql).df()  # noqa: E731
    return {
        "categories": q("""select category, sum(revenue) as revenue from marts.rpt_revenue_monthly
                           group by 1 order by 2 desc"""),
        "monthly": q("""select purchase_month, sum(revenue) as revenue, sum(orders) as orders
                        from marts.rpt_revenue_monthly group by 1 order by 1"""),
        "states": q("""select customer_state, sum(revenue) as revenue from marts.rpt_revenue_monthly
                       group by 1 order by 2 desc"""),
        "retention": q("""select months_since_first, sum(active_customers) / sum(cohort_customers) as rate
                          from marts.rpt_cohort_retention
                          where cohort_month between '2017-01-01' and '2017-12-01' and months_since_first between 1 and 12
                            -- une cohorte ne compte pour le mois N que si elle a pu être observée N mois
                            -- (fin des données complètes : août 2018)
                            and cohort_month + to_months(months_since_first) <= date '2018-08-01'
                          group by 1 order by 1"""),
        "loyalty": q("""select count(*) as customers, avg(is_repeat_customer::int) as repeat_share,
                               median(days_to_second_order) as median_days, sum(is_repeat_customer::int) as repeaters
                        from marts.dim_customers where valid_orders > 0"""),
        "delivery": q("select * from marts.rpt_delivery_satisfaction order by bucket_order"),
        "late": q("""select avg(is_late::int) as late_share, count(*) as orders,
                            avg(review_score) filter (where not is_late) as score_on_time,
                            avg(review_score) filter (where is_late) as score_late
                     from marts.fct_orders where is_late is not null"""),
        "payments": q("""select main_payment_type, sum(orders) as orders, sum(total_paid) / sum(orders) as aov
                         from marts.rpt_payments group by 1 order by 2 desc"""),
        "installments": q("""select installments_bucket, orders, avg_order_value from marts.rpt_payments
                             where main_payment_type = 'credit_card'"""),
        "freight": q("select * from marts.rpt_freight_by_state order by freight_to_price_ratio desc"),
        "totals": q("""select sum(items_value) as revenue, count(*) as orders, sum(freight_value) as freight,
                              avg(review_score) as score
                       from marts.fct_orders where is_valid"""),
    }


def _save(fig, folder: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(folder / f"{name}.png", dpi=200)
    plt.close(fig)


def figures(d: dict[str, pd.DataFrame], lang: str) -> None:
    t = LABELS[lang]
    folder = FIGURES_DIR / lang
    folder.mkdir(parents=True, exist_ok=True)

    # Q1 · catégories, avec l'univers du client mis en avant
    top = d["categories"].head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    colors = [ORANGE if c in CLIENT_CATEGORIES else MUTED for c in top["category"]]
    ax.barh(top["category"], top["revenue"] / 1e6, color=colors)
    ax.set_title(t["q1_title"])
    ax.set_xlabel(t["q1_x"])
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=ORANGE)], labels=[t["q1_legend"]], loc="lower right")
    _save(fig, folder, "q1_ca_par_categorie")

    # Q1 · série mensuelle (mois complets : janvier 2017 à août 2018)
    m = d["monthly"]
    m = m[(m["purchase_month"] >= "2017-01-01") & (m["purchase_month"] <= "2018-08-01")]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.plot(m["purchase_month"], m["revenue"] / 1e6, color=BLUE, lw=2, marker="o", ms=3)
    peak = m.loc[m["revenue"].idxmax()]
    ax.annotate(t["black_friday"], (peak["purchase_month"], peak["revenue"] / 1e6), xytext=(-130, -45),
                textcoords="offset points", color=ORANGE, fontweight="bold",
                arrowprops={"arrowstyle": "->", "color": ORANGE})
    ax.set_title(t["q1b_title"])
    ax.set_ylabel(t["q1b_y"])
    ax.set_ylim(0)
    _save(fig, folder, "q1b_ca_mensuel")

    # Q1 · États
    s = d["states"].copy()
    s["share"] = s["revenue"] / s["revenue"].sum()
    s = s.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.barh(s["customer_state"], s["share"], color=[BLUE if i >= 7 else MUTED for i in range(len(s))])
    for y, v in enumerate(s["share"]):
        ax.text(v + 0.004, y, t["pct"](v), va="center", color=INK_SECONDARY)
    ax.xaxis.set_major_formatter(lambda v, _: t["pct"](v))
    ax.set_title(t["q1c_title"])
    ax.set_xlabel(t["q1c_x"])
    ax.grid(axis="y", visible=False)
    _save(fig, folder, "q1c_ca_par_etat")

    # Q2 · rétention
    r = d["retention"]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(r["months_since_first"], r["rate"], color=ORANGE)
    for x, v in zip(r["months_since_first"], r["rate"], strict=True):
        ax.text(x, v, t["pct2"](v), ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(r["months_since_first"])
    ax.yaxis.set_major_formatter(lambda v, _: t["pct1"](v))
    ax.set_title(t["q2_title"])
    ax.set_xlabel(t["q2_x"])
    ax.set_ylabel(t["q2_y"])
    ax.grid(axis="x", visible=False)
    _save(fig, folder, "q2_retention")

    # Q3 · note selon le retard
    dl = d["delivery"]
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = [AQUA if b <= 3 else ORANGE for b in dl["bucket_order"]]
    ax.bar(t["delay"], dl["avg_review_score"], color=colors)
    for x, (score, low) in enumerate(zip(dl["avg_review_score"], dl["low_score_share"], strict=True)):
        ax.text(x, score + 0.05, f"{score:.1f}".replace(".", "," if lang == "fr" else "."), ha="center", fontweight="bold")
        ax.text(x, 0.35, t["q3_low"].format(low).replace("%", " %" if lang == "fr" else "%"), ha="center",
                color="white", fontsize=7)
    ax.set_ylim(0, 5)
    ax.set_title(t["q3_title"])
    ax.set_ylabel(t["q3_y"])
    ax.grid(axis="x", visible=False)
    _save(fig, folder, "q3_note_selon_retard")

    # Q4 · versements
    order = ["1x", "2-3x", "4-6x", "7-10x", "11x+"]
    ins = d["installments"].set_index("installments_bucket").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.bar(ins["installments_bucket"], ins["avg_order_value"], color=BLUE)
    for x, (v, n) in enumerate(zip(ins["avg_order_value"], ins["orders"], strict=True)):
        ax.text(x, v + 5, f"R$ {v:.0f}", ha="center", fontweight="bold")
        ax.text(x, 12, t["q4_orders"].format(int(n)).replace(",", t["thousands"]), ha="center", color="white", fontsize=7.5)
    ax.set_title(t["q4_title"])
    ax.set_ylabel(t["q4_y"])
    ax.set_xlabel(t["q4_x"])
    ax.grid(axis="x", visible=False)
    _save(fig, folder, "q4_paiement_versements")

    # Q5 · fret par État, coloré par région
    f = d["freight"].iloc[::-1]
    region_of = {s: r for r, states in REGIONS.items() for s in states}
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(f["customer_state"], f["freight_to_price_ratio"], color=[REGION_COLORS[region_of[s]] for s in f["customer_state"]])
    ax.xaxis.set_major_formatter(lambda v, _: t["pct"](v))
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in REGION_COLORS.values()]
    names = list(REGION_COLORS) if lang == "fr" else [REGION_EN[r] for r in REGION_COLORS]
    ax.legend(handles, names, loc="lower right")
    ax.set_title(t["q5_title"])
    ax.set_xlabel(t["q5_x"])
    ax.grid(axis="y", visible=False)
    _save(fig, folder, "q5_fret_par_etat")


def results_markdown(d: dict[str, pd.DataFrame]) -> str:
    tot, loy, late = d["totals"].iloc[0], d["loyalty"].iloc[0], d["late"].iloc[0]
    s = d["states"].assign(share=lambda x: x["revenue"] / x["revenue"].sum())
    cats = d["categories"].assign(share=lambda x: x["revenue"] / x["revenue"].sum())
    client = cats[cats["category"].isin(CLIENT_CATEGORIES)]
    lines = [
        "# Résultats chiffrés (générés par `olist_pipeline.report`)",
        "",
        "> Fichier régénéré à chaque exécution, à partir de la couche marts. Ne pas modifier à la main.",
        "",
        "## Totaux (commandes valides)",
        f"- Chiffre d'affaires : **{tot.revenue:,.2f} BRL** (hors fret) ; fret : {tot.freight:,.2f} BRL",
        f"- Commandes : **{tot.orders:,.0f}** ; panier moyen : {tot.revenue / tot.orders:,.2f} BRL ; "
        f"note moyenne : {tot.score:.2f}",
        "",
        "## Q1 · Catégories, États, saisonnalité",
        "| Catégorie | CA (BRL) | Part |", "|---|---:|---:|",
        *[f"| {r.category} | {r.revenue:,.0f} | {r.share:.1%} |" for r in cats.head(10).itertuples()],
        "",
        f"Univers de Maison Caju ({', '.join(sorted(client['category']))}) : **{client['share'].sum():.1%}** du CA.",
        "",
        "| État | CA (BRL) | Part |", "|---|---:|---:|",
        *[f"| {r.customer_state} | {r.revenue:,.0f} | {r.share:.1%} |" for r in s.head(5).itertuples()],
        "",
        "## Q2 · Fidélité",
        f"- Clients réels : {loy.customers:,.0f} ; clients fidèles (2 commandes valides ou plus) : "
        f"**{loy.repeaters:,.0f} ({loy.repeat_share:.2%})**",
        f"- Délai médian avant la deuxième commande : {loy.median_days:.0f} jours",
        "", "| Mois après le 1er achat | Part de la cohorte (2017) qui recommande |", "|---:|---:|",
        *[f"| {int(r.months_since_first)} | {r.rate:.2%} |" for r in d["retention"].itertuples()],
        "",
        "## Q3 · Livraison et satisfaction",
        f"- Commandes livrées en retard : **{late.late_share:.1%}** ; note moyenne à l'heure : {late.score_on_time:.2f}, "
        f"en retard : {late.score_late:.2f}",
        "", "| Retard | Commandes | Note moyenne | Avis à 1-2 étoiles |", "|---|---:|---:|---:|",
        *[f"| {r.delay_bucket} | {r.orders:,} | {r.avg_review_score:.2f} | {r.low_score_share:.1%} |"
          for r in d["delivery"].itertuples()],
        "",
        "## Q4 · Paiement",
        "| Mode principal | Commandes | Part | Panier moyen (BRL) |", "|---|---:|---:|---:|",
        *[f"| {r.main_payment_type} | {r.orders:,.0f} | {r.orders / d['payments']['orders'].sum():.1%} | {r.aov:,.2f} |"
          for r in d["payments"].itertuples()],
        "",
        "## Q5 · Fret par État",
        "| État | Commandes | Fret / prix | Délai moyen (j) | Part en retard | Note |", "|---|---:|---:|---:|---:|---:|",
        *[f"| {r.customer_state} | {r.orders:,} | {r.freight_to_price_ratio:.1%} | {r.avg_delivery_days:.1f} | "
          f"{r.late_share:.1%} | {r.avg_review_score:.2f} |" for r in d["freight"].itertuples()],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    with duckdb.connect(str(WAREHOUSE_PATH), read_only=True) as con:
        data = load(con)
    for lang in LABELS:
        figures(data, lang)
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    (DELIVERY_DIR / "resultats.md").write_text(results_markdown(data), encoding="utf-8")
    print(f"Graphiques : {FIGURES_DIR} ; résultats : {DELIVERY_DIR / 'resultats.md'}")


if __name__ == "__main__":
    main()
