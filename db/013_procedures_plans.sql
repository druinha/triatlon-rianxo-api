-- Triatlón Rianxo · Stored procedures dos plans de adestramento (Fase 4, parte 2)
-- Sen transaccións aquí; os erros de estado van nunha columna `status`.
-- Fai falta o 011 (User_IsCoach, Notification_ToAthlete).
--
-- Quen fai que:
--   adestradores e admins → crean grupos e plans, ven borradores e o seguimento
--   atleta / titores      → ven o plan publicado que lles toca e marcan o feito

DELIMITER $$

-- ── Grupos ──

-- Está o atleta no grupo? (apuntado á carreira do grupo, ou engadido a man; e non excluído)
DROP FUNCTION IF EXISTS Group_HasAthlete $$
CREATE FUNCTION Group_HasAthlete(p_group_id BIGINT UNSIGNED, p_athlete_id BIGINT UNSIGNED)
RETURNS TINYINT
READS SQL DATA
BEGIN
  IF EXISTS (SELECT 1 FROM training_group_members
              WHERE group_id = p_group_id AND athlete_id = p_athlete_id AND mode = 'exclude') THEN
    RETURN 0;
  END IF;
  RETURN EXISTS (SELECT 1 FROM training_group_members
                  WHERE group_id = p_group_id AND athlete_id = p_athlete_id AND mode = 'add')
      OR EXISTS (SELECT 1 FROM training_groups g
                   JOIN race_attendance ra ON ra.race_id = g.race_id AND ra.status = 'going'
                  WHERE g.id = p_group_id AND ra.athlete_id = p_athlete_id);
END $$

DROP PROCEDURE IF EXISTS Group_List $$
CREATE PROCEDURE Group_List(IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT g.id, g.name, g.race_id, r.name AS race_name, r.race_date,
         (SELECT COUNT(*) FROM athletes a WHERE a.is_active = 1 AND Group_HasAthlete(g.id, a.id)) AS member_count
    FROM training_groups g LEFT JOIN races r ON r.id = g.race_id
   WHERE User_IsCoach(p_viewer_id)
   ORDER BY r.race_date IS NULL, r.race_date, g.name;
END $$

DROP PROCEDURE IF EXISTS Group_Create $$
CREATE PROCEDURE Group_Create(IN p_viewer_id BIGINT UNSIGNED, IN p_name VARCHAR(120), IN p_race_id BIGINT UNSIGNED)
proc: BEGIN
  DECLARE v_id BIGINT UNSIGNED DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND BEGIN END;
  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status, NULL AS id; LEAVE proc; END IF;
  IF p_race_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM races WHERE id = p_race_id) THEN
    SELECT 'not_found' AS status, NULL AS id; LEAVE proc;
  END IF;
  -- Un só grupo por carreira: se xa existe, devólvese ese
  IF p_race_id IS NOT NULL THEN
    SELECT id INTO v_id FROM training_groups WHERE race_id = p_race_id ORDER BY id LIMIT 1;
    IF v_id IS NOT NULL THEN SELECT 'ok' AS status, v_id AS id; LEAVE proc; END IF;
  END IF;
  INSERT INTO training_groups (name, race_id, created_by)
  VALUES (COALESCE(NULLIF(TRIM(p_name), ''), (SELECT name FROM races WHERE id = p_race_id)), p_race_id, p_viewer_id);
  SET v_id = LAST_INSERT_ID();
  SELECT 'ok' AS status, v_id AS id;
END $$

DROP PROCEDURE IF EXISTS Group_Rename $$
CREATE PROCEDURE Group_Rename(IN p_group_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED, IN p_name VARCHAR(120))
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM training_groups WHERE id = p_group_id) THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;
  UPDATE training_groups SET name = TRIM(p_name) WHERE id = p_group_id;
  SELECT 'ok' AS status;
END $$

DROP PROCEDURE IF EXISTS Group_Delete $$
CREATE PROCEDURE Group_Delete(IN p_group_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM training_groups WHERE id = p_group_id) THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;
  DELETE FROM training_groups WHERE id = p_group_id;   -- os seus plans bórranse en cascada
  SELECT 'ok' AS status;
END $$

-- Membros e candidatos dun grupo: todos os atletas activos con
--   in_group (está), from_race (vai á carreira), mode (add / exclude / NULL)
DROP PROCEDURE IF EXISTS Group_Members $$
CREATE PROCEDURE Group_Members(IN p_group_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT a.id AS athlete_id, a.full_name, a.is_minor, a.photo_file,
         Group_HasAthlete(g.id, a.id) AS in_group,
         EXISTS (SELECT 1 FROM race_attendance ra
                  WHERE ra.race_id = g.race_id AND ra.athlete_id = a.id AND ra.status = 'going') AS from_race,
         m.mode
    FROM training_groups g
    JOIN athletes a ON a.is_active = 1
    LEFT JOIN training_group_members m ON m.group_id = g.id AND m.athlete_id = a.id
   WHERE g.id = p_group_id AND User_IsCoach(p_viewer_id)
   ORDER BY in_group DESC, a.is_minor, a.full_name;
END $$

-- p_mode: 'add' (engadir), 'exclude' (sacar a alguén que vai á carreira) ou 'none' (volver ao automático)
DROP PROCEDURE IF EXISTS Group_SetMember $$
CREATE PROCEDURE Group_SetMember(
  IN p_group_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED, IN p_athlete_id BIGINT UNSIGNED, IN p_mode VARCHAR(10)
)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM training_groups WHERE id = p_group_id)
     OR NOT EXISTS (SELECT 1 FROM athletes WHERE id = p_athlete_id) THEN
    SELECT 'not_found' AS status; LEAVE proc;
  END IF;
  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;
  IF p_mode = 'none' THEN
    DELETE FROM training_group_members WHERE group_id = p_group_id AND athlete_id = p_athlete_id;
  ELSE
    INSERT INTO training_group_members (group_id, athlete_id, mode) VALUES (p_group_id, p_athlete_id, p_mode)
    ON DUPLICATE KEY UPDATE mode = VALUES(mode);
  END IF;
  SELECT 'ok' AS status;
END $$

-- ── Plans ──

-- O plan publicado que lle toca a un atleta nunha semana (individual > grupo > xeral). NULL = ningún.
DROP FUNCTION IF EXISTS Plan_ResolveId $$
CREATE FUNCTION Plan_ResolveId(p_athlete_id BIGINT UNSIGNED, p_week DATE)
RETURNS BIGINT UNSIGNED
READS SQL DATA
BEGIN
  DECLARE v_id BIGINT UNSIGNED DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND BEGIN END;
  SELECT id INTO v_id FROM training_plans
   WHERE week_start = p_week AND status = 'published' AND scope = 'athlete' AND athlete_id = p_athlete_id
   LIMIT 1;
  IF v_id IS NULL THEN
    SELECT id INTO v_id FROM training_plans
     WHERE week_start = p_week AND status = 'published' AND scope = 'group' AND Group_HasAthlete(group_id, p_athlete_id)
     ORDER BY id LIMIT 1;
  END IF;
  IF v_id IS NULL THEN
    SELECT id INTO v_id FROM training_plans
     WHERE week_start = p_week AND status = 'published' AND scope = 'general'
     LIMIT 1;
  END IF;
  RETURN v_id;
END $$

-- Plans dunha semana (adestrador): para ver dunha ollada que hai feito
DROP PROCEDURE IF EXISTS Plan_ListWeek $$
CREATE PROCEDURE Plan_ListWeek(IN p_viewer_id BIGINT UNSIGNED, IN p_week DATE)
BEGIN
  SELECT p.id, p.week_start, p.scope, p.group_id, g.name AS group_name, p.athlete_id, a.full_name AS athlete_name,
         p.status, p.published_at, p.updated_at,
         (SELECT COUNT(*) FROM plan_sessions s WHERE s.plan_id = p.id) AS session_count
    FROM training_plans p
    LEFT JOIN training_groups g ON g.id = p.group_id
    LEFT JOIN athletes a ON a.id = p.athlete_id
   WHERE p.week_start = p_week AND User_IsCoach(p_viewer_id)
   ORDER BY FIELD(p.scope, 'general', 'group', 'athlete'), g.name, a.full_name;
END $$

-- Un plan concreto para o editor (adestrador). Sen filas = aínda non existe.
DROP PROCEDURE IF EXISTS Plan_GetForEditor $$
CREATE PROCEDURE Plan_GetForEditor(
  IN p_viewer_id BIGINT UNSIGNED, IN p_week DATE, IN p_scope VARCHAR(10),
  IN p_group_id BIGINT UNSIGNED, IN p_athlete_id BIGINT UNSIGNED
)
BEGIN
  SELECT p.id, p.week_start, p.scope, p.group_id, p.athlete_id, p.status, p.note, p.published_at, p.updated_at
    FROM training_plans p
   WHERE User_IsCoach(p_viewer_id) AND p.week_start = p_week
     AND p.scope_key = CONCAT(p_scope, ':', COALESCE(p_group_id, p_athlete_id, 0));
END $$

DROP PROCEDURE IF EXISTS Plan_Sessions $$
CREATE PROCEDURE Plan_Sessions(IN p_plan_id BIGINT UNSIGNED)
BEGIN
  SELECT id, day, position, sport, title, duration_min, content
    FROM plan_sessions WHERE plan_id = p_plan_id
   ORDER BY day, position, id;
END $$

-- Gardar un plan enteiro (crea ou actualiza) coas súas sesións en JSON:
--   [{"id": 12|null, "day": 0-6, "position": n, "sport": "...", "title": "...", "duration_min": n, "content": "..."}]
-- As sesións que traen id deste plan actualízanse (e conservan o "feito" dos atletas);
-- as que non, créanse; as que xa non veñen, bórranse.
DROP PROCEDURE IF EXISTS Plan_Save $$
CREATE PROCEDURE Plan_Save(
  IN p_viewer_id  BIGINT UNSIGNED,
  IN p_week       DATE,
  IN p_scope      VARCHAR(10),
  IN p_group_id   BIGINT UNSIGNED,
  IN p_athlete_id BIGINT UNSIGNED,
  IN p_status     VARCHAR(10),
  IN p_note       VARCHAR(500),
  IN p_sessions   JSON
)
proc: BEGIN
  DECLARE v_id BIGINT UNSIGNED DEFAULT NULL;
  DECLARE v_was VARCHAR(10) DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND BEGIN END;

  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status, NULL AS id; LEAVE proc; END IF;
  IF (p_scope = 'group' AND NOT EXISTS (SELECT 1 FROM training_groups WHERE id = p_group_id))
     OR (p_scope = 'athlete' AND NOT EXISTS (SELECT 1 FROM athletes WHERE id = p_athlete_id)) THEN
    SELECT 'not_found' AS status, NULL AS id; LEAVE proc;
  END IF;

  SELECT id, status INTO v_id, v_was FROM training_plans
   WHERE week_start = p_week AND scope_key = CONCAT(p_scope, ':', COALESCE(p_group_id, p_athlete_id, 0));

  IF v_id IS NULL THEN
    INSERT INTO training_plans (week_start, scope, group_id, athlete_id, scope_key, status, note, created_by, updated_by, published_at)
    VALUES (p_week, p_scope, IF(p_scope = 'group', p_group_id, NULL), IF(p_scope = 'athlete', p_athlete_id, NULL),
            CONCAT(p_scope, ':', COALESCE(p_group_id, p_athlete_id, 0)),
            p_status, NULLIF(TRIM(p_note), ''), p_viewer_id, p_viewer_id,
            IF(p_status = 'published', UTC_TIMESTAMP(), NULL));
    SET v_id = LAST_INSERT_ID();
  ELSE
    UPDATE training_plans
       SET status = p_status, note = NULLIF(TRIM(p_note), ''), updated_by = p_viewer_id,
           published_at = IF(p_status = 'published', COALESCE(published_at, UTC_TIMESTAMP()), NULL)
     WHERE id = v_id;
  END IF;

  DELETE s FROM plan_sessions s
   WHERE s.plan_id = v_id
     AND s.id NOT IN (SELECT j.id FROM JSON_TABLE(p_sessions, '$[*]' COLUMNS (id BIGINT UNSIGNED PATH '$.id')) j
                       WHERE j.id IS NOT NULL);

  UPDATE plan_sessions s
    JOIN JSON_TABLE(p_sessions, '$[*]' COLUMNS (
           id BIGINT UNSIGNED PATH '$.id', day TINYINT UNSIGNED PATH '$.day', position TINYINT UNSIGNED PATH '$.position',
           sport VARCHAR(10) PATH '$.sport', title VARCHAR(120) CHARACTER SET utf8mb4 PATH '$.title',
           duration_min SMALLINT UNSIGNED PATH '$.duration_min', content TEXT CHARACTER SET utf8mb4 PATH '$.content')) j ON j.id = s.id
     SET s.day = j.day, s.position = j.position, s.sport = j.sport, s.title = NULLIF(j.title, ''),
         s.duration_min = j.duration_min, s.content = NULLIF(j.content, '')
   WHERE s.plan_id = v_id;

  INSERT INTO plan_sessions (plan_id, day, position, sport, title, duration_min, content)
  SELECT v_id, j.day, j.position, j.sport, NULLIF(j.title, ''), j.duration_min, NULLIF(j.content, '')
    FROM JSON_TABLE(p_sessions, '$[*]' COLUMNS (
           id BIGINT UNSIGNED PATH '$.id', day TINYINT UNSIGNED PATH '$.day', position TINYINT UNSIGNED PATH '$.position',
           sport VARCHAR(10) PATH '$.sport', title VARCHAR(120) CHARACTER SET utf8mb4 PATH '$.title',
           duration_min SMALLINT UNSIGNED PATH '$.duration_min', content TEXT CHARACTER SET utf8mb4 PATH '$.content')) j
   WHERE j.id IS NULL OR NOT EXISTS (SELECT 1 FROM plan_sessions x WHERE x.id = j.id AND x.plan_id = v_id);

  -- Avísase aos atletas só cando pasa a publicado por primeira vez
  IF p_status = 'published' AND COALESCE(v_was, '') <> 'published' THEN
    INSERT INTO notifications (user_id, kind, athlete_id, ref_id)
    SELECT u.uid, 'plan_published', u.aid, v_id
      FROM (SELECT a.user_id AS uid, a.id AS aid FROM athletes a
             WHERE a.is_active = 1 AND a.user_id IS NOT NULL AND Plan_ResolveId(a.id, p_week) = v_id
            UNION
            SELECT gd.user_id, a.id FROM athletes a JOIN athlete_guardians gd ON gd.athlete_id = a.id
             WHERE a.is_active = 1 AND Plan_ResolveId(a.id, p_week) = v_id) u;
  END IF;

  SELECT 'ok' AS status, v_id AS id;
END $$

DROP PROCEDURE IF EXISTS Plan_Delete $$
CREATE PROCEDURE Plan_Delete(IN p_plan_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM training_plans WHERE id = p_plan_id) THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT User_IsCoach(p_viewer_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;
  DELETE FROM notifications WHERE kind = 'plan_published' AND ref_id = p_plan_id;
  DELETE FROM training_plans WHERE id = p_plan_id;
  SELECT 'ok' AS status;
END $$

-- A semana dun atleta: o plan que lle toca e as carreiras ás que vai esa semana.
-- Sen filas = non ten acceso. plan_id NULL = aínda non hai plan publicado.
DROP PROCEDURE IF EXISTS Plan_ForAthlete $$
CREATE PROCEDURE Plan_ForAthlete(IN p_athlete_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED, IN p_week DATE)
BEGIN
  DECLARE v_plan BIGINT UNSIGNED DEFAULT Plan_ResolveId(p_athlete_id, p_week);
  SELECT a.id AS athlete_id, a.full_name, a.is_minor, a.photo_file,
         Athlete_AccessLevel(a.id, p_viewer_id) = 'manage' AS can_mark,
         p.id AS plan_id, p.scope, g.name AS group_name, p.note, p.published_at,
         (SELECT JSON_ARRAYAGG(JSON_OBJECT('id', r.id, 'name', r.name, 'race_date', r.race_date, 'place', r.place))
            FROM race_attendance ra JOIN races r ON r.id = ra.race_id
           WHERE ra.athlete_id = a.id AND ra.status = 'going'
             AND r.race_date BETWEEN p_week AND p_week + INTERVAL 6 DAY) AS races
    FROM athletes a
    LEFT JOIN training_plans p ON p.id = v_plan
    LEFT JOIN training_groups g ON g.id = p.group_id
   WHERE a.id = p_athlete_id AND Athlete_AccessLevel(a.id, p_viewer_id) IN ('manage', 'staff');
END $$

DROP PROCEDURE IF EXISTS Plan_SessionsForAthlete $$
CREATE PROCEDURE Plan_SessionsForAthlete(IN p_plan_id BIGINT UNSIGNED, IN p_athlete_id BIGINT UNSIGNED)
BEGIN
  SELECT s.id, s.day, s.position, s.sport, s.title, s.duration_min, s.content,
         d.session_id IS NOT NULL AS done, d.rpe, d.comment, d.done_at
    FROM plan_sessions s
    LEFT JOIN session_done d ON d.session_id = s.id AND d.athlete_id = p_athlete_id
   WHERE s.plan_id = p_plan_id
   ORDER BY s.day, s.position, s.id;
END $$

-- Marcar (ou desmarcar) unha sesión como feita. Só o propio atleta ou os seus titores,
-- e só nas sesións do plan que lle toca.
DROP PROCEDURE IF EXISTS Session_SetDone $$
CREATE PROCEDURE Session_SetDone(
  IN p_session_id BIGINT UNSIGNED, IN p_athlete_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED,
  IN p_done TINYINT, IN p_rpe TINYINT UNSIGNED, IN p_comment VARCHAR(500)
)
proc: BEGIN
  DECLARE v_week DATE;
  DECLARE v_plan BIGINT UNSIGNED;
  DECLARE v_found TINYINT DEFAULT 1;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_found = 0;

  SELECT p.week_start, p.id INTO v_week, v_plan
    FROM plan_sessions s JOIN training_plans p ON p.id = s.plan_id WHERE s.id = p_session_id;
  IF v_found = 0 THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF Athlete_AccessLevel(p_athlete_id, p_viewer_id) <> 'manage'
     OR COALESCE(Plan_ResolveId(p_athlete_id, v_week), 0) <> v_plan THEN
    SELECT 'forbidden' AS status; LEAVE proc;
  END IF;

  IF p_done THEN
    INSERT INTO session_done (session_id, athlete_id, rpe, comment, updated_by)
    VALUES (p_session_id, p_athlete_id, p_rpe, NULLIF(TRIM(p_comment), ''), p_viewer_id)
    ON DUPLICATE KEY UPDATE rpe = VALUES(rpe), comment = VALUES(comment), updated_by = VALUES(updated_by);
  ELSE
    DELETE FROM session_done WHERE session_id = p_session_id AND athlete_id = p_athlete_id;
  END IF;
  SELECT 'ok' AS status;
END $$

-- Seguimento (adestrador): a quen lle toca este plan e que sesións fixo cada un
DROP PROCEDURE IF EXISTS Plan_Progress $$
CREATE PROCEDURE Plan_Progress(IN p_plan_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  DECLARE v_week DATE DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND BEGIN END;
  SELECT week_start INTO v_week FROM training_plans WHERE id = p_plan_id;
  SELECT a.id AS athlete_id, a.full_name, a.is_minor, a.photo_file,
         (SELECT JSON_ARRAYAGG(JSON_OBJECT('session_id', d.session_id, 'rpe', d.rpe, 'comment', d.comment))
            FROM session_done d JOIN plan_sessions s ON s.id = d.session_id AND s.plan_id = p_plan_id
           WHERE d.athlete_id = a.id) AS done
    FROM athletes a
   WHERE a.is_active = 1 AND User_IsCoach(p_viewer_id) AND v_week IS NOT NULL
     AND Plan_ResolveId(a.id, v_week) = p_plan_id
   ORDER BY a.is_minor, a.full_name;
END $$

DELIMITER ;
