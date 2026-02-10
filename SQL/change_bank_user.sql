Select u.id, u.email, u.name, u.surname, b.id, b.name, usr.id, usr."accountNumber", usr."accountType" from users as u
inner join "users-banks-relationship" as usr on usr."userId"= u."id"
inner join banks as b on b.id=usr."bankId"
where u.email='cosmeal_products@hotmail.com';

Select * from users as u
--inner join "users-banks-relationship" as ubr on ubr."userId"= u."id"
where u.email='cosmeal_products@hotmail.com';

-- user: ce4c5427-2f8d-47d7-a997-9732f7afc048
-- bank: 194e424a-3d7c-4619-a517-423f29115265
select * from "users-banks-relationship" ubr --where ubr."userId" = 'ce4c5427-2f8d-47d7-a997-9732f7afc048'

select * from banks b order by name asc