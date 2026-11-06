CREATE_INVITATION = (
    "CALL Invitation_Create(:p_token_hash, :p_email, :p_invited_name, :p_kind, :p_minor_name, "
    ":p_is_athlete, :p_grant_admin, :p_grant_coach, :p_created_by, :p_valid_days);"
)
GET_INVITATION_BY_TOKEN = "CALL Invitation_GetByToken(:p_token_hash);"
LIST_INVITATIONS = "CALL Invitation_List();"
REVOKE_INVITATION = "CALL Invitation_Revoke(:p_id);"
RENEW_INVITATION = "CALL Invitation_Renew(:p_id, :p_token_hash, :p_valid_days);"
ACCEPT_INVITATION_NEW_USER = (
    "CALL Invitation_AcceptNewUser(:p_token_hash, :p_password_hash, :p_display_name, :p_lang, :p_consent_ver);"
)
ACCEPT_INVITATION_EXISTING_USER = "CALL Invitation_AcceptExistingUser(:p_token_hash, :p_user_id);"
