TEST_ACCESS = "CALL Test_Access(:p_athlete_id, :p_viewer_id);"
LIST_FOR_ATHLETE = "CALL Test_ListForAthlete(:p_athlete_id, :p_viewer_id);"
LIST_ZONES = "CALL Zones_ListForAthlete(:p_athlete_id, :p_viewer_id);"
CREATE_TEST = (
    "CALL Test_Create(:p_athlete_id, :p_editor_id, :p_sport, :p_kind, :p_test_date, :p_data, "
    ":p_result_seconds, :p_result_value, :p_avg_hr, :p_zones);"
)
GET_TEST = "CALL Test_Get(:p_test_id, :p_viewer_id);"
INBOX = "CALL Test_Inbox(:p_viewer_id, :p_status, :p_limit);"
REVIEW_TEST = "CALL Test_Review(:p_test_id, :p_viewer_id, :p_comment, :p_zones);"
SET_ZONES = "CALL Zones_Set(:p_athlete_id, :p_viewer_id, :p_sport, :p_kind, :p_zones);"
DELETE_TEST = "CALL Test_Delete(:p_test_id, :p_viewer_id);"
LIST_DUE = "CALL Test_ListDue(:p_viewer_id, :p_days);"
REMIND = "CALL Test_Remind(:p_viewer_id, :p_athlete_id, :p_sport);"
