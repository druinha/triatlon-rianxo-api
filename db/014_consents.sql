-- Triatlón Rianxo · Consentimentos por atleta (RGPD arts. 7 e 9.2.a, LOPDGDD art. 7)
--   training → datos de adestramento e fisiolóxicos (tests, zonas, sesións feitas). Consentimento explícito.
--   img_*    → uso da imaxe por canle: web, redes sociais, WhatsApp do clube, impresos.
--   NULL = sen responder. Só o propio atleta adulto ou un titor pode cambialos.
--   Cada cambio queda en consent_log (quen, cando, versión do texto, IP e navegador).
-- Mesma convención ca o resto: sen transaccións aquí, estado nunha columna `status`.

CREATE TABLE IF NOT EXISTS athlete_consents (
  athlete_id    BIGINT UNSIGNED NOT NULL,
  training      TINYINT(1)      NULL,
  img_web       TINYINT(1)      NULL,
  img_social    TINYINT(1)      NULL,
  img_whatsapp  TINYINT(1)      NULL,
  img_print     TINYINT(1)      NULL,
  version       VARCHAR(20)     NOT NULL,
  updated_by    BIGINT UNSIGNED NULL,
  updated_at    DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (athlete_id),
  CONSTRAINT fk_consent_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id) ON DELETE CASCADE,
  CONSTRAINT fk_consent_user    FOREIGN KEY (updated_by) REFERENCES users(id)    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS consent_log (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  athlete_id    BIGINT UNSIGNED NOT NULL,
  user_id       BIGINT UNSIGNED NULL,
  training      TINYINT(1)      NULL,
  img_web       TINYINT(1)      NULL,
  img_social    TINYINT(1)      NULL,
  img_whatsapp  TINYINT(1)      NULL,
  img_print     TINYINT(1)      NULL,
  version       VARCHAR(20)     NOT NULL,
  ip            VARCHAR(45)     NULL,
  user_agent    VARCHAR(255)    NULL,
  created_at    DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (id),
  KEY ix_clog_athlete (athlete_id, created_at),
  CONSTRAINT fk_clog_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id) ON DELETE CASCADE,
  CONSTRAINT fk_clog_user    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DELIMITER $$

-- 1 se o atleta deu o consentimento de adestramento
DROP FUNCTION IF EXISTS Consent_HasTraining $$
CREATE FUNCTION Consent_HasTraining(p_athlete_id BIGINT UNSIGNED)
RETURNS TINYINT
READS SQL DATA
BEGIN
  RETURN COALESCE((SELECT training FROM athlete_consents WHERE athlete_id = p_athlete_id), 0) = 1;
END $$

-- Atletas que xestiona esta conta (o seu e os dos fillos) cos consentimentos
DROP PROCEDURE IF EXISTS Consent_ListMine $$
CREATE PROCEDURE Consent_ListMine(IN p_user_id BIGINT UNSIGNED)
BEGIN
  SELECT a.id AS athlete_id, a.full_name, a.is_minor = 1 AS is_minor, a.photo_file,
         c.training, c.img_web, c.img_social, c.img_whatsapp, c.img_print, c.version, c.updated_at
    FROM athletes a
    LEFT JOIN athlete_consents c ON c.athlete_id = a.id
   WHERE a.is_active = 1
     AND (a.user_id = p_user_id
          OR a.id IN (SELECT g.athlete_id FROM athlete_guardians g WHERE g.user_id = p_user_id))
   ORDER BY a.is_minor, a.full_name;
END $$

-- Garda os consentimentos. Só o propio atleta ou un titor (nin admins nin adestradores).
-- Se retira o de adestramento, bórranse os tests, as zonas e as sesións marcadas.
DROP PROCEDURE IF EXISTS Consent_Set $$
CREATE PROCEDURE Consent_Set(
  IN p_athlete_id BIGINT UNSIGNED,
  IN p_user_id    BIGINT UNSIGNED,
  IN p_training   TINYINT,
  IN p_web        TINYINT,
  IN p_social     TINYINT,
  IN p_whatsapp   TINYINT,
  IN p_print      TINYINT,
  IN p_version    VARCHAR(20),
  IN p_ip         VARCHAR(45),
  IN p_ua         VARCHAR(255)
)
proc: BEGIN
  DECLARE v_prev TINYINT DEFAULT NULL;

  IF NOT EXISTS (
    SELECT 1 FROM athletes a
     WHERE a.id = p_athlete_id AND a.is_active = 1
       AND (a.user_id = p_user_id
            OR EXISTS (SELECT 1 FROM athlete_guardians g WHERE g.athlete_id = a.id AND g.user_id = p_user_id))
  ) THEN
    SELECT 'forbidden' AS status, 0 AS wiped;
    LEAVE proc;
  END IF;

  SELECT training INTO v_prev FROM athlete_consents WHERE athlete_id = p_athlete_id;

  INSERT INTO athlete_consents (athlete_id, training, img_web, img_social, img_whatsapp, img_print, version, updated_by, updated_at)
  VALUES (p_athlete_id, p_training, p_web, p_social, p_whatsapp, p_print, p_version, p_user_id, UTC_TIMESTAMP())
  ON DUPLICATE KEY UPDATE
    training = VALUES(training), img_web = VALUES(img_web), img_social = VALUES(img_social),
    img_whatsapp = VALUES(img_whatsapp), img_print = VALUES(img_print), version = VALUES(version),
    updated_by = VALUES(updated_by), updated_at = UTC_TIMESTAMP();

  INSERT INTO consent_log (athlete_id, user_id, training, img_web, img_social, img_whatsapp, img_print, version, ip, user_agent)
  VALUES (p_athlete_id, p_user_id, p_training, p_web, p_social, p_whatsapp, p_print, p_version, p_ip, LEFT(p_ua, 255));

  IF p_training = 0 AND COALESCE(v_prev, 0) = 1 THEN
    DELETE FROM session_done  WHERE athlete_id = p_athlete_id;
    DELETE FROM athlete_zones WHERE athlete_id = p_athlete_id;
    DELETE FROM athlete_tests WHERE athlete_id = p_athlete_id;
    SELECT 'ok' AS status, 1 AS wiped;
    LEAVE proc;
  END IF;

  SELECT 'ok' AS status, 0 AS wiped;
END $$

-- Lista para admins e adestradores: quen autoriza que (sen editar)
DROP PROCEDURE IF EXISTS Consent_ListStaff $$
CREATE PROCEDURE Consent_ListStaff(IN p_viewer_id BIGINT UNSIGNED)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM user_roles WHERE user_id = p_viewer_id AND role IN ('admin', 'coach')) THEN
    LEAVE proc;
  END IF;
  SELECT a.id AS athlete_id, a.full_name, a.is_minor = 1 AS is_minor, a.photo_file,
         c.training, c.img_web, c.img_social, c.img_whatsapp, c.img_print, c.version, c.updated_at
    FROM athletes a
    LEFT JOIN athlete_consents c ON c.athlete_id = a.id
   WHERE a.is_active = 1
   ORDER BY a.full_name;
END $$

-- Sesión: igual ca antes, e cada atleta leva a versión dos consentimentos e o de adestramento
DROP PROCEDURE IF EXISTS Session_GetUser $$
CREATE PROCEDURE Session_GetUser(IN p_token_hash CHAR(64))
BEGIN
  UPDATE sessions SET last_seen_at = UTC_TIMESTAMP()
   WHERE token_hash = p_token_hash AND last_seen_at < UTC_TIMESTAMP() - INTERVAL 5 MINUTE;

  SELECT u.id AS user_id, u.email, u.display_name, u.lang,
         (SELECT GROUP_CONCAT(r.role ORDER BY r.role) FROM user_roles r WHERE r.user_id = u.id) AS roles,
         (SELECT JSON_ARRAYAGG(JSON_OBJECT('id', a.id, 'full_name', a.full_name, 'is_minor', a.is_minor = 1,
                                           'photo_file', a.photo_file,
                                           'consent_version', c.version,
                                           'training', COALESCE(c.training, 0) = 1))
            FROM athletes a
            LEFT JOIN athlete_consents c ON c.athlete_id = a.id
           WHERE a.is_active = 1
             AND (a.user_id = u.id
                  OR a.id IN (SELECT g.athlete_id FROM athlete_guardians g WHERE g.user_id = u.id))
         ) AS athletes
  FROM sessions s
  JOIN users u ON u.id = s.user_id
  WHERE s.token_hash = p_token_hash
    AND s.expires_at >= UTC_TIMESTAMP()
    AND u.is_active = 1;
END $$

DELIMITER ;
