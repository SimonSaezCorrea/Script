-- =====================================================
-- PREVIEW: Ver todo lo que se va a eliminar
-- Reemplaza <PET_ID> con el UUID de la mascota
-- =====================================================

SELECT
    p.id                                                                        AS pet_id,
    p.name                                                                      AS pet_name,
    (SELECT COUNT(*) FROM reminders             WHERE "petId"  = p.id)          AS reminders,
    (SELECT COUNT(*) FROM records               WHERE "petId"  = p.id)          AS records,
    (SELECT COUNT(*) FROM "plan-change-records" WHERE "petId"  = p.id)          AS plan_change_records,
    (SELECT COUNT(*) FROM "refunds-requests"    WHERE "petId"  = p.id)          AS refund_requests,
    (SELECT COUNT(*) FROM memberships           WHERE "petId"  = p.id)          AS memberships
FROM pets p
WHERE p.id = '882f1000-14b0-11ef-9078-537f5de8c432';


-- =====================================================
-- DELETE: Eliminar mascota y toda su data relacionada
-- Reemplaza <PET_ID> con el UUID de la mascota
-- =====================================================

DO $$
DECLARE
    v_pet_id        UUID := '0c1029d0-7146-11ef-b78d-4d2e12272968';
    v_refund_ids    UUID[];
    v_membership_ids UUID[];
    v_paw_ids       UUID[];
    v_redemption_ids UUID[];
    v_svc_redemption_ids UUID[];
BEGIN

    RAISE NOTICE '>>> Iniciando eliminación de mascota: %', v_pet_id;

    -- Recolectamos IDs necesarios antes de borrar
    SELECT ARRAY_AGG(id) INTO v_refund_ids
    FROM "refunds-requests" WHERE "petId" = v_pet_id;

    SELECT ARRAY_AGG(id) INTO v_membership_ids
    FROM memberships WHERE "petId" = v_pet_id;

    SELECT ARRAY_AGG(pa.id) INTO v_paw_ids
    FROM "paw-activities" pa
    WHERE pa."membershipId" = ANY(v_membership_ids);

    SELECT ARRAY_AGG(id) INTO v_redemption_ids
    FROM redemptions WHERE "membershipId" = ANY(v_membership_ids);

    SELECT ARRAY_AGG(id) INTO v_svc_redemption_ids
    FROM "services-redemptions" WHERE "membershipId" = ANY(v_membership_ids);

    -- -------------------------
    -- 1. REFUNDS y sus hijos
    -- -------------------------
    IF v_refund_ids IS NOT NULL THEN

        RAISE NOTICE '  -> Eliminando dongraf-results de % refunds', array_length(v_refund_ids, 1);
        DELETE FROM "dongraf-results"
        WHERE "refundRequestId" = ANY(v_refund_ids);

        RAISE NOTICE '  -> Eliminando refunds-requests-attachments';
        DELETE FROM "refunds-requests-attachments"
        WHERE "refundRequestId" = ANY(v_refund_ids);

        RAISE NOTICE '  -> Eliminando refunds-requests-changelog';
        DELETE FROM "refunds-requests-changelog"
        WHERE "refundRequestId" = ANY(v_refund_ids);

        RAISE NOTICE '  -> Eliminando ces (por refund)';
        DELETE FROM ces
        WHERE "refundRequestId" = ANY(v_refund_ids);

        RAISE NOTICE '  -> Eliminando services-records (por refund)';
        DELETE FROM "services-records"
        WHERE "refundRequestId" = ANY(v_refund_ids);

        RAISE NOTICE '  -> Eliminando refunds-requests';
        DELETE FROM "refunds-requests"
        WHERE id = ANY(v_refund_ids);

    END IF;

    -- -------------------------
    -- 2. REMINDERS y sus hijos
    -- -------------------------
    RAISE NOTICE '  -> Eliminando reminder-dates';
    DELETE FROM "reminder-dates"
    WHERE "reminderId" IN (
        SELECT id FROM reminders WHERE "petId" = v_pet_id
    );

    RAISE NOTICE '  -> Eliminando reminders';
    DELETE FROM reminders WHERE "petId" = v_pet_id;

    -- -------------------------
    -- 3. RECORDS y sus hijos
    -- -------------------------
    RAISE NOTICE '  -> Eliminando records-files';
    DELETE FROM "records-files"
    WHERE "recordId" IN (
        SELECT id FROM records WHERE "petId" = v_pet_id
    );

    RAISE NOTICE '  -> Eliminando records';
    DELETE FROM records WHERE "petId" = v_pet_id;

    -- -------------------------
    -- 4. PLAN CHANGE RECORDS
    -- -------------------------
    RAISE NOTICE '  -> Eliminando plan-change-records';
    DELETE FROM "plan-change-records" WHERE "petId" = v_pet_id;

    -- -------------------------
    -- 5. MEMBERSHIPS y sus hijos
    -- -------------------------
    IF v_membership_ids IS NOT NULL THEN

        RAISE NOTICE '  -> Eliminando membership-payments';
        DELETE FROM "membership-payments"
        WHERE "membershipId" = ANY(v_membership_ids);

        RAISE NOTICE '  -> Eliminando membership_subscriptions';
        DELETE FROM membership_subscriptions
        WHERE "membershipId" = ANY(v_membership_ids);

        RAISE NOTICE '  -> Eliminando payments';
        DELETE FROM payments
        WHERE "membershipId" = ANY(v_membership_ids);

        RAISE NOTICE '  -> Eliminando ces (por membership)';
        DELETE FROM ces
        WHERE "membershipId" = ANY(v_membership_ids);

        RAISE NOTICE '  -> Eliminando services-records (por membership)';
        DELETE FROM "services-records"
        WHERE "membershipId" = ANY(v_membership_ids);

        -- Donations dependen de paw-activities
        IF v_paw_ids IS NOT NULL THEN
            RAISE NOTICE '  -> Eliminando donations';
            DELETE FROM donations
            WHERE "pawActivityId" = ANY(v_paw_ids);
        END IF;

        RAISE NOTICE '  -> Eliminando paw-activities';
        DELETE FROM "paw-activities"
        WHERE "membershipId" = ANY(v_membership_ids);

        -- Redemptions pueden apuntar a paw-activities, borrar antes
        IF v_redemption_ids IS NOT NULL THEN
            RAISE NOTICE '  -> Eliminando redemptions';
            DELETE FROM redemptions
            WHERE id = ANY(v_redemption_ids);
        END IF;

        -- Records que apuntan a services-redemptions de esta mascota
        IF v_svc_redemption_ids IS NOT NULL THEN
            RAISE NOTICE '  -> Eliminando records vinculados a services-redemptions';
            DELETE FROM records
            WHERE "serviceRedemptionId" = ANY(v_svc_redemption_ids);

            RAISE NOTICE '  -> Eliminando services-redemptions';
            DELETE FROM "services-redemptions"
            WHERE id = ANY(v_svc_redemption_ids);
        END IF;

        RAISE NOTICE '  -> Eliminando memberships';
        DELETE FROM memberships WHERE id = ANY(v_membership_ids);

    END IF;

    -- -------------------------
    -- 6. PET
    -- -------------------------
    RAISE NOTICE '  -> Eliminando pet';
    DELETE FROM pets WHERE id = v_pet_id;

    RAISE NOTICE '>>> Mascota % eliminada correctamente', v_pet_id;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al eliminar mascota %: % - %', v_pet_id, SQLSTATE, SQLERRM;
END $$;