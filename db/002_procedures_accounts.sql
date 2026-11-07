-- Triatlón Rianxo · Stored procedures de contas (Fase 1)
-- Convención: Domain_Action. As transaccións xestiónaas FastAPI (sen START TRANSACTION/COMMIT aquí).
-- Os procedementos que poden fallar por estado devolven unha columna `status` en vez de SIGNAL,
-- e o repositorio tradúceo a HTTPException.

DELIMITER $$

-- ───────────────────────── INVITACIÓNS ─────────────────────────

DROP PROCEDURE IF EXISTS Invitation_Create $$
CREATE PROCEDURE Invitation_Create(
  IN p_token_hash   CHAR(64),
  IN p_email        VARCHAR(254),
  IN p_invited_name VARCHAR(160),
  IN p_kind         VARCHAR(10),
  IN p_minor_name   VARCHAR(160),
  IN p_is_athlete   TINYINT,
  IN p_grant_admin  TINYINT,
  IN p_grant_coach  TINYINT,
  IN p_created_by   BIGINT UNSIGNED,
  IN p_valid_days   INT
)
BEGIN
  DECLARE v_id BIGINT UNSIGNED;

  INSERT INTO invitations
    (token_hash, email, invited_name, kind, minor_name, is_athlete, grant_admin, grant_coach, created_by, expires_at)
  VALUES
    (p_token_hash, LOWER(TRIM(p_email)), TRIM(p_invited_name), p_kind,
     NULLIF(TRIM(p_minor_name), ''), p_is_athlete, p_grant_admin, p_grant_coach, p_created_by,
     UTC_TIMESTAMP() + INTERVAL p_valid_days DAY);

  SET v_id = LAST_INSERT_ID();

  SELECT id, email, invited_name, kind, minor_name, is_athlete, grant_admin, grant_coach,
         created_at, expires_at, 'pending' AS status
  FROM invitations WHERE id = v_id;
END $$

DROP PROCEDURE IF EXISTS Invitation_GetByToken $$
CREATE PROCEDURE Invitation_GetByToken(IN p_token_hash CHAR(64))
BEGIN
  SELECT i.id, i.email, i.invited_name, i.kind, i.minor_name, i.expires_at,
         CASE
           WHEN i.used_at    IS NOT NULL         THEN 'used'
           WHEN i.revoked_at IS NOT NULL         THEN 'revoked'
           WHEN i.expires_at < UTC_TIMESTAMP()   THEN 'expired'
           ELSE 'pending'
         END AS status,
         EXISTS (SELECT 1 FROM users u WHERE u.email = i.email) AS email_registered
  FROM invitations i
  WHERE i.token_hash = p_token_hash;
END $$

DROP PROCEDURE IF EXISTS Invitation_List $$
CREATE PROCEDURE Invitation_List()
BEGIN
  SELECT i.id, i.email, i.invited_name, i.kind, i.minor_name,
         i.is_athlete, i.grant_admin, i.grant_coach,
         i.created_at, i.expires_at, i.used_at, i.revoked_at,
         CASE
           WHEN i.used_at    IS NOT NULL         THEN 'used'
           WHEN i.revoked_at IS NOT NULL         THEN 'revoked'
           WHEN i.expires_at < UTC_TIMESTAMP()   THEN 'expired'
           ELSE 'pending'
         END AS status,
         c.display_name AS created_by_name,
         u.display_name AS used_by_name
  FROM invitations i
  LEFT JOIN users c ON c.id = i.created_by
  LEFT JOIN users u ON u.id = i.used_by
  ORDER BY i.created_at DESC
  LIMIT 500;
END $$

DROP PROCEDURE IF EXISTS Invitation_Revoke $$
CREATE PROCEDURE Invitation_Revoke(IN p_id BIGINT UNSIGNED)
BEGIN
  -- Só se poden revogar as que aínda non se usaron (idempotente)
  UPDATE invitations
     SET revoked_at = UTC_TIMESTAMP()
   WHERE id = p_id AND used_at IS NULL AND revoked_at IS NULL;

  SELECT id,
         CASE
           WHEN used_at    IS NOT NULL THEN 'used'
           WHEN revoked_at IS NOT NULL THEN 'revoked'
           ELSE 'pending'
         END AS status
  FROM invitations WHERE id = p_id;
END $$

DROP PROCEDURE IF EXISTS Invitation_Renew $$
CREATE PROCEDURE Invitation_Renew(
  IN p_id          BIGINT UNSIGNED,
  IN p_token_hash  CHAR(64),
  IN p_valid_days  INT
)
BEGIN
  -- Xera un token novo e outros N días. Unha invitación xa usada nunca se reabre.
  UPDATE invitations
     SET token_hash = p_token_hash,
         expires_at = UTC_TIMESTAMP() + INTERVAL p_valid_days DAY,
         revoked_at = NULL
   WHERE id = p_id AND used_at IS NULL;

  SELECT id, email, invited_name, kind, minor_name, expires_at,
         IF(ROW_COUNT() > 0, 'renewed', 'not_renewable') AS status
  FROM invitations WHERE id = p_id;
END $$

-- Acepta a invitación creando unha conta nova.
DROP PROCEDURE IF EXISTS Invitation_AcceptNewUser $$
CREATE PROCEDURE Invitation_AcceptNewUser(
  IN p_token_hash     CHAR(64),
  IN p_password_hash  VARCHAR(255),
  IN p_display_name   VARCHAR(120),
  IN p_lang           VARCHAR(2),
  IN p_consent_ver    VARCHAR(20)
)
proc: BEGIN
  DECLARE v_inv_id   BIGINT UNSIGNED;
  DECLARE v_email    VARCHAR(254);
  DECLARE v_name     VARCHAR(160);
  DECLARE v_kind     VARCHAR(10);
  DECLARE v_minor    VARCHAR(160);
  DECLARE v_athlete  TINYINT;
  DECLARE v_admin    TINYINT;
  DECLARE v_coach    TINYINT;
  DECLARE v_user_id  BIGINT UNSIGNED;
  DECLARE v_ath_id   BIGINT UNSIGNED;

  -- Bloquea a fila para que dúas peticións simultáneas non a consuman dúas veces
  SELECT id, email, invited_name, kind, minor_name, is_athlete, grant_admin, grant_coach
    INTO v_inv_id, v_email, v_name, v_kind, v_minor, v_athlete, v_admin, v_coach
    FROM invitations
   WHERE token_hash = p_token_hash
     AND used_at IS NULL AND revoked_at IS NULL AND expires_at >= UTC_TIMESTAMP()
   FOR UPDATE;

  IF v_inv_id IS NULL THEN
    SELECT 'invalid' AS status, NULL AS user_id;
    LEAVE proc;
  END IF;

  IF EXISTS (SELECT 1 FROM users WHERE email = v_email) THEN
    SELECT 'email_taken' AS status, NULL AS user_id;
    LEAVE proc;
  END IF;

  INSERT INTO users (email, password_hash, display_name, lang, privacy_consent_at, privacy_consent_ver)
  VALUES (v_email, p_password_hash, COALESCE(NULLIF(TRIM(p_display_name), ''), v_name),
          IF(p_lang = 'es', 'es', 'gl'), UTC_TIMESTAMP(), p_consent_ver);
  SET v_user_id = LAST_INSERT_ID();

  CALL Invitation_ApplyToUser(v_inv_id, v_user_id, v_name, v_kind, v_minor, v_athlete, v_admin, v_coach);

  SELECT 'ok' AS status, v_user_id AS user_id;
END $$

-- Acepta a invitación cunha conta que xa existe (p. ex. un pai co segundo fillo,
-- ou dar o rol de adestrador a alguén que xa é atleta). O contrasinal compróbase en Python.
DROP PROCEDURE IF EXISTS Invitation_AcceptExistingUser $$
CREATE PROCEDURE Invitation_AcceptExistingUser(
  IN p_token_hash CHAR(64),
  IN p_user_id    BIGINT UNSIGNED
)
proc: BEGIN
  DECLARE v_inv_id   BIGINT UNSIGNED;
  DECLARE v_email    VARCHAR(254);
  DECLARE v_name     VARCHAR(160);
  DECLARE v_kind     VARCHAR(10);
  DECLARE v_minor    VARCHAR(160);
  DECLARE v_athlete  TINYINT;
  DECLARE v_admin    TINYINT;
  DECLARE v_coach    TINYINT;

  SELECT id, email, invited_name, kind, minor_name, is_athlete, grant_admin, grant_coach
    INTO v_inv_id, v_email, v_name, v_kind, v_minor, v_athlete, v_admin, v_coach
    FROM invitations
   WHERE token_hash = p_token_hash
     AND used_at IS NULL AND revoked_at IS NULL AND expires_at >= UTC_TIMESTAMP()
   FOR UPDATE;

  IF v_inv_id IS NULL THEN
    SELECT 'invalid' AS status, NULL AS user_id;
    LEAVE proc;
  END IF;

  -- A conta ten que ser a do email invitado e estar activa
  IF NOT EXISTS (SELECT 1 FROM users WHERE id = p_user_id AND email = v_email AND is_active = 1) THEN
    SELECT 'wrong_user' AS status, NULL AS user_id;
    LEAVE proc;
  END IF;

  CALL Invitation_ApplyToUser(v_inv_id, p_user_id, v_name, v_kind, v_minor, v_athlete, v_admin, v_coach);

  SELECT 'ok' AS status, p_user_id AS user_id;
END $$

-- Interno: aplica roles e perfís dunha invitación a unha conta e márcaa como usada.
DROP PROCEDURE IF EXISTS Invitation_ApplyToUser $$
CREATE PROCEDURE Invitation_ApplyToUser(
  IN p_inv_id   BIGINT UNSIGNED,
  IN p_user_id  BIGINT UNSIGNED,
  IN p_name     VARCHAR(160),
  IN p_kind     VARCHAR(10),
  IN p_minor    VARCHAR(160),
  IN p_athlete  TINYINT,
  IN p_admin    TINYINT,
  IN p_coach    TINYINT
)
BEGIN
  DECLARE v_ath_id BIGINT UNSIGNED;

  IF p_kind = 'guardian' THEN
    INSERT IGNORE INTO user_roles (user_id, role) VALUES (p_user_id, 'guardian');
    INSERT INTO athletes (full_name, is_minor, user_id) VALUES (p_minor, 1, NULL);
    SET v_ath_id = LAST_INSERT_ID();
    INSERT IGNORE INTO athlete_guardians (athlete_id, user_id) VALUES (v_ath_id, p_user_id);
  ELSEIF p_athlete = 1 THEN
    INSERT IGNORE INTO user_roles (user_id, role) VALUES (p_user_id, 'athlete');
    -- Un só perfil propio por conta
    INSERT INTO athletes (full_name, is_minor, user_id)
    SELECT p_name, 0, p_user_id FROM DUAL
     WHERE NOT EXISTS (SELECT 1 FROM athletes WHERE user_id = p_user_id);
  END IF;

  IF p_admin = 1 THEN INSERT IGNORE INTO user_roles (user_id, role) VALUES (p_user_id, 'admin'); END IF;
  IF p_coach = 1 THEN INSERT IGNORE INTO user_roles (user_id, role) VALUES (p_user_id, 'coach'); END IF;

  UPDATE invitations SET used_at = UTC_TIMESTAMP(), used_by = p_user_id
   WHERE id = p_inv_id AND used_at IS NULL;
END $$

-- ───────────────────────── LOGIN E SESIÓNS ─────────────────────────

DROP PROCEDURE IF EXISTS User_GetForLogin $$
CREATE PROCEDURE User_GetForLogin(IN p_email VARCHAR(254))
BEGIN
  SELECT id, email, password_hash, is_active
  FROM users WHERE email = LOWER(TRIM(p_email));
END $$

DROP PROCEDURE IF EXISTS User_UpdatePasswordHash $$
CREATE PROCEDURE User_UpdatePasswordHash(IN p_user_id BIGINT UNSIGNED, IN p_password_hash VARCHAR(255))
BEGIN
  UPDATE users SET password_hash = p_password_hash WHERE id = p_user_id;
  SELECT ROW_COUNT() AS updated;
END $$

DROP PROCEDURE IF EXISTS LoginAttempt_Record $$
CREATE PROCEDURE LoginAttempt_Record(IN p_email VARCHAR(254), IN p_ip VARCHAR(45), IN p_success TINYINT)
BEGIN
  INSERT INTO login_attempts (email, ip, success) VALUES (LOWER(TRIM(p_email)), p_ip, p_success);
  -- Limpeza: non gardamos intentos de máis de 30 días
  DELETE FROM login_attempts WHERE created_at < UTC_TIMESTAMP() - INTERVAL 30 DAY LIMIT 1000;
  SELECT 1 AS recorded;
END $$

DROP PROCEDURE IF EXISTS LoginAttempt_CountRecentFailures $$
CREATE PROCEDURE LoginAttempt_CountRecentFailures(IN p_email VARCHAR(254), IN p_ip VARCHAR(45), IN p_minutes INT)
BEGIN
  DECLARE v_since DATETIME DEFAULT UTC_TIMESTAMP() - INTERVAL p_minutes MINUTE;
  DECLARE v_last_ok_id BIGINT UNSIGNED;

  -- Os fallos anteriores ao último acceso correcto (ou restablecemento) xa non contan.
  -- Compárase por id (orde de inserción) porque varios intentos poden caer no mesmo segundo.
  SELECT COALESCE(MAX(id), 0) INTO v_last_ok_id
    FROM login_attempts WHERE email = LOWER(TRIM(p_email)) AND success = 1;

  SELECT
    (SELECT COUNT(*) FROM login_attempts
      WHERE email = LOWER(TRIM(p_email)) AND success = 0
        AND created_at >= v_since AND id > v_last_ok_id) AS email_failures,
    (SELECT COUNT(*) FROM login_attempts
      WHERE ip = p_ip AND success = 0 AND created_at >= v_since) AS ip_failures;
END $$

DROP PROCEDURE IF EXISTS Session_Create $$
CREATE PROCEDURE Session_Create(
  IN p_token_hash CHAR(64),
  IN p_user_id    BIGINT UNSIGNED,
  IN p_valid_days INT,
  IN p_ip         VARCHAR(45),
  IN p_user_agent VARCHAR(255)
)
BEGIN
  INSERT INTO sessions (token_hash, user_id, expires_at, ip, user_agent)
  VALUES (p_token_hash, p_user_id, UTC_TIMESTAMP() + INTERVAL p_valid_days DAY, p_ip, LEFT(p_user_agent, 255));

  UPDATE users SET last_login_at = UTC_TIMESTAMP() WHERE id = p_user_id;
  DELETE FROM sessions WHERE user_id = p_user_id AND expires_at < UTC_TIMESTAMP();

  SELECT expires_at FROM sessions WHERE token_hash = p_token_hash;
END $$

-- Devolve a conta da sesión (se é válida e a conta está activa) cos seus roles e perfís.
DROP PROCEDURE IF EXISTS Session_GetUser $$
CREATE PROCEDURE Session_GetUser(IN p_token_hash CHAR(64))
BEGIN
  -- Actualiza last_seen como moito unha vez cada 5 minutos
  UPDATE sessions SET last_seen_at = UTC_TIMESTAMP()
   WHERE token_hash = p_token_hash AND last_seen_at < UTC_TIMESTAMP() - INTERVAL 5 MINUTE;

  SELECT u.id AS user_id, u.email, u.display_name, u.lang,
         (SELECT GROUP_CONCAT(r.role ORDER BY r.role) FROM user_roles r WHERE r.user_id = u.id) AS roles,
         (SELECT JSON_ARRAYAGG(JSON_OBJECT('id', a.id, 'full_name', a.full_name, 'is_minor', a.is_minor = 1,
                                           'photo_file', a.photo_file))
            FROM athletes a
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

DROP PROCEDURE IF EXISTS Session_Delete $$
CREATE PROCEDURE Session_Delete(IN p_token_hash CHAR(64))
BEGIN
  DELETE FROM sessions WHERE token_hash = p_token_hash;
  SELECT ROW_COUNT() AS deleted;
END $$

-- ───────────────────────── RESTABLECER CONTRASINAL ─────────────────────────

DROP PROCEDURE IF EXISTS PasswordReset_Create $$
CREATE PROCEDURE PasswordReset_Create(
  IN p_token_hash  CHAR(64),
  IN p_user_id     BIGINT UNSIGNED,
  IN p_created_by  BIGINT UNSIGNED,
  IN p_valid_hours INT
)
proc: BEGIN
  IF NOT EXISTS (SELECT 1 FROM users WHERE id = p_user_id) THEN
    SELECT 'not_found' AS status, NULL AS email, NULL AS display_name, NULL AS expires_at;
    LEAVE proc;
  END IF;

  -- Só unha ligazón válida á vez: invalida as anteriores sen usar
  UPDATE password_resets SET used_at = UTC_TIMESTAMP()
   WHERE user_id = p_user_id AND used_at IS NULL;

  INSERT INTO password_resets (token_hash, user_id, created_by, expires_at)
  VALUES (p_token_hash, p_user_id, p_created_by, UTC_TIMESTAMP() + INTERVAL p_valid_hours HOUR);

  SELECT 'ok' AS status, u.email, u.display_name, r.expires_at
  FROM password_resets r JOIN users u ON u.id = r.user_id
  WHERE r.token_hash = p_token_hash;
END $$

DROP PROCEDURE IF EXISTS PasswordReset_GetByToken $$
CREATE PROCEDURE PasswordReset_GetByToken(IN p_token_hash CHAR(64))
BEGIN
  SELECT u.email, u.display_name, r.expires_at,
         CASE
           WHEN r.used_at IS NOT NULL         THEN 'used'
           WHEN r.expires_at < UTC_TIMESTAMP() THEN 'expired'
           WHEN u.is_active = 0               THEN 'inactive'
           ELSE 'pending'
         END AS status
  FROM password_resets r JOIN users u ON u.id = r.user_id
  WHERE r.token_hash = p_token_hash;
END $$

DROP PROCEDURE IF EXISTS PasswordReset_Consume $$
CREATE PROCEDURE PasswordReset_Consume(IN p_token_hash CHAR(64), IN p_password_hash VARCHAR(255))
proc: BEGIN
  DECLARE v_reset_id BIGINT UNSIGNED;
  DECLARE v_user_id  BIGINT UNSIGNED;

  SELECT r.id, r.user_id INTO v_reset_id, v_user_id
    FROM password_resets r JOIN users u ON u.id = r.user_id
   WHERE r.token_hash = p_token_hash
     AND r.used_at IS NULL AND r.expires_at >= UTC_TIMESTAMP() AND u.is_active = 1
   FOR UPDATE;

  IF v_reset_id IS NULL THEN
    SELECT 'invalid' AS status, NULL AS user_id;
    LEAVE proc;
  END IF;

  -- Conta como acceso correcto: desbloquea o límite de intentos
  INSERT INTO login_attempts (email, ip, success)
  SELECT email, NULL, 1 FROM users WHERE id = v_user_id;

  UPDATE users SET password_hash = p_password_hash WHERE id = v_user_id;
  UPDATE password_resets SET used_at = UTC_TIMESTAMP() WHERE id = v_reset_id;
  -- Pecha todas as sesións abertas desa conta
  DELETE FROM sessions WHERE user_id = v_user_id;

  SELECT 'ok' AS status, v_user_id AS user_id;
END $$

-- ───────────────────────── ADMINISTRACIÓN DE CONTAS ─────────────────────────

DROP PROCEDURE IF EXISTS User_ListAll $$
CREATE PROCEDURE User_ListAll()
BEGIN
  SELECT u.id, u.email, u.display_name, u.lang, u.is_active, u.created_at, u.last_login_at,
         (SELECT GROUP_CONCAT(r.role ORDER BY r.role) FROM user_roles r WHERE r.user_id = u.id) AS roles,
         (SELECT JSON_ARRAYAGG(a.full_name)
            FROM athlete_guardians g JOIN athletes a ON a.id = g.athlete_id
           WHERE g.user_id = u.id) AS minors
  FROM users u
  ORDER BY u.display_name;
END $$

DROP PROCEDURE IF EXISTS User_SetActive $$
CREATE PROCEDURE User_SetActive(IN p_user_id BIGINT UNSIGNED, IN p_active TINYINT)
proc: BEGIN
  -- Nunca deixar o clube sen ningún admin activo
  IF p_active = 0
     AND EXISTS (SELECT 1 FROM user_roles WHERE user_id = p_user_id AND role = 'admin')
     AND (SELECT COUNT(*) FROM users u JOIN user_roles r ON r.user_id = u.id AND r.role = 'admin'
           WHERE u.is_active = 1 AND u.id <> p_user_id) = 0 THEN
    SELECT 'last_admin' AS status;
    LEAVE proc;
  END IF;

  UPDATE users SET is_active = p_active WHERE id = p_user_id;
  IF ROW_COUNT() = 0 AND NOT EXISTS (SELECT 1 FROM users WHERE id = p_user_id) THEN
    SELECT 'not_found' AS status;
    LEAVE proc;
  END IF;

  IF p_active = 0 THEN
    DELETE FROM sessions WHERE user_id = p_user_id;
  END IF;

  SELECT 'ok' AS status;
END $$

DELIMITER ;
