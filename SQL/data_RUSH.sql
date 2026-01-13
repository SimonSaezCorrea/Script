-- 1. Definimos la variable (le ponemos un prefijo 'vars.' para evitar conflictos)
SET vars.idc = '890b23e0-0b60-11f0-a038-e10c84727edb';

-- HISTORICAL --
SELECT * FROM public."users-companies-access" as uca
WHERE uca."companyId" = current_setting('vars.idc')::uuid
ORDER BY uca."userId" ASC;

-- Total de la compañia --
SELECT * FROM public."users-companies-access" as uca
--WHERE uca."companyId" = current_setting('vars.idc')::uuid
	where visible=true
ORDER BY uca."userId" ASC;

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
WHERE uca."companyId" = current_setting('vars.idc')::uuid
	AND ms.status=2
ORDER BY uca."userId" ASC;