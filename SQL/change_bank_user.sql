Select u.id, u.email, u.name, u.surname, b.id, b.name, usr.id, usr."accountNumber", usr."accountType" from users as u
inner join "users-banks-relationship" as usr on usr."userId"= u."id"
inner join banks as b on b.id=usr."bankId"
where u.email='consuelo.claveria@gmail.com';

Select * from users as u
inner join "users-banks-relationship" as ubr on ubr."userId"= u."id"
where u.email='consuelo.claveria@gmail.com';

select * from banks b order by name asc
