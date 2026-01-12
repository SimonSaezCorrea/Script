Select u.id, u.email, u.name, u.surname, b.id, b.name, usr.id, usr."accountNumber", usr."accountType" from users as u
inner join "users-banks-relationship" as usr on usr."userId"= u."id"
inner join banks as b on b.id=usr."bankId"
where u.email='aracelifbaeza@gmail.com';

Select usr.id, usr."accountNumber", usr."accountType" from users as u
inner join "users-banks-relationship" as usr on usr."userId"= u."id"
where u.email='aracelifbaeza@gmail.com';