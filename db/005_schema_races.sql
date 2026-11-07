-- Triatlón Rianxo · Calendario de carreiras (Fase 3)
-- Pódese executar varias veces.

SET NAMES utf8mb4;

-- Carreiras que engaden os propios atletas. Non son inscricións: só para saber quen vai.
CREATE TABLE IF NOT EXISTS races (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(160)    NOT NULL,
  race_date     DATE            NOT NULL,
  start_time    TIME            NULL,
  place         VARCHAR(120)    NOT NULL,
  zone          ENUM('galicia','spain','portugal') NOT NULL DEFAULT 'galicia',
  sport         ENUM('triathlon','duathlon','aquathlon','running','trail','road_cycling','mtb','swimming','open_water','other') NOT NULL,
  distances     VARCHAR(200)    NULL,          -- texto libre separado por comas: "Sprint, Olímpico"
  official_url  VARCHAR(500)    NULL,
  price         VARCHAR(80)     NULL,          -- texto libre: "25 €", "25 €, federados 20 €"
  created_by    BIGINT UNSIGNED NULL,
  created_at    DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  updated_at    DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()) ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_races_date (race_date),
  CONSTRAINT fk_races_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Quen vai a cada carreira. "Non vou" = sen fila.
CREATE TABLE IF NOT EXISTS race_attendance (
  race_id     BIGINT UNSIGNED NOT NULL,
  athlete_id  BIGINT UNSIGNED NOT NULL,
  status      ENUM('going','maybe') NOT NULL,
  distance    VARCHAR(60)     NULL,
  registered  TINYINT(1)      NOT NULL DEFAULT 0,   -- xa inscrito na web da carreira
  updated_by  BIGINT UNSIGNED NULL,
  updated_at  DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()) ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (race_id, athlete_id),
  KEY ix_att_athlete (athlete_id),
  CONSTRAINT fk_att_race    FOREIGN KEY (race_id)    REFERENCES races(id)    ON DELETE CASCADE,
  CONSTRAINT fk_att_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id) ON DELETE CASCADE,
  CONSTRAINT fk_att_user    FOREIGN KEY (updated_by) REFERENCES users(id)    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
