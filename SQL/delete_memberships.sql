-- Buscar membresía primero
-- select * from memberships where id = 'MEMBERSHIP_UUID_AQUI'

-- =====================================================
-- PREVIEW: Ver todo lo que se va a eliminar
-- =====================================================

DO $$
DECLARE
    v_membership_id uuid := '0ec44cb0-c6b5-11ee-8763-9def56488f8b';
BEGIN
    RAISE NOTICE '=== PREVIEW MEMBERSHIP: % ===', v_membership_id;
    RAISE NOTICE 'Refunds-requests:         %', (SELECT COUNT(*) FROM "refunds-requests" WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Refund-attachments:       %', (SELECT COUNT(*) FROM "refunds-requests-attachments" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id));
    RAISE NOTICE 'Refund-changelog:         %', (SELECT COUNT(*) FROM "refunds-requests-changelog" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id));
    RAISE NOTICE 'Dongraf-results:          %', (SELECT COUNT(*) FROM "dongraf-results" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id));
    RAISE NOTICE 'Refund-details:           %', (SELECT COUNT(*) FROM refund_details WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id));
    RAISE NOTICE 'CES (via refund):         %', (SELECT COUNT(*) FROM ces WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id));
    RAISE NOTICE 'Services-records (refund):%', (SELECT COUNT(*) FROM "services-records" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id));
    RAISE NOTICE 'CES (directo):            %', (SELECT COUNT(*) FROM ces WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Services-records (directo):%', (SELECT COUNT(*) FROM "services-records" WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Services-redemptions:     %', (SELECT COUNT(*) FROM "services-redemptions" WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Payments:                 %', (SELECT COUNT(*) FROM payments WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Membership-payments:      %', (SELECT COUNT(*) FROM "membership-payments" WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Membership-subscriptions: %', (SELECT COUNT(*) FROM membership_subscriptions WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Memberships-status-hist:  %', (SELECT COUNT(*) FROM "memberships-status-history" WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Paw-activities:           %', (SELECT COUNT(*) FROM "paw-activities" WHERE "membershipId" = v_membership_id);
    RAISE NOTICE 'Redemptions:              %', (SELECT COUNT(*) FROM redemptions WHERE "membershipId" = v_membership_id);
    RAISE NOTICE '=== FIN PREVIEW — revisar antes de ejecutar el DELETE ===';
END $$;


-- =====================================================
-- DELETE: Ejecutar solo si el preview es correcto
-- =====================================================

DO $$
DECLARE
    -- ===============================================================
    -- CONFIGURACIÓN: INGRESA EL ID DE LA MEMBRESÍA AQUÍ
    -- ===============================================================
    v_membership_id uuid := 'b9911650-c405-11f1-b634-5b48c4f7db8f';
    -- ===============================================================
BEGIN
    RAISE NOTICE 'Iniciando eliminación para membershipId: %', v_membership_id;

    -- ================================================================
    -- 1. REFUNDS-REQUESTS y todas sus dependencias
    --    (RESTRICT hacia memberships, hay que vaciar la cadena primero)
    -- ================================================================
    DELETE FROM "refunds-requests-attachments"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    DELETE FROM "refunds-requests-changelog"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    DELETE FROM "dongraf-results"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    DELETE FROM "ces"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    DELETE FROM "services-records"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    DELETE FROM "refund_details"
        WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    DELETE FROM "refunds-requests" WHERE "membershipId" = v_membership_id;


    -- ================================================================
    -- 2. DEPENDENCIAS DIRECTAS DE LA MEMBRESÍA
    -- ================================================================

    -- CES y services-records restantes (los ligados a refund ya se borraron arriba)
    DELETE FROM "ces" WHERE "membershipId" = v_membership_id;
    DELETE FROM "services-records" WHERE "membershipId" = v_membership_id;

    -- Redemptions (puede tener FK a paw-activities, se borra antes de paw-activities)
    DELETE FROM "redemptions" WHERE "membershipId" = v_membership_id;

    -- Payments
    DELETE FROM "payments" WHERE "membershipId" = v_membership_id;

    -- Membership-payments
    DELETE FROM "membership-payments" WHERE "membershipId" = v_membership_id;

    -- Memberships-status-history
    DELETE FROM "memberships-status-history" WHERE "membershipId" = v_membership_id;


    -- ================================================================
    -- 3. BORRAR LA MEMBRESÍA
    -- ================================================================
    DELETE FROM "memberships" WHERE id = v_membership_id;

    RAISE NOTICE 'Éxito: membresía y todas sus dependencias eliminadas correctamente.';

END $$;