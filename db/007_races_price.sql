-- Triatlón Rianxo · Prezo da carreira (opcional)
-- Para bases de datos que xa tiñan a táboa races (005 xa a crea con esta columna).
-- Pódese executar varias veces.

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

CALL Utils_AddColumnIfMissing('races', 'price', 'VARCHAR(80) NULL AFTER official_url');

DROP PROCEDURE IF EXISTS Utils_AddColumnIfMissing;
