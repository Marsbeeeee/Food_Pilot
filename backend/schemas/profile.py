from pydantic import BaseModel

class ProfileIn(BaseModel):
    age : int
    height : float
    weight : float
    sex : str
    activity_level : str
    goal : str
    kcal_target : int
    diet_style : str
    allergies : str
    exercise_type : str
    pace : str

class ProfileOut(ProfileIn):
    id : int