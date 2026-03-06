-- =====================================================
-- PREVIEW: Refunds sin petId o sin serviceId
-- =====================================================

SELECT
    rr.id,
    rr."referenceIndex",
    rr."referenceNumber",
    rr."userId",
    u.name || ' ' || u.surname          AS user_name,
    rr."petId",
    rr."serviceId",
    rr."requestedAmount",
    rr."approvedAmount",
    rr.draft,
    rr."dgStatus",
    rr."createdAt",
    -- Conteo de hijos para saber qué se va a arrastrar
    (SELECT COUNT(*) FROM "dongraf-results"              WHERE "refundRequestId" = rr.id) AS dongraf_count,
    (SELECT COUNT(*) FROM "refunds-requests-attachments" WHERE "refundRequestId" = rr.id) AS attachments_count,
    (SELECT COUNT(*) FROM "refunds-requests-changelog"   WHERE "refundRequestId" = rr.id) AS changelog_count,
    (SELECT COUNT(*) FROM ces                            WHERE "refundRequestId" = rr.id) AS ces_count,
    (SELECT COUNT(*) FROM "services-records"             WHERE "refundRequestId" = rr.id) AS services_records_count
FROM "refunds-requests" rr
LEFT JOIN users u ON u.id = rr."userId"
WHERE rr."petId" IS NULL
   OR rr."serviceId" IS NULL
ORDER BY rr."createdAt" DESC;


-- =====================================================
-- DELETE: Eliminar refunds sin petId o sin serviceId
-- y toda su data relacionada
-- =====================================================

DO $$
DECLARE
    v_refund_ids UUID[];
BEGIN

    -- Recolectamos los IDs afectados
    SELECT ARRAY_AGG(id) INTO v_refund_ids
    FROM "refunds-requests"
    WHERE "petId" IS NULL
       OR "serviceId" IS NULL;

    IF v_refund_ids IS NULL THEN
        RAISE NOTICE 'No se encontraron refunds sin petId o serviceId. Nada que eliminar.';
        RETURN;
    END IF;

    RAISE NOTICE '>>> % refunds encontrados para eliminar', array_length(v_refund_ids, 1);

    -- 1. Dongraf results
    DELETE FROM "dongraf-results"
    WHERE "refundRequestId" = ANY(v_refund_ids);
    RAISE NOTICE '  -> dongraf-results eliminados';

    -- 2. Attachments
    DELETE FROM "refunds-requests-attachments"
    WHERE "refundRequestId" = ANY(v_refund_ids);
    RAISE NOTICE '  -> refunds-requests-attachments eliminados';

    -- 3. Changelog
    DELETE FROM "refunds-requests-changelog"
    WHERE "refundRequestId" = ANY(v_refund_ids);
    RAISE NOTICE '  -> refunds-requests-changelog eliminados';

    -- 4. CES
    DELETE FROM ces
    WHERE "refundRequestId" = ANY(v_refund_ids);
    RAISE NOTICE '  -> ces eliminados';

    -- 5. Services records
    DELETE FROM "services-records"
    WHERE "refundRequestId" = ANY(v_refund_ids);
    RAISE NOTICE '  -> services-records eliminados';

    -- 6. Los refunds
    DELETE FROM "refunds-requests"
    WHERE id = ANY(v_refund_ids);
    RAISE NOTICE '  -> refunds-requests eliminados: %', array_length(v_refund_ids, 1);

    RAISE NOTICE '>>> Limpieza completada exitosamente';

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error durante la limpieza: % - %', SQLSTATE, SQLERRM;
END $$;