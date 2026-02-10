SET "vars.fechaInicio" = '2025-12-03T03:00:00.000Z';
SET "vars.fechaFin" = '2025-12-04T03:00:00.000Z';

SELECT 
	c.id as "companyId", 
	c."name" as "companyName",
	c."type" as "companyType",
	-- Métricas de Usuarios
	COALESCE(stats.history, 0) as "totalUsersAllTime", -- La cantidad de usuarios de toda la vida
	COALESCE(stats.active, 0) as "activeUsers",       -- La cantidad de usuarios activos
	-- Métricas de Membresías
	c."membershipsPurchased",
	COALESCE(used.quantity, 0) as "activeMemberships", -- La cantidad de usuarios con membresias (status 2 y visibles)
	COALESCE(used.historical_quantity, 0) as "totalMembershipsHistory", -- HISTÓRICO: Sin condiciones de status ni visible
	-- Desglose por Plan (Totales)
	COALESCE(stats.premium_total, 0) as "totalPremiumUsers", 
	COALESCE(stats.elite_total, 0) as "totalEliteUsers",
	-- Desglose de Nuevos Usuarios (En el periodo seleccionado)
	COALESCE(stats.new_users, 0) as "newUsersTotal",
	COALESCE(stats.new_premium, 0) as "newPremiumUsers",
	COALESCE(stats.new_elite, 0) as "newEliteUsers",
	-- Métrica de Negocio (Resultado Final)
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
-- 1. CONSULTA DE LOS DATOS DE LOS users-companies-access NECESARIOS
LEFT JOIN (
	SELECT 
		"companyId",
		COUNT(*) as history,
		-- Activos: Visible = true y creados hasta la fecha fin
		COUNT(*) FILTER (WHERE visible = true AND "createdAt" <= current_setting('vars.fechaFin')::timestamptz) as active,
		-- Nuevos: Creados entre fecha inicio y fecha fin
		COUNT(*) FILTER (WHERE "createdAt" >= current_setting('vars.fechaInicio')::timestamptz AND "createdAt" <= current_setting('vars.fechaFin')::timestamptz) as new_users,
		
		-- Totales por Plan
		COUNT(*) FILTER (WHERE "extraInfo" ILIKE '%premium%') as premium_total,
		COUNT(*) FILTER (WHERE "extraInfo" ILIKE '%elite%') as elite_total,
		
		-- Nuevos por Plan (Fecha rango + Texto plan)
		COUNT(*) FILTER (WHERE "createdAt" >= current_setting('vars.fechaInicio')::timestamptz 
						AND "createdAt" <= current_setting('vars.fechaFin')::timestamptz 
						AND "extraInfo" ILIKE '%premium%') as new_premium,
		COUNT(*) FILTER (WHERE "createdAt" >= current_setting('vars.fechaInicio')::timestamptz 
						AND "createdAt" <= current_setting('vars.fechaFin')::timestamptz 
						AND "extraInfo" ILIKE '%elite%') as new_elite
	FROM public."users-companies-access"
	WHERE ("extraInfo" IS NULL OR "extraInfo" NOT ILIKE '%test%') -- Filtro Global Anti-Test
	GROUP BY "companyId"
) as stats ON c."id" = stats."companyId"
-- 2. CONSULTA MEMBRESÍAS USADAS POR LOS USUARIOS
LEFT JOIN (
	SELECT 
		uca."companyId", 
		-- Cantidad con filtros (status 2)
		COUNT(*) FILTER (WHERE ms.status = 2) as quantity,
		-- Cantidad histórica (Sin filtros de status/visible, solo anti-test)
		COUNT(*) as historical_quantity
	FROM public."users-companies-access" as uca
	INNER JOIN "memberships" as ms ON ms."userId" = uca."userId" 
	WHERE (uca."extraInfo" IS NULL OR uca."extraInfo" NOT ILIKE '%test%')
	GROUP BY uca."companyId"
) as used ON c."id" = used."companyId"
order by c.name Asc