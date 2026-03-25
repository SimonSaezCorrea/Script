-- =====================================================
-- PREVIEW: Ver todo lo que se va a eliminar
-- =====================================================

SELECT
    m.id                                                                                        AS membership_id,
    m."userId",
    m.status,
    m."paymentInterval",
    m."acquisitionChannel",
    m."createdAt",
    m."updatedAt",
    m."startDate",
    m."deletedAt",
    p.id                                                                                        AS pet_id,
    p.name                                                                                      AS pet_name,
    p.species                                                                                   AS pet_species,
    (SELECT COUNT(*) FROM payments                  WHERE "membershipId" = m.id)                AS payments_count,
    (SELECT COUNT(*) FROM "membership-payments"     WHERE "membershipId" = m.id)                AS membership_payments_count,
    (SELECT COUNT(*) FROM membership_subscriptions  WHERE "membershipId" = m.id)                AS subscriptions_count,
    (SELECT COUNT(*) FROM "paw-activities"          WHERE "membershipId" = m.id)                AS paw_activities_count,
    (SELECT COUNT(*) FROM redemptions               WHERE "membershipId" = m.id)                AS redemptions_count,
    (SELECT COUNT(*) FROM "services-records"        WHERE "membershipId" = m.id)                AS services_records_count,
    (SELECT COUNT(*) FROM "services-redemptions"    WHERE "membershipId" = m.id)                AS services_redemptions_count,
    (SELECT COUNT(*) FROM ces                       WHERE "membershipId" = m.id)                AS ces_count,
    (SELECT COUNT(*) FROM reminders                 WHERE "petId" = p.id)                       AS reminders_count,
    (SELECT COUNT(*) FROM records                   WHERE "petId" = p.id)                       AS records_count,
    (SELECT COUNT(*) FROM "plan-change-records"     WHERE "petId" = p.id)                       AS plan_change_records_count,
    (SELECT COUNT(*) FROM "refunds-requests"        WHERE "petId" = p.id)                       AS refunds_count
FROM memberships m
JOIN pets p ON p.id = m."petId"
JOIN "users-companies-access" uca ON uca."userId" = m."userId"
WHERE uca."companyId" = '936e7170-fbb0-11f0-9a7a-71ed286cff15'
  AND m.status = 5;


-- =====================================================
-- DELETE: Eliminar memberships con status=5 de
-- Pacífico Pet (companyId = '936e7170-fbb0-11f0-9a7a-71ed286cff15'),
-- sus pets y todas sus relaciones.
-- No toca usuarios ni sus relaciones.
-- =====================================================

DO $$
DECLARE
    -- =====================================================
    -- Memberships con status=5 de Pacífico Pet
    -- =====================================================
    v_input_membership_ids  UUID[];
    -- =====================================================

    v_pet_ids               UUID[];
    v_all_membership_ids    UUID[];
    v_refund_ids            UUID[];
    v_paw_ids               UUID[];
    v_svc_redemption_ids    UUID[];
BEGIN

    -- -------------------------
    -- Recolectamos los membership IDs con status=5
    -- pertenecientes a usuarios de la empresa
    -- -------------------------
    SELECT ARRAY_AGG(DISTINCT m.id) INTO v_input_membership_ids
    FROM memberships m
    JOIN "users-companies-access" uca ON uca."userId" = m."userId"
    WHERE uca."companyId" = '936e7170-fbb0-11f0-9a7a-71ed286cff15'
      AND m.status = 5;

    IF v_input_membership_ids IS NULL THEN
        RAISE EXCEPTION 'No se encontraron memberships con status=5 para la empresa indicada';
    END IF;

    RAISE NOTICE '>>> Iniciando eliminación de % memberships con status=5 de Pacífico Pet',
        array_length(v_input_membership_ids, 1);

    -- -------------------------
    -- Obtenemos todos los petIds del listado
    -- -------------------------
    SELECT ARRAY_AGG(DISTINCT "petId") INTO v_pet_ids
    FROM memberships
    WHERE id = ANY(v_input_membership_ids)
      AND "petId" IS NOT NULL;

    IF v_pet_ids IS NULL THEN
        RAISE EXCEPTION 'No se encontraron pets asociados a los memberships indicados';
    END IF;

    RAISE NOTICE '  -> Pets encontrados: %', array_length(v_pet_ids, 1);

    -- -------------------------
    -- Recolectamos TODOS los memberships de esos pets
    -- (pueden tener más de uno cada uno)
    -- -------------------------
    SELECT ARRAY_AGG(id) INTO v_all_membership_ids
    FROM memberships
    WHERE "petId" = ANY(v_pet_ids);

    RAISE NOTICE '  -> Total memberships a eliminar (incluyendo históricos): %',
        array_length(v_all_membership_ids, 1);

    -- -------------------------
    -- Recolectamos refunds de todos los pets
    -- -------------------------
    SELECT ARRAY_AGG(id) INTO v_refund_ids
    FROM "refunds-requests"
    WHERE "petId" = ANY(v_pet_ids);

    -- -------------------------
    -- Recolectamos paw-activities de todos los memberships
    -- -------------------------
    SELECT ARRAY_AGG(id) INTO v_paw_ids
    FROM "paw-activities"
    WHERE "membershipId" = ANY(v_all_membership_ids);

    -- -------------------------
    -- Recolectamos services-redemptions de todos los memberships
    -- -------------------------
    SELECT ARRAY_AGG(id) INTO v_svc_redemption_ids
    FROM "services-redemptions"
    WHERE "membershipId" = ANY(v_all_membership_ids);

    -- =========================
    -- 1. REFUNDS y sus hijos
    -- =========================
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

        RAISE NOTICE '  -> Eliminando refund_details';
        DELETE FROM refund_details
        WHERE "refundRequestId" = ANY(v_refund_ids);

        RAISE NOTICE '  -> Eliminando refunds-requests';
        DELETE FROM "refunds-requests"
        WHERE id = ANY(v_refund_ids);

    END IF;

    -- =========================
    -- 2. REMINDERS de los pets
    -- =========================
    RAISE NOTICE '  -> Eliminando reminder-dates';
    DELETE FROM "reminder-dates"
    WHERE "reminderId" IN (
        SELECT id FROM reminders WHERE "petId" = ANY(v_pet_ids)
    );

    RAISE NOTICE '  -> Eliminando reminders';
    DELETE FROM reminders WHERE "petId" = ANY(v_pet_ids);

    -- =========================
    -- 3. RECORDS de los pets
    -- =========================
    RAISE NOTICE '  -> Eliminando records-files';
    DELETE FROM "records-files"
    WHERE "recordId" IN (
        SELECT id FROM records WHERE "petId" = ANY(v_pet_ids)
    );

    IF v_svc_redemption_ids IS NOT NULL THEN
        RAISE NOTICE '  -> Eliminando records vinculados a services-redemptions';
        DELETE FROM records
        WHERE "serviceRedemptionId" = ANY(v_svc_redemption_ids);
    END IF;

    RAISE NOTICE '  -> Eliminando records';
    DELETE FROM records WHERE "petId" = ANY(v_pet_ids);

    -- =========================
    -- 4. PLAN CHANGE RECORDS
    -- =========================
    RAISE NOTICE '  -> Eliminando plan-change-records';
    DELETE FROM "plan-change-records" WHERE "petId" = ANY(v_pet_ids);

    -- =========================
    -- 5. MEMBERSHIPS y sus hijos
    -- =========================
    RAISE NOTICE '  -> Eliminando membership-payments';
    DELETE FROM "membership-payments"
    WHERE "membershipId" = ANY(v_all_membership_ids);

    RAISE NOTICE '  -> Eliminando membership_subscriptions';
    DELETE FROM membership_subscriptions
    WHERE "membershipId" = ANY(v_all_membership_ids);

    RAISE NOTICE '  -> Eliminando payments';
    DELETE FROM payments
    WHERE "membershipId" = ANY(v_all_membership_ids);

    RAISE NOTICE '  -> Eliminando ces (por membership)';
    DELETE FROM ces
    WHERE "membershipId" = ANY(v_all_membership_ids);

    RAISE NOTICE '  -> Eliminando services-records (por membership)';
    DELETE FROM "services-records"
    WHERE "membershipId" = ANY(v_all_membership_ids);

    IF v_paw_ids IS NOT NULL THEN
        RAISE NOTICE '  -> Eliminando donations';
        DELETE FROM donations
        WHERE "pawActivityId" = ANY(v_paw_ids);
    END IF;

    RAISE NOTICE '  -> Eliminando paw-activities';
    DELETE FROM "paw-activities"
    WHERE "membershipId" = ANY(v_all_membership_ids);

    RAISE NOTICE '  -> Eliminando redemptions';
    DELETE FROM redemptions
    WHERE "membershipId" = ANY(v_all_membership_ids);

    IF v_svc_redemption_ids IS NOT NULL THEN
        RAISE NOTICE '  -> Eliminando services-redemptions';
        DELETE FROM "services-redemptions"
        WHERE id = ANY(v_svc_redemption_ids);
    END IF;

    RAISE NOTICE '  -> Eliminando memberships-status-history';
    DELETE FROM "memberships-status-history"
    WHERE "membershipId" = ANY(v_all_membership_ids);

    RAISE NOTICE '  -> Eliminando memberships';
    DELETE FROM memberships
    WHERE id = ANY(v_all_membership_ids);

    -- =========================
    -- 6. PETS
    -- =========================
    RAISE NOTICE '  -> Eliminando % pets', array_length(v_pet_ids, 1);
    DELETE FROM pets WHERE id = ANY(v_pet_ids);

    RAISE NOTICE '>>> Eliminación completada. Memberships input: % | Pets eliminados: % | Memberships eliminados: %',
        array_length(v_input_membership_ids, 1),
        array_length(v_pet_ids, 1),
        array_length(v_all_membership_ids, 1);

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error durante la eliminación: % - %', SQLSTATE, SQLERRM;
END $$;