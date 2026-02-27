select * from users where
--email = 'simon@somospawer.com'
rut = '210843841'

DO $$ 
DECLARE 
    -- ===============================================================
    -- CONFIGURACIÓN: INGRESA LOS IDS DEL USUARIO AQUÍ
    -- ===============================================================
    v_user_uuid uuid := '9be93b97-a77e-4590-ac0c-3c38c73d3637';        -- Ej: 'a0eebc99-9c0b-...'
    v_mongo_id varchar := '699f1475ff5f740034db1259';  -- Ej: '64b1f...'
    -- ===============================================================
BEGIN

    RAISE NOTICE 'Iniciando eliminación corregida para Usuario UUID: % y MongoID: %', v_user_uuid, v_mongo_id;

    -- 1. ELIMINAR DEPENDENCIAS DE "REFUNDS-REQUESTS" (Solicitudes de reembolso)
    -- Esto usa el UUID, suele ser independiente de las membresías de mongo
    DELETE FROM "refunds-requests-attachments" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "refunds-requests-changelog" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "dongraf-results" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "ces" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "services-records" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    
    DELETE FROM "refunds-requests" WHERE "userId" = v_user_uuid;


    -- ==================================================================================
    -- 2. LIMPIEZA PREVIA DE TABLAS QUE APUNTAN A MEMBERSHIPS (EL FIX)
    -- Estas tablas tienen FK hacia memberships, por lo que deben borrarse ANTES de borrar la membresía.
    -- Buscamos tanto por userId directo como por las membresías que pertenecen al usuario.
    -- ==================================================================================

    -- A. REDEMPTIONS (Aquí dio el error antes)
    DELETE FROM "redemptions" 
    WHERE "userId" = v_mongo_id 
       OR "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- B. PAW ACTIVITIES (También suelen estar ligadas a membresías)
    DELETE FROM "paw-activities" 
    WHERE "userId" = v_mongo_id 
       OR "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- C. PAYMENTS (Pagos ligados a membresías o al usuario)
    DELETE FROM "payments" 
    WHERE "userId" = v_mongo_id 
       OR "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- D. CES (Cargas vinculadas a membresías)
    DELETE FROM "ces" 
    WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- E. SERVICES REDEMPTIONS
    DELETE FROM "services-redemptions" 
    WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- F. MEMBERSHIP PAYMENTS & SUBSCRIPTIONS
    DELETE FROM "membership-payments" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);
    DELETE FROM "membership_subscriptions" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);


    -- ==================================================================================
    -- 3. AHORA SÍ: ELIMINAR MEMBERSHIPS
    -- ==================================================================================
    DELETE FROM "memberships" WHERE "userId" = v_mongo_id;


    -- 4. ELIMINAR DEPENDENCIAS DE "PETS" (Mascotas)
    -- Las membresías apuntan a pets, por eso borramos memberships antes (paso 3).
    
    -- Borrar archivos de records
    DELETE FROM "records-files" WHERE "recordId" IN (
        SELECT id FROM records WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
    );
    -- Borrar records
    DELETE FROM "records" WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id);
    
    -- Borrar recordatorios
    DELETE FROM "reminder-dates" WHERE "reminderId" IN (
        SELECT id FROM reminders WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
    );
    DELETE FROM "reminders" WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id);

    -- Eliminamos las mascotas
    DELETE FROM "pets" WHERE owner = v_mongo_id;


    -- 5. ELIMINAR DEPENDENCIAS DE "SPONSORS"
    DELETE FROM "sponsor-membership-payments" WHERE "sponsorMembershipId" IN (SELECT id FROM "sponsors-memberships" WHERE "userId" = v_user_uuid);
    DELETE FROM "sponsors-payments" WHERE "userId" = v_user_uuid;
    DELETE FROM "sponsors-memberships" WHERE "userId" = v_user_uuid;


    -- 6. ELIMINAR RESTO DE TABLAS HUÉRFANAS (MongoID y UUID)
    DELETE FROM "customer-cards" WHERE "userId" = v_mongo_id;
    DELETE FROM "users-companies-access" WHERE "userId" = v_mongo_id;
    DELETE FROM "donations" WHERE "userId" = v_mongo_id;
    
    DELETE FROM "customs-payments" WHERE "userId" = v_user_uuid;
    DELETE FROM "services-records" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-credits" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-details" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-donations" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-special-grants" WHERE "userId" = v_user_uuid;
    DELETE FROM "waiting-list" WHERE "userId" = v_user_uuid;
    DELETE FROM "users-verification-codes" WHERE email IN (SELECT email FROM users WHERE id = v_user_uuid);
    
    -- Borrar relación bancaria al final
    DELETE FROM "users-banks-relationship" WHERE "userId" = v_user_uuid;


    -- 7. ELIMINAR AL USUARIO FINAL
    DELETE FROM "users" WHERE id = v_user_uuid;
    
    RAISE NOTICE 'Éxito: Usuario y todas las dependencias (incluyendo redemptions) eliminados.';

END $$;