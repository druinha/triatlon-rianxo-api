-- Triatlón Rianxo · Stored procedures do perfil do atleta (Fase 2)
-- Mesma convención ca 002: sen transaccións aquí, e os erros de estado van nunha columna `status`.
--
-- Quen ve que (Athlete_AccessLevel):
--   manage → o propio atleta, os seus titores e os admins: ven todo e poden editar
--   staff  → adestradores: ven todo, non editan
--   basic  → calquera outro membro, só para perfís de adultos: nome, foto e deportes
--   none   → o resto (p. ex. un atleta adulto mirando o perfil dun neno da escola)

DELIMITER $$

DROP FUNCTION IF EXISTS Athlete_AccessLevel $$
CREATE FUNCTION Athlete_AccessLevel(p_athlete_id BIGINT UNSIGNED, p_viewer_id BIGINT UNSIGNED)
RETURNS VARCHAR(10)
READS SQL DATA
BEGIN
  DECLARE v_found  TINYINT DEFAULT 1;
  DECLARE v_owner  BIGINT UNSIGNED;
  DECLARE v_minor  TINYINT;
  DECLARE v_active TINYINT;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_found = 0;

  SELECT user_id, is_minor, is_active INTO v_owner, v_minor, v_active
    FROM athletes WHERE id = p_athlete_id;
  IF v_found = 0 THEN RETURN 'none'; END IF;

  IF EXISTS (SELECT 1 FROM user_roles WHERE user_id = p_viewer_id AND role = 'admin') THEN
    RETURN 'manage';
  END IF;
  IF v_active = 0 THEN RETURN 'none'; END IF;

  IF v_owner = p_viewer_id
     OR EXISTS (SELECT 1 FROM athlete_guardians WHERE athlete_id = p_athlete_id AND user_id = p_viewer_id) THEN
    RETURN 'manage';
  END IF;
  IF EXISTS (SELECT 1 FROM user_roles WHERE user_id = p_viewer_id AND role = 'coach') THEN
    RETURN 'staff';
  END IF;
  IF v_minor = 0 THEN RETURN 'basic'; END IF;
  RETURN 'none';
END $$

-- Perfil completo ou recortado segundo quen o mira. Sen filas = non existe ou non o pode ver.
DROP PROCEDURE IF EXISTS Athlete_GetProfile $$
CREATE PROCEDURE Athlete_GetProfile(IN p_athlete_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  DECLARE v_level VARCHAR(10) DEFAULT Athlete_AccessLevel(p_athlete_id, p_viewer_id);
  DECLARE v_full  TINYINT DEFAULT 0;
  SET v_full = v_level IN ('manage', 'staff');

  SELECT a.id, a.full_name, a.is_minor, a.is_active, a.photo_file,
         IF(v_full, a.birth_date, NULL)     AS birth_date,
         IF(v_full, a.license_number, NULL) AS license_number,
         IF(v_full, a.chip_code, NULL)      AS chip_code,
         (SELECT GROUP_CONCAT(s.sport ORDER BY s.sport) FROM athlete_sports s WHERE s.athlete_id = a.id) AS sports,
         IF(v_full,
            (SELECT JSON_ARRAYAGG(u.display_name)
               FROM athlete_guardians g JOIN users u ON u.id = g.user_id
              WHERE g.athlete_id = a.id),
            NULL) AS guardians,
         v_level AS access,
         a.updated_at
  FROM athletes a
  WHERE a.id = p_athlete_id AND v_level <> 'none';
END $$

-- Directorio de atletas activos que a persoa pode ver (só datos básicos).
DROP PROCEDURE IF EXISTS Athlete_ListDirectory $$
CREATE PROCEDURE Athlete_ListDirectory(IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT a.id, a.full_name, a.is_minor, a.photo_file,
         (SELECT GROUP_CONCAT(s.sport ORDER BY s.sport) FROM athlete_sports s WHERE s.athlete_id = a.id) AS sports,
         Athlete_AccessLevel(a.id, p_viewer_id) AS access
  FROM athletes a
  WHERE a.is_active = 1
    AND Athlete_AccessLevel(a.id, p_viewer_id) <> 'none'
  ORDER BY a.full_name;
END $$

-- Garda os datos do perfil. p_sports é un array JSON de claves: ["triathlon","running"].
DROP PROCEDURE IF EXISTS Athlete_Update $$
CREATE PROCEDURE Athlete_Update(
  IN p_athlete_id BIGINT UNSIGNED,
  IN p_editor_id  BIGINT UNSIGNED,
  IN p_full_name  VARCHAR(160),
  IN p_birth_date DATE,
  IN p_license    VARCHAR(40),
  IN p_chip       VARCHAR(40),
  IN p_sports     JSON
)
proc: BEGIN
  DECLARE v_level VARCHAR(10) DEFAULT Athlete_AccessLevel(p_athlete_id, p_editor_id);

  IF v_level = 'none' THEN SELECT 'not_found' AS status; LEAVE proc; END IF;
  IF v_level <> 'manage' THEN SELECT 'forbidden' AS status; LEAVE proc; END IF;

  UPDATE athletes
     SET full_name      = TRIM(p_full_name),
         birth_date     = p_birth_date,
         license_number = NULLIF(TRIM(p_license), ''),
         chip_code      = NULLIF(UPPER(TRIM(p_chip)), '')
   WHERE id = p_athlete_id;

  DELETE FROM athlete_sports WHERE athlete_id = p_athlete_id;
  INSERT IGNORE INTO athlete_sports (athlete_id, sport)
  SELECT p_athlete_id, j.sport
    FROM JSON_TABLE(COALESCE(p_sports, JSON_ARRAY()), '$[*]' COLUMNS (sport VARCHAR(20) PATH '$')) AS j;

  SELECT 'ok' AS status;
END $$

-- Cambia (ou quita, con p_photo_file NULL) a foto. Devolve a anterior para borrala do disco.
DROP PROCEDURE IF EXISTS Athlete_SetPhoto $$
CREATE PROCEDURE Athlete_SetPhoto(
  IN p_athlete_id BIGINT UNSIGNED,
  IN p_editor_id  BIGINT UNSIGNED,
  IN p_photo_file VARCHAR(64)
)
proc: BEGIN
  DECLARE v_level VARCHAR(10) DEFAULT Athlete_AccessLevel(p_athlete_id, p_editor_id);
  DECLARE v_old   VARCHAR(64);

  IF v_level = 'none' THEN SELECT 'not_found' AS status, NULL AS old_photo_file; LEAVE proc; END IF;
  IF v_level <> 'manage' THEN SELECT 'forbidden' AS status, NULL AS old_photo_file; LEAVE proc; END IF;

  SELECT photo_file INTO v_old FROM athletes WHERE id = p_athlete_id FOR UPDATE;
  UPDATE athletes SET photo_file = p_photo_file WHERE id = p_athlete_id;

  SELECT 'ok' AS status, v_old AS old_photo_file;
END $$

-- Nome do ficheiro da foto, só se quen pregunta pode ver o perfil.
DROP PROCEDURE IF EXISTS Athlete_GetPhoto $$
CREATE PROCEDURE Athlete_GetPhoto(IN p_athlete_id BIGINT UNSIGNED, IN p_viewer_id BIGINT UNSIGNED)
BEGIN
  SELECT a.photo_file
  FROM athletes a
  WHERE a.id = p_athlete_id
    AND a.photo_file IS NOT NULL
    AND Athlete_AccessLevel(p_athlete_id, p_viewer_id) <> 'none';
END $$

DELIMITER ;
