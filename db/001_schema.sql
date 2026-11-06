-- Triatlón Rianxo · Esquema de contas (Fase 1)
-- Todas as datas en UTC.
-- Modelo: unha CONTA (users) é quen inicia sesión. Un PERFIL DE ATLETA (athletes)
-- pode pertencer á propia conta (adultos) ou estar xestionado por titores (menores da escola).

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS users (
  id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email                VARCHAR(254)    NOT NULL,
  password_hash        VARCHAR(255)    NOT NULL,
  display_name         VARCHAR(120)    NOT NULL,
  lang                 ENUM('gl','es') NOT NULL DEFAULT 'gl',
  is_active            TINYINT(1)      NOT NULL DEFAULT 1,
  privacy_consent_at   DATETIME        NULL,
  privacy_consent_ver  VARCHAR(20)     NULL,
  created_at           DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  updated_at           DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()) ON UPDATE CURRENT_TIMESTAMP,
  last_login_at        DATETIME        NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS user_roles (
  user_id  BIGINT UNSIGNED NOT NULL,
  role     ENUM('admin','coach','athlete','guardian') NOT NULL,
  PRIMARY KEY (user_id, role),
  CONSTRAINT fk_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Perfil deportivo. Na Fase 2 engádense data de nacemento, licenza, chip, deportes…
CREATE TABLE IF NOT EXISTS athletes (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  full_name   VARCHAR(160)    NOT NULL,
  is_minor    TINYINT(1)      NOT NULL DEFAULT 0,
  user_id     BIGINT UNSIGNED NULL,          -- conta propia (adultos)
  is_active   TINYINT(1)      NOT NULL DEFAULT 1,
  created_at  DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (id),
  UNIQUE KEY uq_athletes_user (user_id),
  CONSTRAINT fk_athletes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Titores (pais/nais) que xestionan perfís de menores. Un menor pode ter varios titores.
CREATE TABLE IF NOT EXISTS athlete_guardians (
  athlete_id  BIGINT UNSIGNED NOT NULL,
  user_id     BIGINT UNSIGNED NOT NULL,
  created_at  DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (athlete_id, user_id),
  KEY ix_guardians_user (user_id),
  CONSTRAINT fk_guard_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id) ON DELETE CASCADE,
  CONSTRAINT fk_guard_user    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Invitacións persoais. Gárdase só o hash SHA-256 do token, nunca o token.
-- kind='member'   → adulto (atleta e/ou staff)
-- kind='guardian' → pai/nai que xestiona o perfil dun menor (minor_name)
CREATE TABLE IF NOT EXISTS invitations (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  token_hash    CHAR(64)        NOT NULL,
  email         VARCHAR(254)    NOT NULL,
  invited_name  VARCHAR(160)    NOT NULL,
  kind          ENUM('member','guardian') NOT NULL DEFAULT 'member',
  minor_name    VARCHAR(160)    NULL,
  is_athlete    TINYINT(1)      NOT NULL DEFAULT 1,
  grant_admin   TINYINT(1)      NOT NULL DEFAULT 0,
  grant_coach   TINYINT(1)      NOT NULL DEFAULT 0,
  created_by    BIGINT UNSIGNED NULL,
  created_at    DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  expires_at    DATETIME        NOT NULL,
  used_at       DATETIME        NULL,
  used_by       BIGINT UNSIGNED NULL,
  revoked_at    DATETIME        NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_inv_token (token_hash),
  KEY ix_inv_email (email),
  CONSTRAINT fk_inv_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_inv_user    FOREIGN KEY (used_by)    REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS sessions (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  token_hash    CHAR(64)        NOT NULL,
  user_id       BIGINT UNSIGNED NOT NULL,
  created_at    DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  expires_at    DATETIME        NOT NULL,
  last_seen_at  DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  ip            VARCHAR(45)     NULL,
  user_agent    VARCHAR(255)    NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_sess_token (token_hash),
  KEY ix_sess_user (user_id),
  CONSTRAINT fk_sess_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Ligazóns de restablecemento de contrasinal que xera un admin (mándanse por WhatsApp)
CREATE TABLE IF NOT EXISTS password_resets (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  token_hash  CHAR(64)        NOT NULL,
  user_id     BIGINT UNSIGNED NOT NULL,
  created_by  BIGINT UNSIGNED NULL,
  created_at  DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  expires_at  DATETIME        NOT NULL,
  used_at     DATETIME        NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_reset_token (token_hash),
  KEY ix_reset_user (user_id),
  CONSTRAINT fk_reset_user    FOREIGN KEY (user_id)    REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_reset_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Para limitar intentos de login (forza bruta)
CREATE TABLE IF NOT EXISTS login_attempts (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email       VARCHAR(254)    NOT NULL,
  ip          VARCHAR(45)     NULL,
  success     TINYINT(1)      NOT NULL,
  created_at  DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (id),
  KEY ix_attempts_email (email, created_at),
  KEY ix_attempts_ip (ip, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
