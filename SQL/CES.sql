-- Q(1) -> 20XX-01-01 <= X < 20XX-04-01
-- Q(2) -> 20XX-04-01 <= X < 20XX-07-01
-- Q(3) -> 20XX-07-01 <= X < 20XX-010-01
-- Q(4) -> 20XX-10-01 <= X < 20XX+1-01-01

-- CES Normal, solo el valor
select sum(c."value") / count(c.value) from ces c where c."createdAt" > '2025-09-30' and c."createdAt" < '2025-12-31'

-- CES por Pais y la cantidad por Q(X)
select c2."iso" country, sum(c.value)/count(c.value), count(*)
from ces c
left join memberships m 
	on m.id = c."membershipId"
left join "plans" p 
	on p.id = m."planId" 
left join countries c2 
	on c2.id = p."countryId" 
where m."acquisitionChannel" like '%b2c%'
	and c."createdAt" > '2025-09-30' 
	and c."createdAt" < '2025-12-31'
group by c2.iso 

-- CES por Pais y la cantidad Historica
select c3."iso", sum(c.value)/count(c.value), count(*)
from ces c
left join memberships m 
	on m.id = c."membershipId"
left join "plans" p 
	on p.id = m."planId"
left join users u
	on u."mongoId" = m."userId" 
left join "users-companies-access" uca 
	on uca."userId" = u."mongoId" 
left join companies c2
	on c2.id = uca."companyId"
left join countries c3 
	on c3.id = p."countryId" 
--	and c."createdAt" > '2025-09-30' 
--	and c."createdAt" < '2025-12-31'
group by c3."iso"


-- CES por Empresa y la cantidad Historica
select c2."name", sum(c.value)/count(c.value) as ces, count(*)
from ces c
left join memberships m 
	on m.id = c."membershipId"
left join "plans" p 
	on p.id = m."planId"
left join users u
	on u."mongoId" = m."userId" 
left join "users-companies-access" uca 
	on uca."userId" = u."mongoId" 
left join companies c2
	on c2.id = uca."companyId"
left join countries c3 
	on c3.id = p."countryId" 
--	and c."createdAt" > '2025-09-30' 
--	and c."createdAt" < '2025-12-31'
group by c2."name"


-- CES por Pais, anio, Q(X), Valor y Total de respuesta
SELECT 
    c3."iso",
    EXTRACT(YEAR FROM c."createdAt") AS anio,
    CASE 
        WHEN EXTRACT(QUARTER FROM c."createdAt") = 1 THEN 'Q1 (Ene-Mar)'
        WHEN EXTRACT(QUARTER FROM c."createdAt") = 2 THEN 'Q2 (Abr-Jun)'
        WHEN EXTRACT(QUARTER FROM c."createdAt") = 3 THEN 'Q3 (Jul-Sep)'
        WHEN EXTRACT(QUARTER FROM c."createdAt") = 4 THEN 'Q4 (Oct-Dic)'
    END AS trimestre,
    AVG(c.value) AS ces_promedio,   -- Reemplaza sum/count por AVG que es más estándar
    COUNT(*) AS total_respuestas
FROM ces c
LEFT JOIN memberships m 
    ON m.id = c."membershipId"
LEFT JOIN "plans" p 
    ON p.id = m."planId"
LEFT JOIN users u
    ON u."mongoId" = m."userId" 
LEFT JOIN "users-companies-access" uca 
    ON uca."userId" = u."mongoId" 
LEFT JOIN companies c2
    ON c2.id = uca."companyId"
LEFT JOIN countries c3 
    ON c3.id = p."countryId" 
-- WHERE c."createdAt" >= '2024-01-01' -- Descomenta si quieres filtrar un año específico
GROUP BY 
    c3."iso", 
    EXTRACT(YEAR FROM c."createdAt"), 
    EXTRACT(QUARTER FROM c."createdAt")
ORDER BY 
    c3."iso", 
    anio DESC, 
    EXTRACT(QUARTER FROM c."createdAt") DESC;