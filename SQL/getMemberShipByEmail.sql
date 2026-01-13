SELECT 
	m.id AS "membershipId",
	u.name AS name,
	u.surname AS surname,
	u.rut AS rut,
	u.email AS email
FROM memberships AS m
INNER JOIN users AS u ON m."userId"=u."mongoId"
WHERE u.email='vero.gonzalez.o@gmail.com';