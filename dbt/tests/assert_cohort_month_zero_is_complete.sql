-- Par définition, 100 % d'une cohorte est active le mois de son premier achat (mois 0).
-- Sinon, la cohorte et l'activité ne sont pas calculées sur les mêmes clients.
select *
from {{ ref('rpt_cohort_retention') }}
where months_since_first = 0
  and active_customers <> cohort_customers
