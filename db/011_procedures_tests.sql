-- Triatlón Rianxo · Stored procedures de tests, zonas e avisos (Fase 4, parte 1)
-- Mesma convención ca sempre: sen transaccións aquí, e os erros de estado van nunha columna `status`.
--
-- Quen ve os tests dun atleta: o propio atleta, os seus titores, os adestradores e os admins
-- (Athlete_AccessLevel = manage ou staff). Os demais membros nunca os ven.
-- Quen revisa e confirma zonas: adestradores e admins.

DELIMITER $$

DROP FUNCTION IF EXISTS User_IsCoach $$
CREATE FUNCTION User_IsCoach(p_user_id BIGINT UNSIGNED)
RETURNS TINYINT
READS SQL DATA
BEGIN
  RETURN EXISTS (SELECT 1 FROM user_roles WHERE user_id = p_user_id AND role IN ('coach', 'admin'));
END $$

-- ── Avisos ──

-- Ao atleta: á súa conta (adultos) e aos seus titores (menores)
DROP PROCEDURE IF EXISTS Notification_ToAthlete $$
CREATE PROCEDURE Notification_ToAthlete(
  IN p_athlete_id BIGINT UNSIGNED, IN p_kind VARCHAR(30), IN p_ref_id BIGINT UNSIGNED, IN p_sport VARCHAR(10)
)
BEGIN
  INSERT INTO notifications (user_id, kind, athlete_id, ref_id, sport)
  SELECT u.uid, p_kind, p_athlete_id, p_ref_id, p_sport
    FROM (SELECT user_id AS uid FROM athletes WHERE id = p_athlete_id AND user_id IS NOT NULL
          UNION
          SELECT user_id FROM athlete_guardians WHERE athlete_id = p_athlete_id) u;
END $$

-- Aos adestradores (rol coach), menos a quen fixo a acción
DROP PROCEDURE IF EXISTS Notification_ToCoaches $$
CREATE PROCEDURE Notification_ToCoaches(
  IN p_kind VARCHAR(30), IN p_athlete_id BIGINT UNSIGNED, IN p_ref_id BIGINT UNSIGNED,
  IN p_sport VARCHAR(10), IN p_except_user BIGINT UNSIGNED
)
BEGIN
  INSERT INTO notifications (user_id, kind, athlete_id, ref_id, sport)
  SELECT DISTINCT r.user_id, p_kind, p_athlete_id, p_ref_id, p_sport
    FROM user_roles r JOIN users u ON u.id = r.user_id AND u.is_active = 1
   WHERE r.role = 'coach' AND r.user_id <> p_except_user;
END $$

DROP PROCEDURE IF EXISTS Notification_List $$
CREATE PROCEDURE Notification_List(IN p_user_id BIGINT UNSIGNED, IN p_limit INT)
BEGIN
  SELECT n.id, n.kind, n.athlete_id, a.full_name AS athlete_name, n.ref_id, n.sport,
         n.read_at IS NOT NULL AS is_read, n.created_at
    FROM notifications n LEFT JOIN athletes a ON a.id = n.athlete_id
   WHERE n.user_id = p_user_id
   ORDER BY n.created_at DESC, n.id DESC
   LIMIT p_limit;
END $$

DROP PROCEDURE IF EXISTS Notification_MarkAllRead $$
CREATE PROCEDURE Notification_MarkAllRead(IN p_user_id BIGINT UNSIGNED)
BEGIN
  UPDATE notifications SET read_at = UTC_TIMESTAMP() WHERE user_id = p_user_id AND read_at IS NULL;
  SELECT ROW_COUNT() AS updated;
END $$

-- ── Tests ──

-- Que pode facer o visor cos tests deste atleta. Sen filas = o atleta non existe.
DROP PROCEDURE IF EXISTS Test_Access $$
CREATE PROCEDURE Test_Access(IN p_athlete_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT a.id, a.full_name, a.is_minor, a.photo_file,
         Athlete_AccessLevel(a.id, p_viewer_id) AS access,
         User_IsCoach(p_viewer_id) AS can_review
    FROM athletes a WHERE a.id = p_athlete_id;
END $$

DROP PROCEDURE IF EXISTS Test_ListForAthlete $$
CREATE PROCEDURE Test_ListForAthlete(IN p_athlete_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT t.id, t.athlete_id, t.sport, t.kind, t.test_date, t.data, t.result_seconds, t.result_value, t.avg_hr,
         t.status, t.coach_comment, t.created_at, t.reviewed_at
    FROM athlete_tests t
   WHERE t.athlete_id = p_athlete_id
     AND Athlete_AccessLevel(p_athlete_id, p_viewer_id) IN ('manage', 'staff')
   ORDER BY t.test_date DESC, t.id DESC;
END $$

DROP PROCEDURE IF EXISTS Zones_ListForAthlete $$
CREATE PROCEDURE Zones_ListForAthlete(IN p_athlete_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT z.sport, z.confirmed_kind, z.confirmed, z.confirmed_at, z.provisional_kind, z.provisional,
         z.provisional_test_id
    FROM athlete_zones z
   WHERE z.athlete_id = p_athlete_id
     AND Athlete_AccessLevel(p_athlete_id, p_viewer_id) IN ('manage', 'staff')
   ORDER BY FIELD(z.sport, 'swim', 'bike', 'run');
END $$

-- Novo test. As zonas provisionais (se as hai) quedan á espera do adestrador.
DROP PROCEDURE IF EXISTS Test_Create $$
CREATE PROCEDURE Test_Create(
  IN p_athlete_id     BIGINT UNSIGNED,
  IN p_editor_id      BIGINT UNSIGNED,
  IN p_sport          VARCHAR(10),
  IN p_kind           VARCHAR(20),
  IN p_test_date      DATE,
  IN p_data           JSON,
  IN p_result_seconds INT UNSIGNED,
  IN p_result_value   SMALLINT UNSIGNED,
  IN p_avg_hr         SMALLINT UNSIGNED,
  IN p_zones          JSON
)
proc: BEGIN
  DECLARE v_id BIGINT UNSIGNED;
  IF NOT EXISTS (SELECT 1 FROM athletes WHERE id = p_athlete_id) THEN
    SELECT 'not_found' AS status, NULL AS id; LEAVE proc;
  END IF;
  IF Athlete_AccessLevel(p_athlete_id, p_editor_id) NOT IN ('manage', 'staff') THEN
    SELECT 'forbidden' AS status, NULL AS id; LEAVE proc;
  END IF;

  INSERT INTO athlete_tests (athlete_id, sport, kind, test_date, data, result_seconds, result_value, avg_hr, created_by)
  VALUES (p_athlete_id, p_sport, p_kind, p_test_date, p_data, p_result_seconds, p_result_value, p_avg_hr, p_editor_id);
  SET v_id = LAST_INSERT_ID();

  IF p_zones IS NOT NULL THEN
    INSERT INTO athlete_zones (athlete_id, sport, provisional_kind, provisional, provisional_test_id)
    VALUES (p_athlete_id, p_sport, p_kind, p_zones, v_id)
    ON DUPLICATE KEY UPDATE provisional_kind = VALUES(provisional_kind), provisional = VALUES(provisional),
                            provisional_test_id = VALUES(provisional_test_id);
  END IF;

  -- Se o mete o propio adestrador non fai falta avisalo
  IF NOT User_IsCoach(p_editor_id) THEN
    CALL Notification_ToCoaches('test_submitted', p_athlete_id, v_id, p_sport, p_editor_id);
  END IF;
  SELECT 'ok' AS status, v_id AS id;
END $$

-- Detalle dun test co anterior do mesmo tipo e as zonas actuais dese deporte
DROP PROCEDURE IF EXISTS Test_Get $$
CREATE PROCEDURE Test_Get(IN p_test_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT t.id, t.athlete_id, a.full_name AS athlete_name, a.is_minor, a.photo_file,
         t.sport, t.kind, t.test_date, t.data, t.result_seconds, t.result_value, t.avg_hr,
         t.status, t.coach_comment, t.created_at, t.reviewed_at,
         ru.display_name AS reviewed_by_name,
         User_IsCoach(p_viewer_id) AS can_review,
         (Athlete_AccessLevel(t.athlete_id, p_viewer_id) = 'manage' AND t.status = 'submitted')
           OR User_IsCoach(p_viewer_id) AS can_delete,
         p.id AS prev_id, p.test_date AS prev_date, p.data AS prev_data, p.result_seconds AS prev_result_seconds,
         p.result_value AS prev_result_value, p.avg_hr AS prev_avg_hr,
         z.confirmed_kind, z.confirmed, z.confirmed_at, z.provisional_kind, z.provisional, z.provisional_test_id
    FROM athlete_tests t
    JOIN athletes a ON a.id = t.athlete_id
    LEFT JOIN users ru ON ru.id = t.reviewed_by
    LEFT JOIN athlete_tests p ON p.id = (
         SELECT x.id FROM athlete_tests x
          WHERE x.athlete_id = t.athlete_id AND x.kind = t.kind
            AND (x.test_date < t.test_date OR (x.test_date = t.test_date AND x.id < t.id))
          ORDER BY x.test_date DESC, x.id DESC LIMIT 1)
    LEFT JOIN athlete_zones z ON z.athlete_id = t.athlete_id AND z.sport = t.sport
   WHERE t.id = p_test_id
     AND Athlete_AccessLevel(t.athlete_id, p_viewer_id) IN ('manage', 'staff');
END $$

-- Bandexa do adestrador
DROP PROCEDURE IF EXISTS Test_Inbox $$
CREATE PROCEDURE Test_Inbox(IN p_viewer_id BIGINT UNSIGNED, IN p_status VARCHAR(10), IN p_limit INT)
BEGIN
  SELECT t.id, t.athlete_id, a.full_name AS athlete_name, a.is_minor, a.photo_file,
         t.sport, t.kind, t.test_date, t.result_seconds, t.result_value, t.avg_hr, t.status, t.created_at
    FROM athlete_tests t JOIN athletes a ON a.id = t.athlete_id AND a.is_active = 1
   WHERE User_IsCoach(p_viewer_id) AND t.status = p_status
   -- Pendentes: o máis antigo primeiro. Revisados: o último revisado primeiro.
   ORDER BY IF(p_status = 'submitted', t.created_at, NULL) ASC, IF(p_status = 'submitted', t.id, NULL) ASC,
            t.reviewed_at DESC, t.id DESC
   LIMIT p_limit;
END $$

-- Revisar: comentario e, se se pasan, zonas confirmadas. p_zones NULL = manter as anteriores.
DROP PROCEDURE IF EXISTS Test_Review $$
CREATE PROCEDURE Test_Review(
  IN p_test_id   BIGINT UNSIGNED,
  IN p_viewer_id BIGINT UNSIGNED,
  IN p_comment   VARCHAR(1000),
  IN p_zones     JSON
)
proc: BEGIN
  DECLARE v_athlete BIGINT UNSIGNED;
  DECLARE v_sport   VARCHAR(10);
  DECLARE v_kind    VARCHAR(20);
  DECLARE v_status  VARCHAR(10);
  DECLARE v_found   TINYINT DEFAULT 1;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_found = 0;

  SELECT athlete_id, sport, kind, status INTO v_athlete, v_sport, v_kind, v_status
    FROM athlete_tests WHERE id = p_test_id;
  IF v_found = 0 THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;

  UPDATE athlete_tests
     SET status = 'reviewed', coach_comment = NULLIF(TRIM(p_comment), ''),
         reviewed_by = p_viewer_id, reviewed_at = UTC_TIMESTAMP()
   WHERE id = p_test_id;

  IF p_zones IS NOT NULL THEN
    INSERT INTO athlete_zones (athlete_id, sport, confirmed_kind, confirmed, confirmed_by, confirmed_at)
    VALUES (v_athlete, v_sport, v_kind, p_zones, p_viewer_id, UTC_TIMESTAMP())
    ON DUPLICATE KEY UPDATE confirmed_kind = VALUES(confirmed_kind), confirmed = VALUES(confirmed),
                            confirmed_by = VALUES(confirmed_by), confirmed_at = VALUES(confirmed_at);
  END IF;
  -- Xa está decidido: as provisionais deste test deixan de estar pendentes
  UPDATE athlete_zones SET provisional = NULL, provisional_kind = NULL, provisional_test_id = NULL
   WHERE athlete_id = v_athlete AND sport = v_sport AND provisional_test_id = p_test_id;

  -- Avísase só a primeira vez (volver gardar a revisión non repite o aviso)
  IF v_status = 'submitted' THEN
    CALL Notification_ToAthlete(v_athlete, 'test_reviewed', p_test_id, v_sport);
  END IF;
  SELECT 'ok' AS status;
END $$

-- O adestrador cambia as zonas a man, sen test
DROP PROCEDURE IF EXISTS Zones_Set $$
CREATE PROCEDURE Zones_Set(
  IN p_athlete_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED,
  IN p_sport VARCHAR(10), IN p_kind VARCHAR(20), IN p_zones JSON
)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM athletes WHERE id = p_athlete_id) THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;
  INSERT INTO athlete_zones (athlete_id, sport, confirmed_kind, confirmed, confirmed_by, confirmed_at)
  VALUES (p_athlete_id, p_sport, p_kind, p_zones, p_viewer_id, UTC_TIMESTAMP())
  ON DUPLICATE KEY UPDATE confirmed_kind = VALUES(confirmed_kind), confirmed = VALUES(confirmed),
                          confirmed_by = VALUES(confirmed_by), confirmed_at = VALUES(confirmed_at);
  SELECT 'ok' AS status;
END $$

-- Borrar: o atleta mentres non estea revisado; o adestrador sempre
DROP PROCEDURE IF EXISTS Test_Delete $$
CREATE PROCEDURE Test_Delete(IN p_test_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
proc: BEGIN
  DECLARE v_athlete BIGINT UNSIGNED;
  DECLARE v_status  VARCHAR(10);
  DECLARE v_found   TINYINT DEFAULT 1;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_found = 0;

  SELECT athlete_id, status INTO v_athlete, v_status FROM athlete_tests WHERE id = p_test_id;
  IF v_found = 0 THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT (User_IsCoach(p_viewer_id)
          OR (Athlete_AccessLevel(v_athlete, p_viewer_id) = 'manage' AND v_status = 'submitted')) THEN
    SELECT 'forbidden' AS status; LEAVE proc;
  END IF;
  UPDATE athlete_zones SET provisional = NULL, provisional_kind = NULL, provisional_test_id = NULL
   WHERE provisional_test_id = p_test_id;
  DELETE FROM notifications WHERE ref_id = p_test_id AND kind IN ('test_submitted', 'test_reviewed');
  DELETE FROM athlete_tests WHERE id = p_test_id;
  SELECT 'ok' AS status;
END $$

-- Atletas aos que lles toca repetir: o último test dese deporte ten máis de p_days días.
-- Natación e carreira tamén se nunca o fixeron; a bici só se xa a probaron algunha vez.
DROP PROCEDURE IF EXISTS Test_ListDue $$
CREATE PROCEDURE Test_ListDue(IN p_viewer_id BIGINT UNSIGNED, IN p_days INT)
BEGIN
  SELECT a.id AS athlete_id, a.full_name AS athlete_name, a.is_minor, a.photo_file, s.sport,
         MAX(t.test_date) AS last_date,
         (SELECT MAX(n.created_at) FROM notifications n
           WHERE n.kind = 'test_reminder' AND n.athlete_id = a.id AND n.sport = s.sport) AS reminded_at
    FROM athletes a
    CROSS JOIN (SELECT 'swim' AS sport UNION ALL SELECT 'bike' UNION ALL SELECT 'run') s
    LEFT JOIN athlete_tests t ON t.athlete_id = a.id AND t.sport = s.sport
   WHERE a.is_active = 1 AND User_IsCoach(p_viewer_id)
   GROUP BY a.id, a.full_name, a.is_minor, a.photo_file, s.sport
  HAVING (last_date IS NULL AND s.sport <> 'bike')
      OR last_date < UTC_DATE() - INTERVAL p_days DAY
   ORDER BY last_date IS NOT NULL, last_date, a.full_name, FIELD(s.sport, 'swim', 'bike', 'run');
END $$

-- Lembrar a un atleta que repita un test. Non se repite o aviso antes de 3 días.
DROP PROCEDURE IF EXISTS Test_Remind $$
CREATE PROCEDURE Test_Remind(IN p_viewer_id BIGINT UNSIGNED, IN p_athlete_id BIGINT UNSIGNED, IN p_sport VARCHAR(10))
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM athletes WHERE id = p_athlete_id) THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;
  IF EXISTS (SELECT 1 FROM notifications
              WHERE kind = 'test_reminder' AND athlete_id = p_athlete_id AND sport = p_sport
                AND created_at > UTC_TIMESTAMP() - INTERVAL 3 DAY) THEN
    SELECT 'ok' AS status; LEAVE proc;
  END IF;
  CALL Notification_ToAthlete(p_athlete_id, 'test_reminder', NULL, p_sport);
  SELECT 'ok' AS status;
END $$

DELIMITER ;
