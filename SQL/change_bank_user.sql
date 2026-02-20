Select u.id, u.email, u.name, u.surname, b.id, b.name, usr.id, usr."accountNumber", usr."accountType" from users as u
inner join "users-banks-relationship" as usr on usr."userId"= u."id"
inner join banks as b on b.id=usr."bankId"
where u.email='alfredo.saez@sonda.com';

Select * from users as u
inner join "users-banks-relationship" as ubr on ubr."userId"= u."id"
where u.email='alfredo.saez@sonda.com';
--where u.rut = '164274535'

-- user: 598a068c-778b-494e-969a-379d75c5e63e
-- bank: f95a8ed9-0c3d-4eda-8d31-5a233615afcf
select * from "users-banks-relationship" ubr where ubr."userId" = '598a068c-778b-494e-969a-379d75c5e63e'

select * from banks b order by name asc