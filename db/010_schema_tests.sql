-- Triatlón Rianxo · Tests, zonas e avisos (Fase 4, parte 1)
-- Pódese executar varias veces.

SET NAMES utf8mb4;

-- Tests que fan os atletas (ou que mete o adestrador). Os datos brutos van en `data` (JSON);
-- os resultados principais van en columnas para ordenar e comparar.
--   swim_200   → 200 m nadando: data {total_s, hr}
--   run_3000   → 3000 m: data {hr_warmup, hr_start, splits:[{m, total_s, hr}]}
--   bike_ftp20 → 20′ a tope con potenciómetro: data {avg_watts, avg_hr}
--   bike_hr20  → 20′ a tope sen potenciómetro: data {avg_hr}
--   bike_climb → subida fixa: data {climb, total_s, avg_hr}
CREATE TABLE IF NOT EXISTS athlete_tests (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  athlete_id      BIGINT UNSIGNED NOT NULL,
  sport           ENUM('swim','bike','run') NOT NULL,
  kind            ENUM('swim_200','run_3000','bike_ftp20','bike_hr20','bike_climb') NOT NULL,
  test_date       DATE            NOT NULL,
  data            JSON            NOT NULL,
  result_seconds  INT UNSIGNED    NULL,     -- tempo final
  result_value    SMALLINT UNSIGNED NULL,   -- vatios medios (ftp20) ou pulso medio (hr20)
  avg_hr          SMALLINT UNSIGNED NULL,
  status          ENUM('submitted','reviewed') NOT NULL DEFAULT 'submitted',
  coach_comment   VARCHAR(1000)   NULL,
  created_by      BIGINT UNSIGNED NULL,
  reviewed_by     BIGINT UNSIGNED NULL,
  reviewed_at     DATETIME        NULL,
  created_at      DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (id),
  KEY ix_tests_athlete (athlete_id, sport, test_date),
  KEY ix_tests_status (status, created_at),
  CONSTRAINT fk_tests_athlete  FOREIGN KEY (athlete_id)  REFERENCES athletes(id) ON DELETE CASCADE,
  CONSTRAINT fk_tests_creator  FOREIGN KEY (created_by)  REFERENCES users(id)    ON DELETE SET NULL,
  CONSTRAINT fk_tests_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id)    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Zonas de cada atleta por deporte. `confirmed` = as que valen (confirmadas polo adestrador);
-- `provisional` = auto-calculadas do último test, á espera de que as confirme.
CREATE TABLE IF NOT EXISTS athlete_zones (
  athlete_id           BIGINT UNSIGNED NOT NULL,
  sport                ENUM('swim','bike','run') NOT NULL,
  confirmed_kind       VARCHAR(20)     NULL,
  confirmed            JSON            NULL,
  confirmed_by         BIGINT UNSIGNED NULL,
  confirmed_at         DATETIME        NULL,
  provisional_kind     VARCHAR(20)     NULL,
  provisional          JSON            NULL,
  provisional_test_id  BIGINT UNSIGNED NULL,
  updated_at           DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()) ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (athlete_id, sport),
  CONSTRAINT fk_zones_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id) ON DELETE CASCADE,
  CONSTRAINT fk_zones_user    FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_zones_test    FOREIGN KEY (provisional_test_id) REFERENCES athlete_tests(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Avisos dentro da web. O texto ponse na web (galego/castelán) segundo `kind`:
--   test_submitted → ao adestrador: un atleta enviou un test
--   test_reviewed  → ao atleta: o adestrador revisou o test
--   test_reminder  → ao atleta: toca repetir un test
CREATE TABLE IF NOT EXISTS notifications (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED NOT NULL,
  kind        VARCHAR(30)     NOT NULL,
  athlete_id  BIGINT UNSIGNED NULL,
  ref_id      BIGINT UNSIGNED NULL,
  sport       VARCHAR(10)     NULL,
  read_at     DATETIME        NULL,
  created_at  DATETIME        NOT NULL DEFAULT (UTC_TIMESTAMP()),
  PRIMARY KEY (id),
  KEY ix_notif_user (user_id, read_at, created_at),
  CONSTRAINT fk_notif_user    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
  CONSTRAINT fk_notif_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
