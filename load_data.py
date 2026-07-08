import numpy as np
import pandas as pd
import openpyxl

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

#load the data from the excel file in dataframes and convert date columns to datetime format
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


#enable filtering by academy capability - joins academy column to a dataset if it doesnt have one already
def filter_activity_by_academy(activity_df, people_df, academy):
    if academy == "All":
        return activity_df
    academy_ids = set(people_df.loc[people_df["Academy"] == academy, "EmployeeID"])
    return activity_df[activity_df["RelatedEmployeeID"].isin(academy_ids)]


#filter by academy function
def _filt(df, academy):
    return df if academy == "All" else df[df["Academy"] == academy]

# SUMMARISING THE DATA FOR THE DASHBOARD 

def headcount_summary(data, academy="All"):
    df = _filt(data["People_Master"], academy)
    return {
        "total_headcount": int(len(df)),
        "active": int(df["ActiveEmployee"].sum()),
        "by_department": df["Department"].value_counts().to_dict(),
        "by_employment_type": df["EmploymentType"].value_counts().to_dict(),
    }

def er_case_summary(data, academy="All"):
    df = _filt(data["ER_Case_Log"], academy)
    return {
        "open_cases": int((df["Status"] != "Closed").sum()),
        "by_severity": df["Severity"].value_counts().to_dict(),
        "avg_days_open_closed": round(df.loc[df["Status"] == "Closed", "DaysOpen"].mean(), 1),
        "by_handler": df["HandledBy"].value_counts().to_dict(),
    }

def onboarding_summary(data, academy="All"):
    df = _filt(data["Onboarding_Tracker"], academy)
    df = df.assign(pct_complete=df["StagesCompleted"] / df["TotalStages"])
    return {
        "in_progress": int((df["Status"] == "In Progress").sum()),
        "complete": int((df["Status"] == "Complete").sum()),
        "avg_pct_complete": round(df["pct_complete"].mean() * 100, 1),
        "avg_induction_feedback": round(df["InductionFeedbackScore"].mean(), 1),
    }

def performance_summary(data, academy="All"):
    df = _filt(data["Performance_Reviews"], academy)
    return {
        "rating_distribution": df["Rating"].value_counts().to_dict(),
        "by_review_type": df["ReviewType"].value_counts().to_dict(),
    }

def bench_summary(data, academy="All"):
    df = _filt(data["Bench_Tracking"], academy)
    return {
        "on_bench": int(len(df)),
        "by_risk_flag": df["RiskFlag"].value_counts().to_dict(),
        "avg_days_on_bench": round(df["DaysOnBench"].mean(), 1),
    }

def engagement_summary(data, academy="All"):
    df = _filt(data["Engagement_Survey"], academy)
    trend = df.groupby("SurveyWave")["SatisfactionScore_1to10"].mean().round(1).to_dict()
    return {
        "satisfaction_trend_by_wave": trend,
        "enps_breakdown": df["eNPSCategory"].value_counts().to_dict(),
    }

def pay_review_summary(data, academy="All"):
    df = _filt(data["Pay_Reviews"], academy)
    approved = df[df["Status"] == "Approved"]
    budget_impact = (approved["ProposedSalaryGBP"] - approved["CurrentSalaryGBP"]).sum()
    return {
        "by_status": df["Status"].value_counts().to_dict(),
        "approved_budget_impact_gbp": int(budget_impact),
    }

def probation_summary(data, academy="All"):
    df = _filt(data["Probation_Tracking"], academy)
    passed = (df["Status"] == "Passed").sum()
    decided = df["Status"].isin(["Passed", "Failed"]).sum()
    return {
        "by_status": df["Status"].value_counts().to_dict(),
        "pass_rate_pct": round(100 * passed / decided, 1) if decided else None,
    }

def ftc_summary(data, academy="All"):
    df = _filt(data["FTC_Tracking"], academy)
    return {
        "by_status": df["Status"].value_counts().to_dict(),
        "expiring_within_90_days": int((df["DaysToExpiry"].between(0, 90)).sum()),
    }

def team_activity_summary(data, academy="All"):
    df = filter_activity_by_academy(data["PeopleTeam_Activity_Log"], data["People_Master"], academy)
    return {
        "total_hours": round(df["TimeSpentHours"].sum(), 1),
        "by_activity_type": df.groupby("ActivityType")["TimeSpentHours"].sum().round(1).to_dict(),
        "by_team_member": df.groupby("PeopleTeamMember")["TimeSpentHours"].sum().round(1).to_dict(),
    }


#build the json that builds the dashboard and feeds the ai model, with the ability to filter by academy
def build_context_json(data, academy="All"):
    return {
        "academy_filter": academy,
        "headcount": headcount_summary(data, academy),
        "er_cases": er_case_summary(data, academy),
        "onboarding": onboarding_summary(data, academy),
        "performance": performance_summary(data, academy),
        "bench": bench_summary(data, academy),
        "engagement": engagement_summary(data, academy),
        "pay_reviews": pay_review_summary(data, academy),
        "probation": probation_summary(data, academy),
        "ftc": ftc_summary(data, academy),
        "team_activity": team_activity_summary(data, academy),
    }


def exploring_data():
    fdm_data = load_data("Global_People_Intelligence_Dummy_Data (1).xlsx")

    headcount_summary = headcount_summary(fdm_data, "All")
    print("==== Headcount Summary ====")
    print(headcount_summary)
    print("==== Bench Summary ====")
    print(bench_summary(fdm_data, "All"))
    print("==== Pay Review Summary ====")
    print(pay_review_summary(fdm_data, "All"))
    print("==== Engagement Summary ====")
    print(engagement_summary(fdm_data, "All"))
    print("==== ER Case Summary ====")
    print(er_case_summary(fdm_data, "All"))
    print("==== Onboarding Summary ====")
    print(onboarding_summary(fdm_data, "All"))
    print("==== Performance Summary ====")
    print(performance_summary(fdm_data, "All"))
    print("==== Probation Summary ====")
    print(probation_summary(fdm_data, "All"))
    print("==== FTC Summary ====")
    print(ftc_summary(fdm_data, "All"))
    print("==== Team Activity Summary ====")
    print(team_activity_summary(fdm_data, "All"))
