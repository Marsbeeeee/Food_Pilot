from fastapi import APIRouter
from backend.database.connection import get_db_connection
from backend.schemas.profile import ProfileIn, ProfileOut

router = APIRouter(prefix = "/profile", tags = ["profile"])

@router.post("", response_model = ProfileOut)
def create_profile(profile: ProfileIn):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        '''
        INSERT INTO profiles (
            age, height, weight, sex, activity_level, goal,
            kcal_target, diet_style, allergies, exercise_type, pace
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            profile.age,
            profile.height,
            profile.weight,
            profile.sex,
            profile.activity_level,
            profile.goal,
            profile.kcal_target,
            profile.diet_style,
            profile.allergies,
            profile.exercise_type,
            profile.pace,
        ),
    )
    conn.commit()
    profile_id = cursor.lastrowid
    conn.close()

    return ProfileOut(id = profile_id, **profile.model_dump())

@router.post("/echo")
def echo_profile(profile: ProfileIn):
    return profile
