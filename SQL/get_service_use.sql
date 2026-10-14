WITH req_states AS (
    SELECT
        rrc."refundRequestId",
        bool_or(rrc."statusId" = 'f30116c9-661f-4caa-b2a5-78976dd729bc') AS pagado,
        bool_or(rrc."statusId" = 'f30116c9-661f-4caa-b2a5-78976dd729bb') AS aprobado
    FROM "refunds-requests-changelog" rrc
    GROUP BY rrc."refundRequestId"
)
SELECT
    s.id    AS "serviceId",
    s.title AS servicio,
    COUNT(*) FILTER (WHERE rs.aprobado AND NOT rs.pagado)            AS aprobados,
    COUNT(*) FILTER (WHERE rs.pagado)                               AS pagados,
    COUNT(*) FILTER (WHERE rs.pagado OR rs.aprobado)                AS total,
    trim_scale(COALESCE(SUM(rr."approvedAmount") FILTER (WHERE rs.aprobado AND NOT rs.pagado), 0)::numeric)::text AS monto_aprobado,
    trim_scale(COALESCE(SUM(rr."approvedAmount") FILTER (WHERE rs.pagado), 0)::numeric)::text                     AS monto_pagado,
    trim_scale(COALESCE(SUM(rr."approvedAmount") FILTER (WHERE rs.pagado OR rs.aprobado), 0)::numeric)::text      AS monto_total
FROM "refunds-requests" rr
INNER JOIN req_states rs ON rs."refundRequestId" = rr.id
INNER JOIN memberships m     ON rr."membershipId" = m.id
INNER JOIN "users-companies-access" uca ON uca.id = m."ucaId"
LEFT JOIN services s          ON s.id = rr."serviceId"
WHERE uca."companyId" = 'c4508fd0-6efd-11ef-9f50-49a44ea1a93c'
  AND (rs.pagado OR rs.aprobado)
GROUP BY s.id, s.title
ORDER BY servicio;