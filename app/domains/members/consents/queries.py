LIST_MINE = "CALL Consent_ListMine(:p_user_id);"
LIST_STAFF = "CALL Consent_ListStaff(:p_viewer_id);"
SET_CONSENT = (
    "CALL Consent_Set(:p_athlete_id, :p_user_id, :p_training, :p_web, :p_social, :p_whatsapp, :p_print, "
    ":p_version, :p_ip, :p_ua);"
)
HAS_TRAINING = "SELECT Consent_HasTraining(:p_athlete_id) AS ok;"
