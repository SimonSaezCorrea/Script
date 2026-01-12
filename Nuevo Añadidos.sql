SELECT 
    uca."companyId", 
    c."name" as "companyName",
    COUNT(*) as cantidad
FROM public."users-companies-access" as uca
INNER JOIN "companies" as c
    ON c."id" = uca."companyId"
WHERE uca."createdAt" >= '2025-12-02T03:00:00.000Z'
	and uca."createdAt" <= '2025-12-03T03:00:00.000Z'
GROUP BY uca."companyId", c."name"
ORDER BY cantidad DESC;
