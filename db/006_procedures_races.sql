-- Triatlón Rianxo · Stored procedures do calendario (Fase 3)
-- Mesma convención: sen transaccións aquí; os erros de estado van nunha columna `status`.
--
-- Quen ve quen: as listas de "quen vai" usan Athlete_AccessLevel (004), así que os nenos
-- da escola só aparecen ás súas familias, adestradores e admins. A web pública só recibe
-- as carreiras onde vai alguén, sen nomes nin contadores.

DELIMITER $$

-- 1 se o perfil é da propia conta ou dun fillo/a que xestiona (os admins NON contan aquí)
DROP FUNCTION IF EXISTS Athlete_IsMine $$
CREATE FUNCTION Athlete_IsMine(p_athlete_id BIGINT UNSIGNED, p_user_id BIGINT UNSIGNED)
RETURNS TINYINT
READS SQL DATA
BEGIN
  RETURN EXISTS (SELECT 1 FROM athletes WHERE id = p_athlete_id AND user_id = p_user_id AND is_active = 1)
      OR EXISTS (SELECT 1 FROM athlete_guardians g JOIN athletes a ON a.id = g.athlete_id
                  WHERE g.athlete_id = p_athlete_id AND g.user_id = p_user_id AND a.is_active = 1);
END $$

-- Pode editar ou borrar a carreira: quen a creou e os admins
DROP FUNCTION IF EXISTS Race_CanEdit $$
CREATE FUNCTION Race_CanEdit(p_race_id BIGINT UNSIGNED, p_user_id BIGINT UNSIGNED)
RETURNS TINYINT
READS SQL DATA
BEGIN
  RETURN EXISTS (SELECT 1 FROM user_roles WHERE user_id = p_user_id AND role = 'admin')
      OR EXISTS (SELECT 1 FROM races WHERE id = p_race_id AND created_by = p_user_id);
END $$

-- Próximas carreiras para a zona de membros. p_only_mine = 1 → só onde vai algún perfil meu.
DROP PROCEDURE IF EXISTS Race_List $$
CREATE PROCEDURE Race_List(IN p_viewer_id BIGINT UNSIGNED, IN p_only_mine TINYINT)
BEGIN
  SELECT r.id, r.name, r.race_date, r.start_time, r.place, r.zone, r.sport, r.distances, r.official_url,
         (SELECT COUNT(*) FROM race_attendance a
           WHERE a.race_id = r.id AND a.status = 'going'
             AND Athlete_AccessLevel(a.athlete_id, p_viewer_id) <> 'none') AS going_count,
         (SELECT COUNT(*) FROM race_attendance a
           WHERE a.race_id = r.id AND a.status = 'maybe'
             AND Athlete_AccessLevel(a.athlete_id, p_viewer_id) <> 'none') AS maybe_count,
         (SELECT JSON_ARRAYAGG(JSON_OBJECT('id', x.id, 'full_name', x.full_name, 'photo_file', x.photo_file))
            FROM (SELECT t.id, t.full_name, t.photo_file
                    FROM race_attendance a JOIN athletes t ON t.id = a.athlete_id
                   WHERE a.race_id = r.id AND a.status = 'going'
                     AND Athlete_AccessLevel(t.id, p_viewer_id) <> 'none'
                   ORDER BY a.updated_at
                   LIMIT 5) AS x) AS who,
         (SELECT JSON_ARRAYAGG(JSON_OBJECT('athlete_id', a.athlete_id, 'status', a.status))
            FROM race_attendance a
           WHERE a.race_id = r.id AND Athlete_IsMine(a.athlete_id, p_viewer_id)) AS mine,
         Race_CanEdit(r.id, p_viewer_id) AS can_edit
  FROM races r
  WHERE r.race_date >= CURDATE()
    AND (p_only_mine = 0 OR EXISTS (
          SELECT 1 FROM race_attendance a WHERE a.race_id = r.id AND Athlete_IsMine(a.athlete_id, p_viewer_id)))
  ORDER BY r.race_date, r.start_time IS NULL, r.start_time, r.name;
END $$

-- Unha carreira (calquera membro pode vela). Sen filas = non existe.
DROP PROCEDURE IF EXISTS Race_Get $$
CREATE PROCEDURE Race_Get(IN p_race_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT r.id, r.name, r.race_date, r.start_time, r.place, r.zone, r.sport, r.distances, r.official_url, r.price,
         r.race_date < CURDATE() AS is_past,
         (SELECT COUNT(*) FROM race_attendance a
           WHERE a.race_id = r.id AND a.status = 'going'
             AND Athlete_AccessLevel(a.athlete_id, p_viewer_id) <> 'none') AS going_count,
         (SELECT COUNT(*) FROM race_attendance a
           WHERE a.race_id = r.id AND a.status = 'maybe'
             AND Athlete_AccessLevel(a.athlete_id, p_viewer_id) <> 'none') AS maybe_count,
         Race_CanEdit(r.id, p_viewer_id) AS can_edit,
         u.display_name AS created_by_name
  FROM races r
  LEFT JOIN users u ON u.id = r.created_by
  WHERE r.id = p_race_id;
END $$

-- Quen vai (só os perfís que pode ver quen pregunta). Primeiro os que van, inscritos antes.
DROP PROCEDURE IF EXISTS Race_GetAttendees $$
CREATE PROCEDURE Race_GetAttendees(IN p_race_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT t.id AS athlete_id, t.full_name, t.photo_file, t.is_minor,
         a.status, a.distance, a.registered,
         Athlete_IsMine(t.id, p_viewer_id) AS is_mine
  FROM race_attendance a
  JOIN athletes t ON t.id = a.athlete_id
  WHERE a.race_id = p_race_id
    AND Athlete_AccessLevel(t.id, p_viewer_id) <> 'none'
  ORDER BY a.status = 'maybe', a.registered DESC, t.full_name;
END $$

DROP PROCEDURE IF EXISTS Race_Create $$
CREATE PROCEDURE Race_Create(
  IN p_user_id      BIGINT UNSIGNED,
  IN p_name         VARCHAR(160),
  IN p_race_date    DATE,
  IN p_start_time   TIME,
  IN p_place        VARCHAR(120),
  IN p_zone         VARCHAR(10),
  IN p_sport        VARCHAR(20),
  IN p_distances    VARCHAR(200),
  IN p_official_url VARCHAR(500),
  IN p_price        VARCHAR(80)
)
BEGIN
  DECLARE v_id BIGINT UNSIGNED;
  INSERT INTO races (name, race_date, start_time, place, zone, sport, distances, official_url, price, created_by)
  VALUES (TRIM(p_name), p_race_date, p_start_time, TRIM(p_place), p_zone, p_sport,
          NULLIF(TRIM(p_distances), ''), NULLIF(TRIM(p_official_url), ''), NULLIF(TRIM(p_price), ''), p_user_id);
  SET v_id = LAST_INSERT_ID();
  SELECT v_id AS id;
END $$

DROP PROCEDURE IF EXISTS Race_Update $$
CREATE PROCEDURE Race_Update(
  IN p_race_id      BIGINT UNSIGNED,
  IN p_user_id      BIGINT UNSIGNED,
  IN p_name         VARCHAR(160),
  IN p_race_date    DATE,
  IN p_start_time   TIME,
  IN p_place        VARCHAR(120),
  IN p_zone         VARCHAR(10),
  IN p_sport        VARCHAR(20),
  IN p_distances    VARCHAR(200),
  IN p_official_url VARCHAR(500),
  IN p_price        VARCHAR(80)
)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM races WHERE id = p_race_id) THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT Race_CanEdit(p_race_id, p_user_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;

  UPDATE races
     SET name = TRIM(p_name), race_date = p_race_date, start_time = p_start_time, place = TRIM(p_place),
         zone = p_zone, sport = p_sport,
         distances = NULLIF(TRIM(p_distances), ''), official_url = NULLIF(TRIM(p_official_url), ''),
         price = NULLIF(TRIM(p_price), '')
   WHERE id = p_race_id;
  SELECT 'ok' AS status;
END $$

DROP PROCEDURE IF EXISTS Race_Delete $$
CREATE PROCEDURE Race_Delete(IN p_race_id BIGINT UNSIGNED, IN p_user_id BIGINT UNSIGNED)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM races WHERE id = p_race_id) THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF NOT Race_CanEdit(p_race_id, p_user_id) THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;
  DELETE FROM races WHERE id = p_race_id;   -- a asistencia bórrase en cascada
  SELECT 'ok' AS status;
END $$

-- Vou / Quizais / Non vou (p_status = 'none' borra a fila). Só para perfís que xestiona (ou admin).
DROP PROCEDURE IF EXISTS Race_SetAttendance $$
CREATE PROCEDURE Race_SetAttendance(
  IN p_race_id    BIGINT UNSIGNED,
  IN p_athlete_id BIGINT UNSIGNED,
  IN p_user_id    BIGINT UNSIGNED,
  IN p_status     VARCHAR(10),
  IN p_distance   VARCHAR(60),
  IN p_registered TINYINT
)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM races WHERE id = p_race_id) THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF Athlete_AccessLevel(p_athlete_id, p_user_id) <> 'manage' THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;

  IF p_status = 'none' THEN
    DELETE FROM race_attendance WHERE race_id = p_race_id AND athlete_id = p_athlete_id;
  ELSE
    INSERT INTO race_attendance (race_id, athlete_id, status, distance, registered, updated_by)
    VALUES (p_race_id, p_athlete_id, p_status, NULLIF(TRIM(p_distance), ''),
            IF(p_status = 'going', p_registered, 0), p_user_id) AS new
    ON DUPLICATE KEY UPDATE status = new.status, distance = new.distance,
                            registered = new.registered, updated_by = new.updated_by;
  END IF;
  SELECT 'ok' AS status;
END $$

-- Carreiras parecidas mentres alguén escribe unha nova: todas as palabras (ata 3) no nome,
-- en calquera orde e sen importar maiúsculas nin tiles, ou a mesma data.
DROP PROCEDURE IF EXISTS Race_FindSimilar $$
CREATE PROCEDURE Race_FindSimilar(
  IN p_w1 VARCHAR(60), IN p_w2 VARCHAR(60), IN p_w3 VARCHAR(60),
  IN p_date DATE, IN p_viewer_id BIGINT UNSIGNED
)
BEGIN
  SELECT r.id, r.name, r.race_date, r.place,
         (SELECT COUNT(*) FROM race_attendance a
           WHERE a.race_id = r.id AND a.status = 'going'
             AND Athlete_AccessLevel(a.athlete_id, p_viewer_id) <> 'none') AS going_count
  FROM races r
  WHERE r.race_date >= CURDATE()
    AND ((p_w1 IS NOT NULL
          AND r.name LIKE CONCAT('%', p_w1, '%')
          AND (p_w2 IS NULL OR r.name LIKE CONCAT('%', p_w2, '%'))
          AND (p_w3 IS NULL OR r.name LIKE CONCAT('%', p_w3, '%')))
         OR (p_date IS NOT NULL AND r.race_date = p_date))
  ORDER BY r.race_date
  LIMIT 5;
END $$

-- Carreiras dun atleta para o seu perfil: as próximas (vai ou quizais) e as feitas (foi).
-- p_viewer_athlete_id = perfil propio de quen mira, para o botón "Eu tamén vou".
DROP PROCEDURE IF EXISTS Race_ListForAthlete $$
CREATE PROCEDURE Race_ListForAthlete(
  IN p_athlete_id        BIGINT UNSIGNED,
  IN p_viewer_id         BIGINT UNSIGNED,
  IN p_viewer_athlete_id BIGINT UNSIGNED
)
BEGIN
  SELECT r.id, r.name, r.race_date, r.place, r.sport,
         a.status, a.distance, a.registered,
         r.race_date < CURDATE() AS is_past,
         (SELECT v.status FROM race_attendance v
           WHERE v.race_id = r.id AND v.athlete_id = p_viewer_athlete_id) AS viewer_status
  FROM race_attendance a
  JOIN races r ON r.id = a.race_id
  WHERE a.athlete_id = p_athlete_id
    AND Athlete_AccessLevel(p_athlete_id, p_viewer_id) <> 'none'
    AND (r.race_date >= CURDATE() OR a.status = 'going')
  ORDER BY is_past, IF(r.race_date >= CURDATE(), r.race_date, NULL), r.race_date DESC
  LIMIT 40;
END $$

-- Web pública: próximas carreiras onde vai alguén do clube. going_count só serve para filtrar:
-- a API non o envía (PublicRace en schemas.py).
DROP PROCEDURE IF EXISTS Race_PublicList $$
CREATE PROCEDURE Race_PublicList(IN p_limit INT)
BEGIN
  SELECT r.id, r.name, r.race_date, r.start_time, r.place, r.zone, r.sport, r.distances, r.official_url, r.price,
         (SELECT COUNT(*) FROM race_attendance a JOIN athletes t ON t.id = a.athlete_id
           WHERE a.race_id = r.id AND a.status = 'going' AND t.is_active = 1) AS going_count
  FROM races r
  WHERE r.race_date >= CURDATE()
  HAVING going_count > 0
  ORDER BY r.race_date, r.start_time IS NULL, r.start_time
  LIMIT p_limit;
END $$

DELIMITER ;
