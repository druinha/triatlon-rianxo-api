GET_PROFILE = "CALL Athlete_GetProfile(:p_athlete_id, :p_viewer_id);"
LIST_DIRECTORY = "CALL Athlete_ListDirectory(:p_viewer_id);"
UPDATE_PROFILE = (
    "CALL Athlete_Update(:p_athlete_id, :p_editor_id, :p_full_name, :p_birth_date, "
    ":p_license, :p_chip, :p_sports);"
)
SET_PHOTO = "CALL Athlete_SetPhoto(:p_athlete_id, :p_editor_id, :p_photo_file);"
GET_PHOTO = "CALL Athlete_GetPhoto(:p_athlete_id, :p_viewer_id);"
