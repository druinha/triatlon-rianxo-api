LIST_RACES = "CALL Race_List(:p_viewer_id, :p_only_mine);"
GET_RACE = "CALL Race_Get(:p_race_id, :p_viewer_id);"
GET_ATTENDEES = "CALL Race_GetAttendees(:p_race_id, :p_viewer_id);"
CREATE_RACE = (
    "CALL Race_Create(:p_user_id, :p_name, :p_race_date, :p_start_time, :p_place, :p_zone, :p_sport, "
    ":p_distances, :p_official_url, :p_price);"
)
UPDATE_RACE = (
    "CALL Race_Update(:p_race_id, :p_user_id, :p_name, :p_race_date, :p_start_time, :p_place, :p_zone, "
    ":p_sport, :p_distances, :p_official_url, :p_price);"
)
DELETE_RACE = "CALL Race_Delete(:p_race_id, :p_user_id);"
SET_ATTENDANCE = (
    "CALL Race_SetAttendance(:p_race_id, :p_athlete_id, :p_user_id, :p_status, :p_distance, :p_registered);"
)
FIND_SIMILAR = "CALL Race_FindSimilar(:p_w1, :p_w2, :p_w3, :p_date, :p_viewer_id);"
LIST_FOR_ATHLETE = "CALL Race_ListForAthlete(:p_athlete_id, :p_viewer_id, :p_viewer_athlete_id);"
PUBLIC_LIST = "CALL Race_PublicList(:p_limit);"