-- TOTAL DE MASCOTAS PROTEGIDAS -- 

with summary as (
	SELECT 
	    c."id", 
	    c."name", 
	    c."membershipsPurchased",
		c.type,
	    COALESCE(usadas.cantidad, 0) as "cantidad_usadas",
	    COALESCE(activos.cantidad, 0) as "cantidad_activos",
	    CASE 
	        -- CASO 1: Si es tipo 'assistance'
	        WHEN c."type" = 'assistance' THEN
	            CASE 
	                WHEN c."membershipsPurchased" > 0 THEN c."membershipsPurchased"
	                ELSE COALESCE(activos.cantidad, 0)
	            END
	        -- CASO 2: Cualquier otro tipo (Lógica original: el mayor entre compradas y usadas)
	        ELSE
	            CASE 
	                WHEN COALESCE(usadas.cantidad, 0) > c."membershipsPurchased" THEN usadas.cantidad
	                ELSE c."membershipsPurchased"
	            END
	    END as "resultado_comparacion"
	FROM public."companies" as c
	-- Subconsulta 1: Cantidad Usadas (Membresías status 2)
	LEFT JOIN (
	    SELECT 
	        uca."companyId", 
	        COUNT(*) as cantidad
	    FROM public."users-companies-access" as uca
	    INNER JOIN "memberships" as ms
	        ON ms."userId" = uca."userId" 
	    WHERE ms.status = 2
	    GROUP BY uca."companyId"
	) as usadas ON c."id" = usadas."companyId"
	-- Subconsulta 2: Cantidad Activos (Visible = true y fecha tope)
	LEFT JOIN (
	    SELECT 
	        uca."companyId", 
	        COUNT(*) as cantidad
	    FROM public."users-companies-access" as uca
	    WHERE uca.visible = true
	      AND uca."createdAt" <= '2025-12-03T03:00:00.000Z' -- Fecha manual
	    GROUP BY uca."companyId"
	) as activos ON c."id" = activos."companyId"
	ORDER BY "resultado_comparacion" DESC
)
SELECT 
    SUM("membershipsPurchased") AS "Total Compradas", 
    SUM("cantidad_usadas") AS "Total Usadas", 
    SUM("cantidad_activos") AS "Total Activos", 
    SUM("resultado_comparacion") AS "Total Mascotas Protegidas"
FROM 
    summary;