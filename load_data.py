import numpy as np
import pandas as pd

SHEET_NAMES = [
    "People_Master", "ER_Case_Log", "Onboarding_Tracker", "Probation_Tracking",
    "FTC_Tracking", "Performance_Reviews", "Pay_Reviews", "Exit_Interviews",
    "Engagement_Survey", "TA_Funnel", "Bench_Tracking", "Touchpoints_Events",
    "PeopleTeam_Activity_Log",
]

DATE_COLS = {
    "People_Master": ["StartDate", "ContractEndDate", "LeaveDate"],
    "ER_Case_Log": ["DateOpened", "DateClosed"],
    "Onboarding_Tracker": ["StartDate", "TargetCompletionDate"],
    "Probation_Tracking": ["ProbationStartDate", "ProbationEndDate", "ReviewDate"],
    "FTC_Tracking": ["ContractStartDate", "ContractEndDate"],
    "Performance_Reviews": ["ReviewDate", "NextReviewDue"],
    "Pay_Reviews": ["ReviewDate", "EffectiveDate"],
    "Exit_Interviews": ["LeaveDate", "ExitInterviewDate"],
    "Engagement_Survey": ["SurveyDate"],
    "TA_Funnel": ["DateOpened"],
    "Bench_Tracking": ["BenchStartDate"],
    "Touchpoints_Events": ["Date"],
    "PeopleTeam_Activity_Log": ["Date"],
}

def load_data(path: str) -> dict[str, pd.DataFrame]:
    xl = pd.ExcelFile(path)
    data = {}
    for name in SHEET_NAMES:
        df = pd.read_excel(xl, name, dtype={"EmployeeID": str})
        for col in DATE_COLS.get(name, []):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        data[name] = df
    return data