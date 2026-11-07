-- Triatlón Rianxo · Plans de adestramento (Fase 4, parte 2)
-- Pódese executar varias veces.
--
-- Cada semana pode haber:
--   • un plan XERAL (para todos),
--   • plans de GRUPO (p. ex. "Van a Zuia": os apuntados á carreira + os que engade o adestrador),
--   • plans INDIVIDUAIS.
-- A cada atleta tócalle o máis concreto que estea publicado: individual > grupo > xeral.

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS training_groups (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name        VARCHAR(120)    NOT NULL,
  race_id     BIGINT UNSIGNED NULL,          -- grupo dunha carreira: entran sós os que van
  created_by  BIGINT UNSIGNED NULL,
  created_at  DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (id),
  KEY ix_groups_race (race_id),
  CONSTRAINT fk_groups_race    FOREIGN KEY (race_id)    REFERENCES races(id) ON DELETE SET NULL,
  CONSTRAINT fk_groups_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- mode='add' → engadido a man; mode='exclude' → apuntado á carreira pero fóra deste grupo
CREATE TABLE IF NOT EXISTS training_group_members (
  group_id    BIGINT UNSIGNED NOT NULL,
  athlete_id  BIGINT UNSIGNED NOT NULL,
  mode        ENUM('add','exclude') NOT NULL,
  PRIMARY KEY (group_id, athlete_id),
  KEY ix_gm_athlete (athlete_id),
  CONSTRAINT fk_gm_group   FOREIGN KEY (group_id)   REFERENCES training_groups(id) ON DELETE CASCADE,
  CONSTRAINT fk_gm_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id)        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS training_plans (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  week_start    DATE            NOT NULL,     -- sempre un luns
  scope         ENUM('general','group','athlete') NOT NULL,
  group_id      BIGINT UNSIGNED NULL,
  athlete_id    BIGINT UNSIGNED NULL,
  -- Clave única por destinatario ('general:0', 'group:7', 'athlete:12'). Ponse no Plan_Save:
  -- os NULL non contan nos UNIQUE de MySQL e unha columna xerada non pode ir con FK en cascada.
  scope_key     VARCHAR(40)     NOT NULL,
  status        ENUM('draft','published') NOT NULL DEFAULT 'draft',
  note          VARCHAR(500)    NULL,
  created_by    BIGINT UNSIGNED NULL,
  updated_by    BIGINT UNSIGNED NULL,
  published_at  DATETIME        NULL,
  updated_at    DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()) ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_plan_week_scope (week_start, scope_key),
  CONSTRAINT fk_plans_group   FOREIGN KEY (group_id)   REFERENCES training_groups(id) ON DELETE CASCADE,
  CONSTRAINT fk_plans_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id)        ON DELETE CASCADE,
  CONSTRAINT fk_plans_creator FOREIGN KEY (created_by) REFERENCES users(id)           ON DELETE SET NULL,
  CONSTRAINT fk_plans_updater FOREIGN KEY (updated_by) REFERENCES users(id)           ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Sesións de cada día (0 = luns … 6 = domingo), na orde de `position`
CREATE TABLE IF NOT EXISTS plan_sessions (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  plan_id       BIGINT UNSIGNED NOT NULL,
  day           TINYINT UNSIGNED NOT NULL,
  position      TINYINT UNSIGNED NOT NULL DEFAULT 0,
  sport         ENUM('swim','bike','run','gym','rest','race','other') NOT NULL,
  title         VARCHAR(120)    NULL,
  duration_min  SMALLINT UNSIGNED NULL,
  content       TEXT            NULL,
  PRIMARY KEY (id),
  KEY ix_sessions_plan (plan_id, day, position),
  CONSTRAINT fk_sessions_plan FOREIGN KEY (plan_id) REFERENCES training_plans(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- O atleta marca a sesión como feita (e, se quere, como foi: esforzo 1-10 e un comentario)
CREATE TABLE IF NOT EXISTS session_done (
  session_id  BIGINT UNSIGNED NOT NULL,
  athlete_id  BIGINT UNSIGNED NOT NULL,
  rpe         TINYINT UNSIGNED NULL,
  comment     VARCHAR(500)    NULL,
  updated_by  BIGINT UNSIGNED NULL,
  done_at     DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (session_id, athlete_id),
  KEY ix_done_athlete (athlete_id),
  CONSTRAINT fk_done_session FOREIGN KEY (session_id) REFERENCES plan_sessions(id) ON DELETE CASCADE,
  CONSTRAINT fk_done_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id)      ON DELETE CASCADE,
  CONSTRAINT fk_done_user    FOREIGN KEY (updated_by) REFERENCES users(id)         ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
