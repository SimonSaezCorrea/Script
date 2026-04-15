-- REVISAR antes de borrar
SELECT 
    rr.id AS refund_id,
    rr."referenceIndex",
    rr."userId",
    rr."requestedAmount",
    rr."approvedAmount",
    rr.draft,
    (SELECT COUNT(*) FROM "dongraf-results" WHERE "refundRequestId" = rr.id) AS dongraf_count,
    (SELECT COUNT(*) FROM "refunds-requests-attachments" WHERE "refundRequestId" = rr.id) AS attachments_count,
    (SELECT COUNT(*) FROM "refunds-requests-changelog" WHERE "refundRequestId" = rr.id) AS changelog_count,
    (SELECT COUNT(*) FROM ces WHERE "refundRequestId" = rr.id) AS ces_count,
    (SELECT COUNT(*) FROM "services-records" WHERE "refundRequestId" = rr.id) AS services_records_count
FROM "refunds-requests" rr
WHERE rr.id = '6376d8ce-8863-4693-bf71-6068fce5f0c9';

-- =====================================================
-- ELIMINAR REFUND Y TODA SU DATA RELACIONADA
-- Reemplaza <REFUND_ID> con el UUID del refund
-- =====================================================

DO $$
DECLARE
    v_refund_id UUID := '6376d8ce-8863-4693-bf71-6068fce5f0c9';
BEGIN

    -- 1. Dongraf results (apunta a refunds-requests)
    DELETE FROM "dongraf-results"
    WHERE "refundRequestId" = v_refund_id;

    -- 2. Attachments (apunta a refunds-requests)
    DELETE FROM "refunds-requests-attachments"
    WHERE "refundRequestId" = v_refund_id;

    -- 3. Changelog (apunta a refunds-requests)
    DELETE FROM "refunds-requests-changelog"
    WHERE "refundRequestId" = v_refund_id;

    -- 4. CES - Customer Effort Score (apunta a refunds-requests)
    DELETE FROM ces
    WHERE "refundRequestId" = v_refund_id;

    -- 5. Services records (apunta a refunds-requests)
    DELETE FROM "services-records"
    WHERE "refundRequestId" = v_refund_id;

    -- 6. Records que apuntan a services-redemptions vinculadas al refund
    DELETE FROM records
    WHERE "serviceRedemptionId" IN (
        SELECT sr.id FROM "services-redemptions" sr
        JOIN "services-records" srec ON srec."membershipId" = sr."membershipId"
        WHERE srec."refundRequestId" = v_refund_id
    );

    -- 7. El refund en sí
    DELETE FROM "refunds-requests"
    WHERE id = v_refund_id;

    RAISE NOTICE 'Refund % eliminado correctamente', v_refund_id;

END $$;