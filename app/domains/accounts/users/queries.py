LIST_USERS = "CALL User_ListAll();"
SET_USER_ACTIVE = "CALL User_SetActive(:p_user_id, :p_active);"
CREATE_PASSWORD_RESET = "CALL PasswordReset_Create(:p_token_hash, :p_user_id, :p_created_by, :p_valid_hours);"
