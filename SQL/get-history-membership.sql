select 
	u."name", 
	u.surname, 
	u.rut, 
	u.email, 
	pt."name", 
	p."name", 
	msh."deactivationReason",
	msh."createdAt" 
from "memberships-status-history" msh 
inner join memberships m on m.id = msh."membershipId" 
inner join pets pt on pt.id = m."petId" 
inner join plans p on p.id = m."planId" 
inner join users u on u."mongoId" = m."userId" 
where msh."createdAt" >= '2026-05-01' and msh."createdAt" < '2026-06-01'
and msh."newStatus" = 4
order by msh."createdAt" desc