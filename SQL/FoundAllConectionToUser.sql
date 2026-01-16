select * from users where
--email = 'simon@somospawer.com'
rut = '210843841'

WITH variables AS (
    SELECT 
        '88d253a4-12cd-473f-a555-418a28d3b4a9'::uuid AS v_user_uuid, 
        '66298b41c316d6003d30b478'::varchar AS v_mongo_id
),
summary AS (
    -- 1. TABLAS VINCULADAS POR UUID (Claves foráneas explícitas en tu SQL)
    SELECT 'customs-payments' AS tabla, 'UUID' AS tipo_vinculo, count(*) AS registros FROM "customs-payments", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'refunds-requests', 'UUID', count(*) FROM "refunds-requests", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'services-records', 'UUID', count(*) FROM "services-records", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'sponsors-memberships', 'UUID', count(*) FROM "sponsors-memberships", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'sponsors-payments', 'UUID', count(*) FROM "sponsors-payments", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'users-banks-relationship', 'UUID', count(*) FROM "users-banks-relationship", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'users-credits', 'UUID', count(*) FROM "users-credits", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'users-details', 'UUID', count(*) FROM "users-details", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'users-donations', 'UUID', count(*) FROM "users-donations", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'users-special-grants', 'UUID', count(*) FROM "users-special-grants", variables WHERE "userId" = v_user_uuid
    UNION ALL
    SELECT 'waiting-list', 'UUID', count(*) FROM "waiting-list", variables WHERE "userId" = v_user_uuid
    -- 2. TABLAS VINCULADAS POR MONGO ID (Strings/Varchar según tu esquema)
    UNION ALL
    SELECT 'pets', 'MongoID (owner)', count(*) FROM pets, variables WHERE owner = v_mongo_id
    UNION ALL
    SELECT 'memberships', 'MongoID', count(*) FROM memberships, variables WHERE "userId" = v_mongo_id
    UNION ALL
    SELECT 'payments', 'MongoID', count(*) FROM payments, variables WHERE "userId" = v_mongo_id
    UNION ALL
    SELECT 'paw-activities', 'MongoID', count(*) FROM "paw-activities", variables WHERE "userId" = v_mongo_id
    UNION ALL
    SELECT 'customer-cards', 'MongoID', count(*) FROM "customer-cards", variables WHERE "userId" = v_mongo_id
    UNION ALL
    SELECT 'donations', 'MongoID', count(*) FROM donations, variables WHERE "userId" = v_mongo_id
    UNION ALL
    SELECT 'redemptions', 'MongoID', count(*) FROM redemptions, variables WHERE "userId" = v_mongo_id
    UNION ALL
    SELECT 'users-companies-access', 'MongoID', count(*) FROM "users-companies-access", variables WHERE "userId" = v_mongo_id
)
-- Mostrar solo tablas donde se encontró información
SELECT * FROM summary 
WHERE registros > 0 
ORDER BY tipo_vinculo, tabla;
