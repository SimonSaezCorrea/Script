select * from users
where rut='234097396'
--where email='camilomaldonadorecabal@gmail.com'

-- Buscar usuario primero
-- select id, rut, email from users where rut = '210843841';
-- select id, rut, email from users where email = 'simon@somospawer.com';

WITH p  AS (SELECT '3f540bac-630f-498f-b84a-2c8f2c0100e0'::uuid AS user_id),   -- 👈 solo cambia esto
m  AS (SELECT id FROM memberships WHERE "userId" = (SELECT user_id FROM p)),
pe AS (SELECT id FROM pets WHERE owner = (SELECT user_id FROM p)),
rr AS (SELECT id FROM "refunds-requests"
       WHERE "userId" = (SELECT user_id FROM p)
          OR "petId" IN (SELECT id FROM pe)
          OR "membershipId" IN (SELECT id FROM m)),
at AS (SELECT id FROM attendances WHERE "membershipId"::text IN (SELECT id::text FROM m)),
sm AS (SELECT id FROM "sponsors-memberships" WHERE "userId" = (SELECT user_id FROM p)),
cp AS (SELECT id FROM "customs-payments" WHERE "userId" = (SELECT user_id FROM p))
SELECT
  (SELECT rut FROM users WHERE id = (SELECT user_id FROM p))                                         AS "rut",
  (SELECT count(*) FROM coverage_quotes WHERE "userId" = (SELECT user_id FROM p)
                                           OR "membershipId" IN (SELECT id FROM m))                 AS "coverage_quotes",
  (SELECT count(*) FROM ces WHERE "refundRequestId" IN (SELECT id FROM rr)
                               OR "membershipId" IN (SELECT id FROM m))                             AS "ces",
  (SELECT count(*) FROM refund_details WHERE "refundRequestId" IN (SELECT id FROM rr))               AS "refund_details",
  (SELECT count(*) FROM "services-records" WHERE "userId" = (SELECT user_id FROM p)
                                              OR "membershipId" IN (SELECT id FROM m)
                                              OR "refundRequestId" IN (SELECT id FROM rr)
                                              OR "attendanceId" IN (SELECT id FROM at))             AS "services-records",
  (SELECT count(*) FROM at)                                                                          AS "attendances",
  (SELECT count(*) FROM "clinic-invoices" WHERE "userId" = (SELECT user_id FROM p)
                                             OR "petId" IN (SELECT id FROM pe))                     AS "clinic-invoices (→NULL)",
  (SELECT count(*) FROM rr)                                                                          AS "refunds-requests",
  (SELECT count(*) FROM payments WHERE "userId" = (SELECT user_id FROM p)
                                    OR "membershipId" IN (SELECT id FROM m))                        AS "payments",
  (SELECT count(*) FROM "membership-payments" WHERE "membershipId" IN (SELECT id FROM m))            AS "membership-payments",
  (SELECT count(*) FROM redemptions WHERE "userId" = (SELECT user_id FROM p)
                                       OR "membershipId" IN (SELECT id FROM m))                     AS "redemptions",
  (SELECT count(*) FROM "solidario-sponsorship-offers" WHERE "membershipId" IN (SELECT id FROM m))   AS "solidario-offers",
  (SELECT count(*) FROM m)                                                                           AS "memberships",
  (SELECT count(*) FROM "users-companies-access" WHERE "userId" = (SELECT user_id FROM p))           AS "users-companies-access",
  (SELECT count(*) FROM "plan-change-records" WHERE "petId" IN (SELECT id FROM pe))                  AS "plan-change-records",
  (SELECT count(*) FROM records WHERE "petId" IN (SELECT id FROM pe))                                AS "records",
  (SELECT count(*) FROM records WHERE "createdByUserId" = (SELECT user_id FROM p)
                                   AND "petId" NOT IN (SELECT id FROM pe))                          AS "records ajenos (→NULL)",
  (SELECT count(*) FROM pe)                                                                          AS "pets",
  (SELECT count(*) FROM sm)                                                                          AS "sponsors-memberships",
  (SELECT count(*) FROM "sponsors-payments" WHERE "userId" = (SELECT user_id FROM p)
                                               OR "sponsorMembershipId" IN (SELECT id FROM sm))     AS "sponsors-payments",
  (SELECT count(*) FROM cp)                                                                          AS "customs-payments",
  (SELECT count(*) FROM "users-details" WHERE "userId" = (SELECT user_id FROM p))                    AS "users-details",
  (SELECT count(*) FROM identity_verification_codes WHERE "userId" = (SELECT user_id FROM p))        AS "identity_verification_codes",
  (SELECT count(*) FROM user_contact_mediums WHERE "userId" = (SELECT user_id FROM p))               AS "user_contact_mediums",
  (SELECT count(*) FROM "opposition-requests" WHERE "userId" = (SELECT user_id FROM p))              AS "opposition-requests ⚠️",
  (SELECT count(*) FROM "portability-requests" WHERE "userId" = (SELECT user_id FROM p))             AS "portability-requests ⚠️",
  (SELECT count(*) FROM "users-banks-relationship" WHERE "userId" = (SELECT user_id FROM p))         AS "bank-accounts (cascade)",
  (SELECT count(*) FROM "felix-activation-codes" WHERE "usedByUserId" = (SELECT user_id FROM p))     AS "felix-codes (→NULL)",
  (SELECT count(*) FROM codes WHERE "rewardsToId" = (SELECT user_id FROM p)::text)                   AS "codes (→NULL)";


-- =====================================================
-- DELETE: Ejecutar solo si el preview es correcto
-- =====================================================	
	

DO $$
DECLARE
    v_user_id uuid := '967dfee3-0a5d-4565-badc-bb2184472c53';   -- 👈 solo cambia esto
    v_rut     text;
BEGIN
    SELECT rut INTO v_rut FROM users WHERE id = v_user_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Usuario % no existe', v_user_id;
    END IF;
    RAISE NOTICE 'Eliminando usuario %', v_user_id;

    -- Conjuntos de ids afectados (se descartan al terminar la transacción)
    CREATE TEMP TABLE _m  ON COMMIT DROP AS SELECT id FROM memberships WHERE "userId" = v_user_id;
    CREATE TEMP TABLE _p  ON COMMIT DROP AS SELECT id FROM pets WHERE owner = v_user_id;
    CREATE TEMP TABLE _rr ON COMMIT DROP AS
        SELECT id FROM "refunds-requests"
        WHERE "userId" = v_user_id
           OR "petId" IN (SELECT id FROM _p)
           OR "membershipId" IN (SELECT id FROM _m);
    CREATE TEMP TABLE _at ON COMMIT DROP AS
        SELECT id FROM attendances WHERE "membershipId"::text IN (SELECT id::text FROM _m);

    -- 1. Cotizaciones (RESTRICT sobre users y memberships; las líneas caen en cascada)
    DELETE FROM coverage_quotes
        WHERE "userId" = v_user_id OR "membershipId" IN (SELECT id FROM _m);

    -- 2. Hijos de reembolsos, membresías y atenciones
    DELETE FROM ces
        WHERE "refundRequestId" IN (SELECT id FROM _rr) OR "membershipId" IN (SELECT id FROM _m);
    DELETE FROM refund_details WHERE "refundRequestId" IN (SELECT id FROM _rr);
    DELETE FROM "services-records"
        WHERE "userId" = v_user_id
           OR "membershipId" IN (SELECT id FROM _m)
           OR "refundRequestId" IN (SELECT id FROM _rr)
           OR "attendanceId" IN (SELECT id FROM _at);

    -- 3. Atenciones; las facturas de clínica se conservan, solo se desvinculan
    DELETE FROM attendances WHERE id IN (SELECT id FROM _at);
    UPDATE "clinic-invoices" SET "userId" = NULL WHERE "userId" = v_user_id;
    UPDATE "clinic-invoices" SET "petId"  = NULL WHERE "petId" IN (SELECT id FROM _p);

    -- 4. Reembolsos (adjuntos, changelog y dongraf-results caen en cascada)
    DELETE FROM "refunds-requests" WHERE id IN (SELECT id FROM _rr);

    -- 5. Hijos de membresías
    DELETE FROM payments
        WHERE "userId" = v_user_id OR "membershipId" IN (SELECT id FROM _m);
    DELETE FROM "membership-payments" WHERE "membershipId" IN (SELECT id FROM _m);
    DELETE FROM redemptions
        WHERE "userId" = v_user_id OR "membershipId" IN (SELECT id FROM _m);
    DELETE FROM "solidario-sponsorship-offers" WHERE "membershipId" IN (SELECT id FROM _m);
    DELETE FROM "plan-change-records" WHERE "petId" IN (SELECT id FROM _p);

    -- 6. Membresías (status-history cae en cascada) y accesos de empresa
    DELETE FROM memberships WHERE id IN (SELECT id FROM _m);
    DELETE FROM "users-companies-access" WHERE "userId" = v_user_id;

    -- 7. Fichas clínicas; las que creó en mascotas ajenas se conservan sin autor
    DELETE FROM "records-files"
        WHERE "recordId" IN (SELECT id FROM records WHERE "petId" IN (SELECT id FROM _p));
    DELETE FROM records WHERE "petId" IN (SELECT id FROM _p);
    UPDATE records SET "createdByUserId" = NULL WHERE "createdByUserId" = v_user_id;

    -- 8. Mascotas (reminders y reminder-dates caen en cascada)
    DELETE FROM pets WHERE id IN (SELECT id FROM _p);

    -- 9. Apadrinamientos
    DELETE FROM "sponsor-membership-payments"
        WHERE "sponsorMembershipId" IN (SELECT id FROM "sponsors-memberships" WHERE "userId" = v_user_id);
    DELETE FROM "sponsors-payments"
        WHERE "userId" = v_user_id
           OR "sponsorMembershipId" IN (SELECT id FROM "sponsors-memberships" WHERE "userId" = v_user_id);
    DELETE FROM "sponsors-memberships" WHERE "userId" = v_user_id;

    -- 10. Donaciones y pagos personalizados
    DELETE FROM "users-donations"
        WHERE "userId" = v_user_id
           OR "customPaymentId" IN (SELECT id FROM "customs-payments" WHERE "userId" = v_user_id);
    DELETE FROM "customs-payments" WHERE "userId" = v_user_id;

    -- 11. Tablas directas del usuario (FK NO ACTION)
    DELETE FROM "users-details"             WHERE "userId" = v_user_id;
    DELETE FROM "waiting-list"              WHERE "userId" = v_user_id;
    DELETE FROM identity_verification_codes WHERE "userId" = v_user_id;
    DELETE FROM user_contact_mediums        WHERE "userId" = v_user_id;
    DELETE FROM "opposition-requests"       WHERE "userId" = v_user_id;
    DELETE FROM "portability-requests"      WHERE "userId" = v_user_id;

    -- 12. Referencias que se conservan sin el usuario
    UPDATE "felix-activation-codes" SET "usedByUserId" = NULL WHERE "usedByUserId" = v_user_id;
    UPDATE codes SET "rewardsToId" = NULL WHERE "rewardsToId" = v_user_id::text;

    -- 13. Códigos de recuperación (por rut), solo si ningún otro usuario comparte ese rut
    DELETE FROM "users-recovery-codes"
        WHERE dni = v_rut
          AND NOT EXISTS (SELECT 1 FROM users WHERE rut = v_rut AND id <> v_user_id);

    -- 14. Usuario (push-tokens, preferencias, consentimientos, co_tutors,
    --     cuentas bancarias, special-grants y welcome-emails caen en cascada)
    DELETE FROM users WHERE id = v_user_id;

    RAISE NOTICE 'OK: usuario % eliminado', v_user_id;
END $$;
