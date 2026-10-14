select 
	mp.id as id_MP, 
	mp."externalPaymentId",
	mp."externalSubscriptionId",
	mp.amount, 
	mp."paidAt",
	u.email, 
	p.name as petName,
	u."mongoId", 
	u."flowId",
	u.name, 
	u.surname, 
	u.rut,
	mp."membershipId", 
	m.status, 
	mp."paymentGateway",  
	mp."createdAt",
	m."planId",
	m."createdAt" as "membershipCreatedAt"
from "membership-payments" mp
inner join memberships m on m.id = mp."membershipId" 
inner join users u on u."mongoId" = m."userId" 
inner join pets p on p.id = m."petId" 
where mp."membershipId" = 'ab80d0a0-bbeb-11f0-9704-19175553abcb'
--where mp."externalPaymentId" = '171166500494'
--where mp."idReferencePayment" = '42a1e4f447194d358d9492992bb9d4b9'
--where u.email = 'camilamorasoto@gmail.com'
--and mp."paymentGateway" = 'MercadoPago'
--where m."flowId" = 'sus_u0juzb963v'
order by mp."membershipId" asc, mp."paidAt" desc

select * from "membership-payments" mp 
where mp."membershipId" = '690b5dc0-e0f4-11f0-8f1e-4db453a269cf'
--where mp."idReferencePayment" like '3814a5b2ccdc4e11b6e70ac980124ed5'
--and mp."paymentGateway" = 'MercadoPago'
order by "paidAt" desc
--order by "createdAt" desc

select m.* from memberships m 
left join users u on u."id" = m."userId"
where u.email like 'rebkhdezp@gmail.com'
--where u.rut like '%189156790%'
--where u.email like 'ces%@ri%'
--where name like 'M%' and u.surname like 'R%' and m."planId" ='aa4a3320-c502-11ee-8499-71c77429f54f'
--where m.id='128a8420-470d-11f0-ab94-1b340d2e2acc'
