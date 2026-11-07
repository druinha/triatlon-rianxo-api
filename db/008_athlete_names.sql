-- Triatlón Rianxo · Nome, apelidos e nome para mostrar no perfil
-- full_name segue sendo o nome que ven os demais (perfil, directorio, carreiras):
--   nickname se o hai; se non, "first_name last_name". Athlete_Update mantén full_name ao día.
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

CALL Utils_AddColumnIfMissing('athletes', 'first_name', 'VARCHAR(80) NULL AFTER full_name');
CALL Utils_AddColumnIfMissing('athletes', 'last_name',  'VARCHAR(120) NULL AFTER first_name');
CALL Utils_AddColumnIfMissing('athletes', 'nickname',   'VARCHAR(60) NULL AFTER last_name');

DROP PROCEDURE IF EXISTS Utils_AddColumnIfMissing;

-- Perfís que xa existían: a primeira palabra é o nome e o resto os apelidos
UPDATE athletes
   SET first_name = SUBSTRING_INDEX(TRIM(full_name), ' ', 1),
       last_name  = NULLIF(TRIM(SUBSTRING(TRIM(full_name), CHAR_LENGTH(SUBSTRING_INDEX(TRIM(full_name), ' ', 1)) + 1)), '')
 WHERE first_name IS NULL;
