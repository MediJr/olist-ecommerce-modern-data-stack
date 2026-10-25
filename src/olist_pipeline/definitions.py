"""Orchestration Dagster : ce que le pipeline produit (assets), quand il le produit (capteurs), et avec quoi.

    dagster dev            # interface sur http://127.0.0.1:3000 (voir le README)

Dagster raisonne en ASSETS (les données produites) plutôt qu'en tâches : chaque table du lac et chaque modèle dbt
est un asset, avec ses dépendances, son historique et ses contrôles. Le graphe complet va de la livraison CSV
jusqu'aux tables lues par le tableau de bord.
"""

import json
from pathlib import Path

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    BackfillPolicy,
    DefaultSensorStatus,
    Definitions,
    DynamicPartitionsDefinition,
    MaterializeResult,
    RunRequest,
    SensorEvaluationContext,
    SensorResult,
    SkipReason,
    asset,
    define_asset_job,
    in_process_executor,
    sensor,
)
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

from . import bronze, landing
from .config import DBT_DIR, LANDING_DIR, MONTHLY_TABLES, REFERENCE_FOLDER, REFERENCE_TABLES, TableSpec
from .dbt_cli import dbt_environment

dbt_environment()      # .env, chemin de l'entrepôt et emplacement du lac, pour dbt lancé par Dagster

# --------------------------------------------------------------------------------------------- partitions
# Une partition = une livraison REÇUE. Partitions dynamiques : c'est le capteur qui les crée à l'arrivée
# d'un dossier, plutôt qu'un calendrier fixé à l'avance qui afficherait des mois « manquants ».
deliveries = DynamicPartitionsDefinition(name="delivery_month")

WAREHOUSE_TAG = {
    "olist/warehouse": "duckdb",       # DuckDB n'accepte qu'un écrivain : une seule exécution à la fois (dagster.yaml)
    "dagster/max_runtime": "900",      # au-delà de 15 min, l'exécution est arrêtée : un blocage ne retient plus la file
}


# --------------------------------------------------------------------------------------------- couche bronze
def _bronze_asset(spec: TableSpec, monthly: bool):
    @asset(
        key=AssetKey(["bronze", spec.name]),
        group_name="bronze" if monthly else "reference",
        partitions_def=deliveries if monthly else None,
        # Rattrapage de plusieurs mois = UNE seule exécution (et donc un seul dbt build), pas une par mois.
        backfill_policy=BackfillPolicy.single_run() if monthly else None,
        kinds={"parquet", "s3"},
        description=f"{spec.source_file} livré par le partenaire, copié tel quel en Parquet (contrat vérifié).",
    )
    def _ingest(context: AssetExecutionContext) -> MaterializeResult:
        months = context.partition_keys if monthly else [None]
        results = [bronze.ingest(spec, month) for month in months]
        for r in results:
            context.log.info(f"{spec.name} {r.month or REFERENCE_FOLDER} : {r.rows:,} lignes → {r.path}")
        return MaterializeResult(
            metadata={
                "rows": sum(r.rows for r in results),
                "deliveries": len(results),
                "path": results[-1].path,
                "source_sha256": results[-1].sha256,
            }
        )

    return _ingest


monthly_bronze_assets = [_bronze_asset(spec, monthly=True) for spec in MONTHLY_TABLES]
reference_assets = [_bronze_asset(spec, monthly=False) for spec in REFERENCE_TABLES]


# --------------------------------------------------------------------------------------------- dbt
dbt_project = DbtProject(project_dir=DBT_DIR, profiles_dir=DBT_DIR)
dbt_project.prepare_if_dev()     # en développement, Dagster lance « dbt parse » pour lire le manifeste à jour


class OlistTranslator(DagsterDbtTranslator):
    """Range chaque modèle dbt dans le groupe de sa couche : staging, intermediate ou marts."""

    def get_group_name(self, dbt_resource_props: dict) -> str | None:
        if dbt_resource_props["resource_type"] == "model":
            return dbt_resource_props["fqn"][1]
        return super().get_group_name(dbt_resource_props)


@dbt_assets(manifest=dbt_project.manifest_path, dagster_dbt_translator=OlistTranslator())
def olist_dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    # « build » = modèles + tests, dans l'ordre du graphe : un test en échec arrête les modèles qui en dépendent.
    # Chaque test dbt apparaît dans Dagster comme un contrôle (asset check) de son modèle.
    yield from dbt.cli(["build"], context=context).stream()


# --------------------------------------------------------------------------------------------- jobs
monthly_delivery_job = define_asset_job(
    "monthly_delivery",
    selection=AssetSelection.assets(*monthly_bronze_assets) | AssetSelection.assets(olist_dbt_models),
    partitions_def=deliveries,
    tags=WAREHOUSE_TAG,
    executor_def=in_process_executor,
    description="Une livraison mensuelle : contrat, couche bronze, puis reconstruction et tests dbt.",
)

reference_job = define_asset_job(
    "reference_refresh",
    selection=AssetSelection.assets(*reference_assets) | AssetSelection.assets(olist_dbt_models),
    tags=WAREHOUSE_TAG,
    executor_def=in_process_executor,
    description="Nouveaux référentiels (produits, vendeurs, catégories, géolocalisation), puis dbt.",
)

# Amorçage : tant qu'aucun mois n'est dans le lac, dbt n'a rien à lire. On charge alors les référentiels seuls.
reference_bootstrap_job = define_asset_job(
    "reference_bootstrap",
    selection=AssetSelection.assets(*reference_assets),
    tags=WAREHOUSE_TAG,
    executor_def=in_process_executor,
    description="Premier dépôt des référentiels, avant toute livraison mensuelle : couche bronze seulement.",
)

ORDERS_KEY = AssetKey(["bronze", "orders"])
PRODUCTS_KEY = AssetKey(["bronze", "products"])


# --------------------------------------------------------------------------------------------- capteurs
def _changed_deliveries(context: SensorEvaluationContext, folders: list[Path]) -> tuple[list[tuple[str, int]], str]:
    """Livraisons nouvelles OU relivrées depuis la dernière évaluation (date du marqueur _SUCCESS)."""
    seen = json.loads(context.cursor) if context.cursor else {}
    changed = []
    for folder in folders:
        stamp = int((folder / landing.SUCCESS_MARKER).stat().st_mtime)
        if seen.get(folder.name) != stamp:
            changed.append((folder.name, stamp))
            seen[folder.name] = stamp
    return changed, json.dumps(seen)


@sensor(job=monthly_delivery_job, minimum_interval_seconds=30, default_status=DefaultSensorStatus.RUNNING)
def landing_sensor(context: SensorEvaluationContext):
    """Surveille la zone de dépôt : chaque dossier mensuel complet (_SUCCESS) déclenche son traitement."""
    # Prérequis : dbt joint chaque commande à son produit et à son vendeur. Sans référentiels, on attend.
    if not context.instance.get_latest_materialization_event(PRODUCTS_KEY):
        return SkipReason("En attente du premier chargement des référentiels")
    folders = [LANDING_DIR / m for m in landing.delivered_months()]
    changed, cursor = _changed_deliveries(context, folders)
    if not changed:
        return SkipReason("Aucune nouvelle livraison mensuelle")
    months = [m for m, _ in changed]
    known = set(context.instance.get_dynamic_partitions(deliveries.name))
    return SensorResult(
        # run_key : une même version de livraison n'est jamais traitée deux fois, même si le capteur repasse.
        run_requests=[RunRequest(partition_key=m, run_key=f"{m}@{stamp}") for m, stamp in changed],
        dynamic_partitions_requests=[deliveries.build_add_request([m for m in months if m not in known])],
        cursor=cursor,
    )


@sensor(jobs=[reference_job, reference_bootstrap_job], minimum_interval_seconds=30,
        default_status=DefaultSensorStatus.RUNNING)
def reference_sensor(context: SensorEvaluationContext):
    """Recharge les référentiels quand une nouvelle version complète est déposée."""
    folder = LANDING_DIR / REFERENCE_FOLDER
    if not landing.is_complete(folder):
        return SkipReason("Pas de référentiel complet déposé")
    changed, cursor = _changed_deliveries(context, [folder])
    if not changed:
        return SkipReason("Référentiels inchangés")
    has_orders = context.instance.get_latest_materialization_event(ORDERS_KEY) is not None
    job = reference_job if has_orders else reference_bootstrap_job
    return SensorResult(run_requests=[RunRequest(run_key=f"reference@{changed[0][1]}", job_name=job.name)], cursor=cursor)


defs = Definitions(
    assets=[*monthly_bronze_assets, *reference_assets, olist_dbt_models],
    jobs=[monthly_delivery_job, reference_job, reference_bootstrap_job],
    sensors=[landing_sensor, reference_sensor],
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
)
