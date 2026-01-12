SELECT 
    uca."companyId", 
    c."name" as "companyName",
    COUNT(*) as cantidad
FROM public."users-companies-access" as uca
INNER JOIN "memberships" as ms
    ON ms."userId" = uca."userId" 
INNER JOIN "companies" as c
    ON c."id" = uca."companyId"
WHERE ms.status = 2
GROUP BY uca."companyId", c."name"
ORDER BY cantidad DESC;