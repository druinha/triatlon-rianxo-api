-- Triatlón Rianxo · Perfil do atleta (Fase 2)
-- Pódese executar varias veces: só engade o que falta.

SET NAMES utf8mb4;

DELIMITER $$
DROP PROCEDURE IF EXISTS Utils_AddColumnIfMissing $$
CREATE PROCEDURE Utils_AddColumnIfMissing(IN p_table VARCHAR(64), IN p_column VARCHAR(64), IN p_definition VARCHAR(255))
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = DATABASE() AND table_name = p_table AND column_name = p_column
  ) THEN
    SET @ddl = CONCAT('ALTER TABLE `', p_table, '` ADD COLUMN `', p_column, '` ', p_definition);
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END $$
DELIMITER ;

-- Datos do perfil. Os sensibles (nacemento, licenza, chip) só os ven o propio atleta,
-- os seus titores, os adestradores e os admins: os procedementos devolven NULL ao resto.
CALL Utils_AddColumnIfMissing('athletes', 'birth_date',     'DATE NULL AFTER is_minor');
CALL Utils_AddColumnIfMissing('athletes', 'license_number', 'VARCHAR(40) NULL AFTER birth_date');
CALL Utils_AddColumnIfMissing('athletes', 'chip_code',      'VARCHAR(40) NULL AFTER license_number');
-- Nome do ficheiro da foto (aleatorio, .webp) dentro de MEDIA_DIR/athletes/
CALL Utils_AddColumnIfMissing('athletes', 'photo_file',     'VARCHAR(64) NULL AFTER chip_code');
CALL Utils_AddColumnIfMissing('athletes', 'updated_at',
  'DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP()) ON UPDATE CURRENT_TIMESTAMP AFTER created_at');

DROP PROCEDURE IF EXISTS Utils_AddColumnIfMissing;

-- Deportes que practica cada atleta (as claves tradúcense na web)
CREATE TABLE IF NOT EXISTS athlete_sports (
  athlete_id  BIGINT UNSIGNED NOT NULL,
  sport       ENUM('triathlon','duathlon','aquathlon','running','trail','road_cycling','mtb','swimming','open_water') NOT NULL,
  PRIMARY KEY (athlete_id, sport),
  CONSTRAINT fk_sports_athlete FOREIGN KEY (athlete_id) REFERENCES athletes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
