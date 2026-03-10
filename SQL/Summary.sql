SET "vars.fechaInicio" = '2026-03-08T03:00:00.000Z';
SET "vars.fechaFin" = '2026-03-09T03:00:00.000Z';

SELECT 
    c.id as "companyId",
    c."name" as "companyName",
    c."type" as "companyType",
    (
      SELECT COALESCE(json_object_agg(sub.name, sub."userCount"), '{}'::json)
      FROM (
        SELECT p."name", COUNT(DISTINCT m.id) as "userCount"
        FROM public."companies-plans" cp
        LEFT JOIN public.plans p ON p.id = cp."planId"
        LEFT JOIN public."users-companies-access" uca 
          ON cp."companyId" = uca."companyId" 
         AND uca.visible = true
         AND uca."createdAt" <= :dateTo
         AND (uca."extraInfo" IS NULL OR uca."extraInfo" NOT ILIKE '%test%')
        LEFT JOIN public.memberships m
          ON m."userId" = uca."userId" 
         AND m."planId" = cp."planId"
         AND m.status = 2
        WHERE cp."companyId" = c.id
        GROUP BY p."name"
      ) as sub
    ) as "plansBreakdown",
    COALESCE(stats.history, 0) as "totalUsersAllTime",
    COALESCE(stats.active, 0) as "activeUsers",
    c."membershipsPurchased",
    COALESCE(used.quantity, 0) as "activeMemberships",
    COALESCE(used.historical_quantity, 0) as "totalMembershipsHistory",
    COALESCE(stats.premium_total, 0) as "totalPremiumUsers",
    COALESCE(stats.elite_total, 0) as "totalEliteUsers",
    COALESCE(stats.new_users, 0) as "newUsersTotal",
    COALESCE(stats.new_premium, 0) as "newPremiumUsers",
    COALESCE(stats.new_elite, 0) as "newEliteUsers",
    CASE 
      WHEN c."type" = 'assistance' THEN
        CASE 
          WHEN c."membershipsPurchased" > 0 THEN c."membershipsPurchased"
          ELSE COALESCE(stats.active, 0)
        END
      ELSE
        GREATEST(COALESCE(used.quantity, 0), c."membershipsPurchased")
    END as "protectedPetsCount"
FROM public."companies" as c
LEFT JOIN (
    SELECT 
      "companyId",
      COUNT(*) as history,
      COUNT(*) FILTER (WHERE visible = true AND "createdAt" <= :dateTo) as active,
      COUNT(*) FILTER (WHERE "createdAt" >= :dateFrom AND "createdAt" <= :dateTo) as new_users,
      COUNT(*) FILTER (WHERE "extraInfo" ILIKE '%premium%') as premium_total,
      COUNT(*) FILTER (WHERE "extraInfo" ILIKE '%elite%') as elite_total,
      COUNT(*) FILTER (WHERE "createdAt" >= :dateFrom 
              AND "createdAt" <= :dateTo 
              AND "extraInfo" ILIKE '%premium%') as new_premium,
      COUNT(*) FILTER (WHERE "createdAt" >= :dateFrom 
              AND "createdAt" <= :dateTo 
              AND "extraInfo" ILIKE '%elite%') as new_elite
    FROM public."users-companies-access"
    WHERE ("extraInfo" IS NULL OR "extraInfo" NOT ILIKE '%test%')
    GROUP BY "companyId"
) as stats ON c."id" = stats."companyId"
LEFT JOIN (
    SELECT 
      uca."companyId",
      COUNT(DISTINCT ms.id) FILTER (WHERE ms.status = 2) as quantity,
      COUNT(DISTINCT ms.id) as historical_quantity
    FROM public."users-companies-access" as uca
    INNER JOIN public."companies-plans" cp 
      ON cp."companyId" = uca."companyId"
    INNER JOIN "memberships" as ms 
      ON ms."userId" = uca."userId"
      AND ms."planId" = cp."planId"
    WHERE (uca."extraInfo" IS NULL OR uca."extraInfo" NOT ILIKE '%test%')
    GROUP BY uca."companyId"
) as used ON c."id" = used."companyId"
ORDER BY c.name ASC