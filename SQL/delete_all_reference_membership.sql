-- ============================================================
-- REVISAR antes de borrar
-- ============================================================

SELECT
    m.id AS membership_id,
    m."userId",
    m."planId",
    m.status,
    m."startDate",
    m."endDate",
    m."paymentInterval",
    m."createdAt",
    p.id AS pet_id,
    p.name AS pet_name,
    p.species AS pet_species,
    (SELECT COUNT(*) FROM "refunds-requests"             WHERE "membershipId" = m.id) AS refunds_count,
    (SELECT COUNT(*) FROM "membership-payments"          WHERE "membershipId" = m.id) AS membership_payments_count,
    (SELECT COUNT(*) FROM payments                       WHERE "membershipId" = m.id) AS payments_count,
    (SELECT COUNT(*) FROM "memberships-status-history"   WHERE "membershipId" = m.id) AS status_history_count,
    (SELECT COUNT(*) FROM redemptions                    WHERE "membershipId" = m.id) AS redemptions_count,
    (SELECT COUNT(*) FROM ces                            WHERE "membershipId" = m.id) AS ces_count,
    (SELECT COUNT(*) FROM "services-records"             WHERE "membershipId" = m.id) AS services_records_count,
    (SELECT COUNT(*) FROM "solidario-sponsorship-offers" WHERE "membershipId" = m.id) AS solidario_offers_count,
    (SELECT COUNT(*) FROM "refunds-requests-changelog"   WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = m.id)) AS refund_changelogs_count,
    (SELECT COUNT(*) FROM "refunds-requests-attachments" WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = m.id)) AS refund_attachments_count,
    (SELECT COUNT(*) FROM "dongraf-results"              WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = m.id)) AS dongraf_count,
    (SELECT COUNT(*) FROM refund_details                 WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = m.id)) AS refund_details_count,
    (SELECT COUNT(*) FROM "plan-change-records" WHERE "petId" = p.id) AS plan_changes_count,
    (SELECT COUNT(*) FROM reminders             WHERE "petId" = p.id) AS reminders_count,
    (SELECT COUNT(*) FROM records               WHERE "petId" = p.id) AS records_count,
    (SELECT COUNT(*) FROM "clinic-invoices"     WHERE "petId" = p.id) AS clinic_invoices_count
FROM memberships m
JOIN pets p ON p.id = m."petId"
WHERE m.id = '4196d3b0-408f-11f0-bf32-a5dd4fe449c9';

-- ============================================================
-- ELIMINAR MEMBRESÍA, MASCOTA Y TODA SU DATA RELACIONADA
-- ============================================================

DO $$
DECLARE
    v_membership_id UUID := '04a39040-bb97-11f1-9313-5d0b3a378b85';
    v_pet_id        UUID;
BEGIN

    SELECT "petId" INTO v_pet_id FROM memberships WHERE id = v_membership_id;

    IF v_pet_id IS NULL THEN
        RAISE EXCEPTION 'Membresía % no existe', v_membership_id;
    END IF;

    -- 1. Dongraf results
    DELETE FROM "dongraf-results"
    WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    -- 2. Refund details
    DELETE FROM refund_details
    WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    -- 3. Refund attachments
    DELETE FROM "refunds-requests-attachments"
    WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    -- 4. Refund changelogs
    DELETE FROM "refunds-requests-changelog"
    WHERE "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    -- 5. CES
    DELETE FROM ces WHERE "membershipId" = v_membership_id;

    -- 6. Services records (por membershipId Y por refundRequestId)
    DELETE FROM "services-records"
    WHERE "membershipId" = v_membership_id
       OR "refundRequestId" IN (SELECT id FROM "refunds-requests" WHERE "membershipId" = v_membership_id);

    -- 7. Refund requests
    DELETE FROM "refunds-requests" WHERE "membershipId" = v_membership_id;

    -- 8. Membership payments
    DELETE FROM "membership-payments" WHERE "membershipId" = v_membership_id;

    -- 9. Legacy payments
    DELETE FROM payments WHERE "membershipId" = v_membership_id;

    -- 10. Membership status history
    DELETE FROM "memberships-status-history" WHERE "membershipId" = v_membership_id;

    -- 12. Redemptions
    DELETE FROM redemptions WHERE "membershipId" = v_membership_id;

    -- 13. Ofertas de apadrinamiento Solidario
    DELETE FROM "solidario-sponsorship-offers" WHERE "membershipId" = v_membership_id;

    -- 14. Membresía
    DELETE FROM memberships WHERE id = v_membership_id;

    -- 15. Plan change records de la mascota
    DELETE FROM "plan-change-records" WHERE "petId" = v_pet_id;

    -- 16. Records files (via records de la mascota)
    DELETE FROM "records-files"
    WHERE "recordId" IN (SELECT id FROM records WHERE "petId" = v_pet_id);

    -- 17. Records de la mascota
    DELETE FROM records WHERE "petId" = v_pet_id;

    -- 18. Reminder dates (via reminders de la mascota)
    DELETE FROM "reminder-dates"
    WHERE "reminderId" IN (SELECT id FROM reminders WHERE "petId" = v_pet_id);

    -- 19. Reminders de la mascota
    DELETE FROM reminders WHERE "petId" = v_pet_id;

    -- 20. Boletas de clínica: se desvinculan, no se borran (son data de la clínica)
    UPDATE "clinic-invoices" SET "petId" = NULL WHERE "petId" = v_pet_id;

    -- 21. Mascota
    DELETE FROM pets WHERE id = v_pet_id;

    RAISE NOTICE 'Membresía % y mascota % eliminadas correctamente', v_membership_id, v_pet_id;

END $$;