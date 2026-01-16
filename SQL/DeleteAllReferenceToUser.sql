select * from users where
--email = 'simon@somospawer.com'
rut = '210843841'

DO $$ 
DECLARE 
    -- ===============================================================
    -- CONFIGURACIÓN: INGRESA LOS IDS DEL USUARIO AQUÍ
    -- ===============================================================
    v_user_uuid uuid := '88d253a4-12cd-473f-a555-418a28d3b4a9';        -- Ej: 'a0eebc99-9c0b-...'
    v_mongo_id varchar := '66298b41c316d6003d30b478';  -- Ej: '64b1f...'
    -- ===============================================================
BEGIN
    RAISE NOTICE 'Iniciando eliminación masiva para Usuario UUID: % y MongoID: %', v_user_uuid, v_mongo_id;
    -- 1. ELIMINAR DEPENDENCIAS DE "REFUNDS-REQUESTS" (Solicitudes de reembolso)
    -- Estas tablas dependen de refunds-requests, que a su vez depende del usuario
    DELETE FROM "refunds-requests-attachments" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "refunds-requests-changelog" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "dongraf-results" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    -- CES y Services-Records también pueden estar ligados a un refund request
    DELETE FROM "ces" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "services-records" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    -- Finalmente eliminamos los refunds del usuario
    DELETE FROM "refunds-requests" WHERE "userId" = v_user_uuid;
    -- 2. ELIMINAR DEPENDENCIAS DE "MEMBERSHIPS" (Membresías)
    -- Las membresías usan MongoID en tu esquema. Debemos borrar sus pagos y suscripciones primero.
    DELETE FROM "membership-payments" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);
    DELETE FROM "membership_subscriptions" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);
    DELETE FROM "services-redemptions" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);
    DELETE FROM "ces" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);
    -- También hay pagos generales y records ligados a la membresía
    DELETE FROM "payments" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);
    -- Eliminamos las membresías del usuario
    DELETE FROM "memberships" WHERE "userId" = v_mongo_id;
    -- 3. ELIMINAR DEPENDENCIAS DE "PETS" (Mascotas)
    -- Las mascotas usan MongoID (campo owner). Debemos borrar records, recordatorios, etc.
    -- Borrar archivos de records de las mascotas de este dueño
    DELETE FROM "records-files" WHERE "recordId" IN (
        SELECT id FROM records WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
    );
    -- Borrar records de las mascotas
    DELETE FROM "records" WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id);
    -- Borrar fechas de recordatorios y recordatorios
    DELETE FROM "reminder-dates" WHERE "reminderId" IN (
        SELECT id FROM reminders WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
    );
    DELETE FROM "reminders" WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id);
    -- Eliminamos las mascotas del usuario
    DELETE FROM "pets" WHERE owner = v_mongo_id;
    -- 4. ELIMINAR DEPENDENCIAS DE "SPONSORS" (Padrinos)
    -- Borrar pagos de sponsors
    DELETE FROM "sponsor-membership-payments" WHERE "sponsorMembershipId" IN (SELECT id FROM "sponsors-memberships" WHERE "userId" = v_user_uuid);
    DELETE FROM "sponsors-payments" WHERE "userId" = v_user_uuid;
    -- Borrar membresías de sponsors
    DELETE FROM "sponsors-memberships" WHERE "userId" = v_user_uuid;
    -- 5. ELIMINAR OTRAS TABLAS VINCULADAS POR MONGO ID
    DELETE FROM "customer-cards" WHERE "userId" = v_mongo_id;
    DELETE FROM "users-companies-access" WHERE "userId" = v_mongo_id;
    DELETE FROM "donations" WHERE "userId" = v_mongo_id;
    DELETE FROM "redemptions" WHERE "userId" = v_mongo_id;
    -- Paw activities puede tener dependencias, borrar con cuidado
    DELETE FROM "paw-activities" WHERE "userId" = v_mongo_id;
    DELETE FROM "payments" WHERE "userId" = v_mongo_id; -- Pagos sueltos que no se borraron con membresías
    -- 6. ELIMINAR OTRAS TABLAS VINCULADAS POR UUID
    DELETE FROM "customs-payments" WHERE "userId" = v_user_uuid;
    DELETE FROM "services-records" WHERE "userId" = v_user_uuid; -- Registros de servicios directos al usuario
    DELETE FROM "users-credits" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-details" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-donations" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-special-grants" WHERE "userId" = v_user_uuid;
    DELETE FROM "waiting-list" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-verification-codes" WHERE email IN (SELECT email FROM users WHERE id = v_user_uuid); -- Limpieza extra por email
    -- Borrar relación bancaria al final (por si refunds dependía de ella, aunque ya borramos refunds)
    DELETE FROM "users-banks-relationship" WHERE "userId" = v_user_uuid;
    -- 7. FINALMENTE, ELIMINAR AL USUARIO
    DELETE FROM "users" WHERE id = v_user_uuid;
    RAISE NOTICE 'Usuario y todos sus datos relacionados han sido eliminados correctamente.';
END $$;