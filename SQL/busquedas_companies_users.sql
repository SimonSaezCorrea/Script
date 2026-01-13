-- 1. Definimos la variable (le ponemos un prefijo 'vars.' para evitar conflictos)
SET vars.idc = '05f5b6d0-81ce-11ef-be1c-4f5fdfb2b8da';

-- HISTORICAL --
SELECT * FROM public."users-companies-access" as uca
WHERE uca."companyId" = current_setting('vars.idc')::uuid
ORDER BY uca."userId" ASC;

-- Total de la compañia --
SELECT *
FROM public."users-companies-access" as uca
where uca.visible=true
	and uca."createdAt"<='2025-12-03T03:00:00.000Z'

-- Memberships --
SELECT * FROM public."users-companies-access" as uca
INNER JOIN "memberships" as ms
    ON ms."userId" = uca."userId" 
WHERE uca."companyId" = current_setting('vars.idc')::uuid
ORDER BY uca."userId" ASC;

-- total membresias --
SELECT * FROM public."users-companies-access" as uca
INNER JOIN "memberships" as ms
    ON ms."userId" = uca."userId" 
inner join "companies" as c
	on c.id = current_setting('vars.idc')::uuid
WHERE uca."companyId" = current_setting('vars.idc')::uuid
	and ms.status=2
	and uca."createdAt"<c."startDate"
ORDER BY ms."createdAt" DESC;


