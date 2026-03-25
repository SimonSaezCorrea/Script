SELECT id, name, "monthlyPrice", "createdAt", visible, "internalDescription"
FROM plans
WHERE name = 'Plan Esencial'
and visible=true;