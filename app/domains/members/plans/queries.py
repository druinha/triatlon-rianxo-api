LIST_GROUPS = "CALL Group_List(:p_viewer_id);"
CREATE_GROUP = "CALL Group_Create(:p_viewer_id, :p_name, :p_race_id);"
RENAME_GROUP = "CALL Group_Rename(:p_group_id, :p_viewer_id, :p_name);"
DELETE_GROUP = "CALL Group_Delete(:p_group_id, :p_viewer_id);"
GROUP_MEMBERS = "CALL Group_Members(:p_group_id, :p_viewer_id);"
SET_MEMBER = "CALL Group_SetMember(:p_group_id, :p_viewer_id, :p_athlete_id, :p_mode);"

LIST_WEEK = "CALL Plan_ListWeek(:p_viewer_id, :p_week);"
GET_FOR_EDITOR = "CALL Plan_GetForEditor(:p_viewer_id, :p_week, :p_scope, :p_group_id, :p_athlete_id);"
PLAN_SESSIONS = "CALL Plan_Sessions(:p_plan_id);"
SAVE_PLAN = (
    "CALL Plan_Save(:p_viewer_id, :p_week, :p_scope, :p_group_id, :p_athlete_id, :p_status, :p_note, :p_sessions);"
)
DELETE_PLAN = "CALL Plan_Delete(:p_plan_id, :p_viewer_id);"
FOR_ATHLETE = "CALL Plan_ForAthlete(:p_athlete_id, :p_viewer_id, :p_week);"
SESSIONS_FOR_ATHLETE = "CALL Plan_SessionsForAthlete(:p_plan_id, :p_athlete_id);"
SET_DONE = "CALL Session_SetDone(:p_session_id, :p_athlete_id, :p_viewer_id, :p_done, :p_rpe, :p_comment);"
PROGRESS = "CALL Plan_Progress(:p_plan_id, :p_viewer_id);"
GET_PLAN = "CALL Plan_GetById(:p_plan_id, :p_viewer_id);"
