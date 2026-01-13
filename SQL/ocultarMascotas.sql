SELECT p.* FROM memberships as ms
inner join users as u on ms."userId"=u."mongoId"
inner join pets as p on ms."petId"=p."id"
where u.email = 'alvaro.reyesm@usm.cl'