-- Buscar usuario primero
-- select * from users where rut = '210843841'
-- select * from users where email = 'simon@somospawer.com'

-- =====================================================
-- PREVIEW: Ver todo lo que se va a eliminar
-- =====================================================

do $$
DECLARE
    v_user_uuid uuid    := '7b601e06-2275-4cd9-bb79-46be45b085b8';
    v_mongo_id  varchar := '69c3d3fab2a646003446cb8e';
BEGIN
    RAISE NOTICE '=== PREVIEW USUARIO: % ===', v_user_uuid;
    RAISE NOTICE 'Memberships:              %', (SELECT COUNT(*) FROM memberships WHERE "userId" = v_mongo_id);
    RAISE NOTICE 'Pets:                     %', (SELECT COUNT(*) FROM pets WHERE owner = v_mongo_id);
    RAISE NOTICE 'Refunds-requests:         %', (SELECT COUNT(*) FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Refund-attachments:       %', (SELECT COUNT(*) FROM "refunds-requests-attachments" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid));
    RAISE NOTICE 'Refund-changelog:         %', (SELECT COUNT(*) FROM "refunds-requests-changelog" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid));
    RAISE NOTICE 'Refund-details:           %', (SELECT COUNT(*) FROM refund_details WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid));
    RAISE NOTICE 'Dongraf-results:          %', (SELECT COUNT(*) FROM "dongraf-results" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid));
    RAISE NOTICE 'Payments:                 %', (SELECT COUNT(*) FROM payments WHERE "userId" = v_mongo_id);
    RAISE NOTICE 'Membership-payments:      %', (SELECT COUNT(*) FROM "membership-payments" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id));
    RAISE NOTICE 'Membership-subscriptions: %', (SELECT COUNT(*) FROM membership_subscriptions WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id));
    RAISE NOTICE 'Memberships-status-hist:  %', (SELECT COUNT(*) FROM "memberships-status-history" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id));
    RAISE NOTICE 'Paw-activities:           %', (SELECT COUNT(*) FROM "paw-activities" WHERE "userId" = v_mongo_id);
    RAISE NOTICE 'PawActivities (legacy):   %', (SELECT COUNT(*) FROM "pawActivities" WHERE "userId" = v_mongo_id);
    RAISE NOTICE 'Redemptions:              %', (SELECT COUNT(*) FROM redemptions WHERE "userId" = v_mongo_id);
    RAISE NOTICE 'Services-records:         %', (SELECT COUNT(*) FROM "services-records" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Services-redemptions:     %', (SELECT COUNT(*) FROM "services-redemptions" WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id));
    RAISE NOTICE 'CES:                      %', (SELECT COUNT(*) FROM ces WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id));
    RAISE NOTICE 'Plan-change-records:      %', (SELECT COUNT(*) FROM "plan-change-records" WHERE "petId" IN (SELECT "petId" FROM memberships WHERE "userId" = v_mongo_id));
    RAISE NOTICE 'Records:                  %', (SELECT COUNT(*) FROM records WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id));
    RAISE NOTICE 'Records-files:            %', (SELECT COUNT(*) FROM "records-files" WHERE "recordId" IN (SELECT id FROM records WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)));
    RAISE NOTICE 'Reminders:                %', (SELECT COUNT(*) FROM reminders WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id));
    RAISE NOTICE 'Reminder-dates:           %', (SELECT COUNT(*) FROM "reminder-dates" WHERE "reminderId" IN (SELECT id FROM reminders WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)));
    RAISE NOTICE 'Sponsors-memberships:     %', (SELECT COUNT(*) FROM "sponsors-memberships" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Sponsors-payments:        %', (SELECT COUNT(*) FROM "sponsors-payments" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Sponsor-memb-payments:    %', (SELECT COUNT(*) FROM "sponsor-membership-payments" WHERE "sponsorMembershipId" IN (SELECT id FROM "sponsors-memberships" WHERE "userId" = v_user_uuid));
    RAISE NOTICE 'Customer-cards:           %', (SELECT COUNT(*) FROM "customer-cards" WHERE "userId" = v_mongo_id);
    RAISE NOTICE 'Users-companies-access:   %', (SELECT COUNT(*) FROM "users-companies-access" WHERE "userId" = v_mongo_id);
    RAISE NOTICE 'Shared-credits:           %', (SELECT COUNT(*) FROM "shared-credits" WHERE "ucaId" IN (SELECT id FROM "users-companies-access" WHERE "userId" = v_mongo_id));
    RAISE NOTICE 'Donations:                %', (SELECT COUNT(*) FROM donations WHERE "userId" = v_mongo_id);
    RAISE NOTICE 'Users-donations:          %', (SELECT COUNT(*) FROM "users-donations" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Customs-payments:         %', (SELECT COUNT(*) FROM "customs-payments" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Users-credits:            %', (SELECT COUNT(*) FROM "users-credits" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Users-details:            %', (SELECT COUNT(*) FROM "users-details" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Users-special-grants:     %', (SELECT COUNT(*) FROM "users-special-grants" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Users-welcome-emails:     %', (SELECT COUNT(*) FROM "users-welcome-emails" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Waiting-list:             %', (SELECT COUNT(*) FROM "waiting-list" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Users-banks-relationship: %', (SELECT COUNT(*) FROM "users-banks-relationship" WHERE "userId" = v_user_uuid);
    RAISE NOTICE 'Users-verification-codes: %', (SELECT COUNT(*) FROM "users-verification-codes" WHERE email IN (SELECT email FROM users WHERE id = v_user_uuid));
    RAISE NOTICE 'Users-recovery-codes:     %', (SELECT COUNT(*) FROM "users-recovery-codes" WHERE dni IN (SELECT rut FROM users WHERE id = v_user_uuid));
    RAISE NOTICE '=== FIN PREVIEW — revisar antes de ejecutar el DELETE ===';
END $$;


-- =====================================================
-- DELETE: Ejecutar solo si el preview es correcto
-- =====================================================

DO $$
DECLARE 
    -- ===============================================================
    -- CONFIGURACIÓN: INGRESA LOS IDS DEL USUARIO AQUÍ
    -- ===============================================================
    v_user_uuid uuid    := '7b601e06-2275-4cd9-bb79-46be45b085b8';
    v_mongo_id  varchar := '69c3d3fab2a646003446cb8e';
    -- ===============================================================
BEGIN
    RAISE NOTICE 'Iniciando eliminación para UUID: % y MongoID: %', v_user_uuid, v_mongo_id;
    -- ================================================================
    -- 1. REFUNDS-REQUESTS y todas sus dependencias
    --    (ces, dongraf-results, refund_details, services-records,
    --     attachments, changelog — todo apunta a refunds-requests)
    -- ================================================================
    DELETE FROM "refunds-requests-attachments"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "refunds-requests-changelog"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);
    DELETE FROM "dongraf-results"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);

    DELETE FROM "ces"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);

    -- services-records puede apuntar a refund Y a membership; borramos la parte de refund aquí
    DELETE FROM "services-records"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);

    -- refund_details tiene FK ON DELETE CASCADE hacia refunds-requests,
    -- pero mejor borrarlo explícitamente para evitar sorpresas
    DELETE FROM "refund_details"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "userId" = v_user_uuid);

    DELETE FROM "refunds-requests" WHERE "userId" = v_user_uuid;


    -- ================================================================
    -- 2. DEPENDENCIAS DE MEMBERSHIPS (deben ir ANTES de borrar memberships)
    -- ================================================================

    -- Redemptions (tiene FK a memberships y a paw-activities)
    DELETE FROM "redemptions"
        WHERE "userId" = v_mongo_id
           OR "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- Paw-activities (puede tener FK desde redemptions, ya borradas arriba)
    DELETE FROM "paw-activities"
        WHERE "userId" = v_mongo_id
           OR "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- Payments
    DELETE FROM "payments"
        WHERE "userId" = v_mongo_id
           OR "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- Membership-payments
    DELETE FROM "membership-payments"
        WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- Membership subscriptions (MercadoPago)
    DELETE FROM "membership_subscriptions"
        WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- CES ligados a membresías (los de refund ya fueron borrados arriba)
    DELETE FROM "ces"
        WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- Services-records ligados a membresías
    DELETE FROM "services-records"
        WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- Services-redemptions
    DELETE FROM "services-redemptions"
        WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- Plan-change-records (petId apunta a pets, pero petId viene de membresías del usuario)
    DELETE FROM "plan-change-records"
        WHERE "petId" IN (SELECT "petId" FROM memberships WHERE "userId" = v_mongo_id);

    -- Memberships-status-history
    DELETE FROM "memberships-status-history"
        WHERE "membershipId" IN (SELECT id FROM memberships WHERE "userId" = v_mongo_id);

    -- ================================================================
    -- 3. BORRAR MEMBERSHIPS
    -- ================================================================
    DELETE FROM "memberships" WHERE "userId" = v_mongo_id;


    -- ================================================================
    -- 4. DEPENDENCIAS DE PETS (memberships ya borradas en paso 3)
    -- ================================================================

    -- Records-files → records → pets
    DELETE FROM "records-files"
        WHERE "recordId" IN (
            SELECT id FROM records WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
        );

    DELETE FROM "records"
        WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id);

    -- Reminders y reminder-dates
    DELETE FROM "reminder-dates"
        WHERE "reminderId" IN (
            SELECT id FROM reminders WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
        );

    DELETE FROM "reminders"
        WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id);

    -- refunds-requests que apuntan a pets del usuario
    -- (edge case: si hay RR de otro userId pero con pet de este usuario)
    DELETE FROM "refund_details"
        WHERE "refundRequestId" IN (
            SELECT id FROM "refunds-requests"
            WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
        );
    DELETE FROM "refunds-requests-attachments"
        WHERE "refundRequestId" IN (
            SELECT id FROM "refunds-requests"
            WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
        );
    DELETE FROM "refunds-requests-changelog"
        WHERE "refundRequestId" IN (
            SELECT id FROM "refunds-requests"
            WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
        );
    DELETE FROM "dongraf-results"
        WHERE "refundRequestId" IN (
            SELECT id FROM "refunds-requests"
            WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id)
        );
    DELETE FROM "refunds-requests"
        WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id);

    -- plan-change-records restantes (por petId directo)
    DELETE FROM "plan-change-records"
        WHERE "petId" IN (SELECT id FROM pets WHERE owner = v_mongo_id);

    DELETE FROM "pets" WHERE owner = v_mongo_id;


    -- ================================================================
    -- 5. SPONSORS
    -- ================================================================
    DELETE FROM "sponsor-membership-payments"
        WHERE "sponsorMembershipId" IN (SELECT id FROM "sponsors-memberships" WHERE "userId" = v_user_uuid);

    DELETE FROM "sponsors-payments" WHERE "userId" = v_user_uuid;

    DELETE FROM "sponsors-memberships" WHERE "userId" = v_user_uuid;


    -- ================================================================
    -- 6. TABLAS DIRECTAS DEL USUARIO (mongoId / uuid)
    -- ================================================================

    -- pawActivities (tabla legacy, distinta de paw-activities)
    DELETE FROM "pawActivities" WHERE "userId" = v_mongo_id;

    -- customer-cards usa mongoId
    DELETE FROM "customer-cards" WHERE "userId" = v_mongo_id;

    -- shared-credits apunta a users-companies-access; borrar antes de UCA
    DELETE FROM "shared-credits"
        WHERE "ucaId" IN (SELECT id FROM "users-companies-access" WHERE "userId" = v_mongo_id)
           OR "userId" = v_user_uuid;

    -- users-companies-access (mongoId)
    DELETE FROM "users-companies-access" WHERE "userId" = v_mongo_id;

    -- donations (mongoId)
    DELETE FROM "donations" WHERE "userId" = v_mongo_id;

    -- users-welcome-emails (uuid)
    DELETE FROM "users-welcome-emails" WHERE "userId" = v_user_uuid;

    -- customs-payments (uuid) — primero borrar users-donations que apunta a customs-payments
    DELETE FROM "users-donations"
        WHERE "customPaymentId" IN (SELECT id FROM "customs-payments" WHERE "userId" = v_user_uuid)
           OR "userId" = v_user_uuid;

    DELETE FROM "customs-payments" WHERE "userId" = v_user_uuid;

    -- services-records restantes (por userId uuid directo)
    DELETE FROM "services-records" WHERE "userId" = v_user_uuid;

    -- users-credits, details, special-grants, waiting-list
    DELETE FROM "users-credits"        WHERE "userId" = v_user_uuid;
    DELETE FROM "users-details"        WHERE "userId" = v_user_uuid;
    DELETE FROM "users-special-grants" WHERE "userId" = v_user_uuid;
    DELETE FROM "waiting-list"         WHERE "userId" = v_user_uuid;

    -- users-banks-relationship (tiene FK desde refunds-requests ya borradas)
    DELETE FROM "users-banks-relationship" WHERE "userId" = v_user_uuid;

    -- verification y recovery codes
    DELETE FROM "users-verification-codes"
        WHERE email IN (SELECT email FROM users WHERE id = v_user_uuid);
    DELETE FROM "users-recovery-codes"
        WHERE dni IN (SELECT rut FROM users WHERE id = v_user_uuid);


    -- ================================================================
    -- 7. BORRAR USUARIO
    -- ================================================================
    DELETE FROM "users" WHERE id = v_user_uuid;

    RAISE NOTICE 'Éxito: usuario y todas las dependencias eliminados correctamente.';

END $$;