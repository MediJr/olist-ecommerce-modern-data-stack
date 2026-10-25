"""Tableau de bord du comité de direction de Maison Caju : le e-commerce brésilien en cinq questions.

    streamlit run dashboard/app.py         # http://127.0.0.1:8501

Il ne lit QUE la couche marts, déjà calculée et testée par dbt. Chaque requête ouvre l'entrepôt en lecture seule
puis le referme aussitôt : le tableau de bord ne bloque jamais une reconstruction dbt (DuckDB n'accepte qu'un écrivain).
"""

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

from olist_pipeline.config import WAREHOUSE_PATH

TEXT = {
    "fr": {
        "title": "Le e-commerce brésilien en cinq questions",
        "subtitle": "Étude de marché pour Maison Caju · données Olist 2016-2018 · montants en réais (BRL), hors fret",
        "period": "Période", "states": "États du client (vide = tous)",
        "revenue": "Chiffre d'affaires", "orders": "Commandes", "aov": "Panier moyen",
        "customers": "Clients", "repeat": "Clients fidèles", "score": "Note moyenne",
        "tabs": ["Q1 · Ventes", "Q2 · Fidélité", "Q3 · Livraison", "Q4 · Paiement", "Q5 · Fret"],
        "q1": "Quelles catégories et quels États font le chiffre d'affaires ?",
        "monthly": "Chiffre d'affaires mensuel", "top_cat": "Top 15 des catégories", "by_state": "Par État",
        "q2": "Les clients reviennent-ils acheter ?",
        "repeat_note": "Un client = customer_unique_id. Fidèle = au moins deux commandes valides.",
        "median_days": "Délai médian avant la 2e commande (jours)",
        "retention": "Part d'une cohorte qui recommande N mois après son premier achat (%)",
        "q3": "Le retard de livraison dégrade-t-il la note ?",
        "avg_score": "Note moyenne (1 à 5)", "low_share": "Part d'avis à 1 ou 2 étoiles",
        "q4": "Comment les clients paient-ils ?",
        "pay_share": "Mode de paiement principal", "installments": "Panier moyen selon le nombre de versements (carte)",
        "q5": "Combien pèse le fret selon la région ?",
        "freight_ratio": "Fret / prix des articles (%)", "delivery_days": "Délai moyen de livraison (jours)",
        "source": "Source : Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0). Scénario client fictif.",
        "delay": {"early_15d_plus": "15 j d'avance ou +", "early_8_14d": "8-14 j d'avance",
                  "early_1_7d_or_on_time": "0-7 j d'avance", "late_1_3d": "1-3 j de retard",
                  "late_4_7d": "4-7 j de retard", "late_8_14d": "8-14 j de retard", "late_15d_plus": "15 j de retard ou +"},
    },
    "en": {
        "title": "Brazilian e-commerce in five questions",
        "subtitle": "Market study for Maison Caju · Olist data 2016-2018 · amounts in reais (BRL), excluding freight",
        "period": "Period", "states": "Customer states (empty = all)",
        "revenue": "Revenue", "orders": "Orders", "aov": "Average order value",
        "customers": "Customers", "repeat": "Repeat customers", "score": "Average rating",
        "tabs": ["Q1 · Sales", "Q2 · Loyalty", "Q3 · Delivery", "Q4 · Payment", "Q5 · Freight"],
        "q1": "Which categories and states drive revenue?",
        "monthly": "Monthly revenue", "top_cat": "Top 15 categories", "by_state": "By state",
        "q2": "Do customers come back?",
        "repeat_note": "A customer = customer_unique_id. Repeat = at least two valid orders.",
        "median_days": "Median days to second order",
        "retention": "Share of a cohort ordering again N months after its first purchase (%)",
        "q3": "Does late delivery hurt the rating?",
        "avg_score": "Average rating (1 to 5)", "low_share": "Share of 1-2 star reviews",
        "q4": "How do customers pay?",
        "pay_share": "Main payment method", "installments": "Average order value by number of instalments (card)",
        "q5": "How much does freight weigh by region?",
        "freight_ratio": "Freight / item price (%)", "delivery_days": "Average delivery time (days)",
        "source": "Source: Brazilian E-Commerce Public Dataset by Olist (Kaggle, CC BY-NC-SA 4.0). Fictional client scenario.",
        "delay": {"early_15d_plus": "15+ days early", "early_8_14d": "8-14 days early",
                  "early_1_7d_or_on_time": "0-7 days early", "late_1_3d": "1-3 days late",
                  "late_4_7d": "4-7 days late", "late_8_14d": "8-14 days late", "late_15d_plus": "15+ days late"},
    },
}

ACCENT = "#C8553D"     # couleur de la marque fictive (terre cuite)


@st.cache_data(ttl=300, show_spinner=False)
def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Lecture seule, connexion ouverte et refermée à chaque requête (mise en cache 5 minutes)."""
    with duckdb.connect(str(WAREHOUSE_PATH), read_only=True) as con:
        return con.execute(sql, list(params)).df()


def number(value: float, lang: str, decimals: int = 0) -> str:
    """1 234,5 en français, 1,234.5 en anglais."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", " ").replace(".", ",") if lang == "fr" else text


def brl(value: float, lang: str) -> str:
    return f"R$ {number(value / 1e6, lang, 2)} M" if value >= 1e6 else f"R$ {number(value, lang)}"


def percent(value: float, lang: str, decimals: int = 1) -> str:
    return number(value * 100, lang, decimals) + (" %" if lang == "fr" else "%")


def main() -> None:
    st.set_page_config(page_title="Maison Caju · Brasil", page_icon="🛋️", layout="wide")
    lang = st.sidebar.radio("Langue / Language", ["fr", "en"], format_func=lambda x: {"fr": "Français", "en": "English"}[x])
    t = TEXT[lang]

    if not WAREHOUSE_PATH.exists():
        st.error("Entrepôt introuvable : lancez d'abord le pipeline (voir le README).")
        st.stop()

    months = query("select distinct purchase_month from marts.rpt_revenue_monthly order by 1")["purchase_month"]
    months = [m.strftime("%Y-%m") for m in pd.to_datetime(months)]
    # Par défaut : les mois complets (janvier 2017 à août 2018) s'ils existent, sinon toute la période disponible.
    default = ("2017-01" if "2017-01" in months else months[0], "2018-08" if "2018-08" in months else months[-1])
    start, end = st.sidebar.select_slider(t["period"], options=months, value=default)
    all_states = query("select distinct customer_state from marts.rpt_freight_by_state order by 1")["customer_state"].tolist()
    states = st.sidebar.multiselect(t["states"], all_states) or all_states
    st.sidebar.caption(t["source"])

    period = (f"{start}-01", f"{end}-01")
    state_filter = "customer_state in (select unnest(?::varchar[]))"

    st.title(t["title"])
    st.caption(t["subtitle"])

    kpi = query(
        f"""
        select sum(items_value) as revenue, count(*) as orders, avg(review_score) as score
        from marts.fct_orders
        where is_valid and purchase_month between ?::date and ?::date and {state_filter}
        """,
        (*period, states),
    ).iloc[0]
    loyalty = query(
        f"""
        select count(*) as customers, avg(is_repeat_customer::int) as repeat_share, median(days_to_second_order) as days
        from marts.dim_customers
        where cohort_month between ?::date and ?::date and {state_filter}
        """,
        (*period, states),
    ).iloc[0]

    row1, row2 = st.columns(3, border=True), st.columns(3, border=True)
    row1[0].metric(t["revenue"], brl(kpi.revenue, lang))
    row1[1].metric(t["orders"], number(kpi.orders, lang))
    row1[2].metric(t["aov"], brl(kpi.revenue / kpi.orders, lang))
    row2[0].metric(t["customers"], number(loyalty.customers, lang))
    row2[1].metric(t["repeat"], percent(loyalty.repeat_share, lang))
    row2[2].metric(t["score"], f"{number(kpi.score, lang, 2)} / 5")

    tabs = st.tabs(t["tabs"])

    # --- Q1 ------------------------------------------------------------------------------------------------
    with tabs[0]:
        st.subheader(t["q1"])
        revenue = query(
            f"""select * from marts.rpt_revenue_monthly
                where purchase_month between ?::date and ?::date and {state_filter}""",
            (*period, states),
        )
        monthly = revenue.groupby("purchase_month", as_index=False)["revenue"].sum()
        st.altair_chart(
            alt.Chart(monthly, title=t["monthly"]).mark_area(color=ACCENT, opacity=0.8).encode(
                x=alt.X("purchase_month:T", title=None), y=alt.Y("revenue:Q", title="BRL")
            ),
            use_container_width=True,
        )
        left, right = st.columns(2)
        top = revenue.groupby("category", as_index=False)["revenue"].sum().nlargest(15, "revenue")
        left.altair_chart(
            alt.Chart(top, title=t["top_cat"]).mark_bar(color=ACCENT).encode(
                x=alt.X("revenue:Q", title="BRL"), y=alt.Y("category:N", sort="-x", title=None)
            ),
            use_container_width=True,
        )
        by_state = revenue.groupby("customer_state", as_index=False)["revenue"].sum().nlargest(15, "revenue")
        right.altair_chart(
            alt.Chart(by_state, title=t["by_state"]).mark_bar(color="#5B7553").encode(
                x=alt.X("revenue:Q", title="BRL"), y=alt.Y("customer_state:N", sort="-x", title=None)
            ),
            use_container_width=True,
        )

    # --- Q2 ------------------------------------------------------------------------------------------------
    with tabs[1]:
        st.subheader(t["q2"])
        st.caption(t["repeat_note"])
        c1, c2 = st.columns(2, border=True)
        c1.metric(t["repeat"], percent(loyalty.repeat_share, lang))
        c2.metric(t["median_days"], number(loyalty.days, lang))
        cohorts = query(
            """select strftime(cohort_month, '%Y-%m') as cohort, months_since_first, retention_rate * 100 as pct
               from marts.rpt_cohort_retention
               where months_since_first between 1 and 12 and cohort_month between ?::date and ?::date""",
            period,
        )
        st.altair_chart(
            alt.Chart(cohorts, title=t["retention"]).mark_rect().encode(
                x=alt.X("months_since_first:O", title="N"),
                y=alt.Y("cohort:O", title=None),
                color=alt.Color("pct:Q", scale=alt.Scale(scheme="oranges"), title="%"),
                tooltip=["cohort", "months_since_first", alt.Tooltip("pct:Q", format=".2f")],
            ),
            use_container_width=True,
        )

    # --- Q3 ------------------------------------------------------------------------------------------------
    with tabs[2]:
        st.subheader(t["q3"])
        delivery = query("select * from marts.rpt_delivery_satisfaction order by bucket_order")
        delivery["label"] = delivery["delay_bucket"].map(t["delay"])
        order = delivery["label"].tolist()
        left, right = st.columns(2)
        left.altair_chart(
            alt.Chart(delivery, title=t["avg_score"]).mark_bar().encode(
                x=alt.X("label:N", sort=order, title=None),
                y=alt.Y("avg_review_score:Q", scale=alt.Scale(domain=[1, 5]), title=None),
                color=alt.condition("datum.bucket_order >= 4", alt.value(ACCENT), alt.value("#5B7553")),
            ),
            use_container_width=True,
        )
        right.altair_chart(
            alt.Chart(delivery, title=t["low_share"]).mark_bar().encode(
                x=alt.X("label:N", sort=order, title=None),
                y=alt.Y("low_score_share:Q", axis=alt.Axis(format="%"), title=None),
                color=alt.condition("datum.bucket_order >= 4", alt.value(ACCENT), alt.value("#5B7553")),
            ),
            use_container_width=True,
        )

    # --- Q4 ------------------------------------------------------------------------------------------------
    with tabs[3]:
        st.subheader(t["q4"])
        payments = query("select * from marts.rpt_payments")
        share = payments.groupby("main_payment_type", as_index=False)["orders"].sum()
        left, right = st.columns(2)
        left.altair_chart(
            alt.Chart(share, title=t["pay_share"]).mark_arc(innerRadius=60).encode(
                theta="orders:Q", color=alt.Color("main_payment_type:N", title=None), tooltip=["main_payment_type", "orders"]
            ),
            use_container_width=True,
        )
        cards = payments[payments["main_payment_type"] == "credit_card"]
        right.altair_chart(
            alt.Chart(cards, title=t["installments"]).mark_bar(color=ACCENT).encode(
                x=alt.X("installments_bucket:N", sort=["1x", "2-3x", "4-6x", "7-10x", "11x+"], title=None),
                y=alt.Y("avg_order_value:Q", title="BRL"),
                tooltip=["installments_bucket", "orders", "avg_order_value"],
            ),
            use_container_width=True,
        )

    # --- Q5 ------------------------------------------------------------------------------------------------
    with tabs[4]:
        st.subheader(t["q5"])
        freight = query(f"select * from marts.rpt_freight_by_state where {state_filter}", (states,))
        freight["ratio_pct"] = freight["freight_to_price_ratio"] * 100
        left, right = st.columns(2)
        left.altair_chart(
            alt.Chart(freight, title=t["freight_ratio"]).mark_bar(color=ACCENT).encode(
                x=alt.X("ratio_pct:Q", title="%"), y=alt.Y("customer_state:N", sort="-x", title=None),
                tooltip=["customer_state", "orders", alt.Tooltip("ratio_pct:Q", format=".1f")],
            ),
            use_container_width=True,
        )
        right.altair_chart(
            alt.Chart(freight, title=t["delivery_days"]).mark_bar(color="#5B7553").encode(
                x=alt.X("avg_delivery_days:Q", title=None), y=alt.Y("customer_state:N", sort="-x", title=None),
            ),
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
