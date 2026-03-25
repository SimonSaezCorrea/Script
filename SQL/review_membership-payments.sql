select 
	mp.id as id_MP, 
	mp."mpPaymentId",
	mp."idReferencePayment",
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
where mp."membershipId" = 'ce74cd00-098b-11ef-a535-9d13e0ca13f7'
--where mp."mpPaymentId" = '146235686563'
--where mp."idReferencePayment" = '2c9380848ef3876b018ef7981ac802b6'
--where u.email = 'michellesegal6@gmail.com'
--and mp."paymentGateway" = 'MercadoPago'
--where m."flowId" = 'sus_u0juzb963v'
order by mp."membershipId" asc, mp."paidAt" desc

select * from "membership-payments" mp 
where mp."membershipId" = 'ce74cd00-098b-11ef-a535-9d13e0ca13f7'
--where mp."idReferencePayment" like '379924ff7a45446d9e78c3d99ecd4910'
--and mp."paymentGateway" = 'MercadoPago'
order by "paidAt" desc
--order by "createdAt" desc

select m.* from memberships m 
left join users u on u."mongoId" = m."userId"
where u.email like 'a.rodriguezq82@gmail.com'
--where u.rut like '%189156790%'
--where u.email like 'ces%@ri%'
--where name like 'M%' and u.surname like 'R%' and m."planId" ='aa4a3320-c502-11ee-8499-71c77429f54f'
--where m.id='128a8420-470d-11f0-ab94-1b340d2e2acc'