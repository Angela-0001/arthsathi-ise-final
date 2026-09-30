"""
Financial Roadmap Engine — purely rule-based, fully explainable.
No ML. Every step is traceable to a rule.
"""
from app.models.user import User
from app.schemas.roadmap import RoadmapOut, RoadmapStep


async def generate(user: User) -> RoadmapOut:
    income = user.monthly_income or 0.0
    goals = user.goals or {}
    debts = goals.get("debts", [])   # list of {name, amount, interest_rate}
    savings_goal = goals.get("savings_target", 0.0)

    steps: list[RoadmapStep] = []
    total_debt = sum(d.get("amount", 0) for d in debts)

    # Rule 1: Emergency fund first (1 month income)
    emergency_fund = income * 1
    steps.append(RoadmapStep(
        priority=1,
        action="Build an emergency fund",
        reason="Covers 1 month of expenses in case of job loss or emergency",
        amount=emergency_fund,
    ))

    # Rule 2: Pay off high-interest debt (>24% annual) first
    high_interest = [d for d in debts if d.get("interest_rate", 0) > 24]
    for debt in high_interest:
        steps.append(RoadmapStep(
            priority=2,
            action=f"Pay off {debt.get('name', 'high-interest loan')}",
            reason=f"Interest rate {debt.get('interest_rate')}% is above 24% threshold — costing more than savings earn",
            amount=debt.get("amount"),
        ))

    # Rule 3: Apply for eligible government schemes
    steps.append(RoadmapStep(
        priority=3,
        action="Apply for eligible government welfare schemes",
        reason="Free or subsidized benefits you qualify for can reduce financial pressure",
    ))

    # Rule 4: Allocate 20% income to savings if no high-interest debt
    if not high_interest and income > 0:
        steps.append(RoadmapStep(
            priority=4,
            action="Save 20% of monthly income",
            reason="Standard 50/30/20 rule: 50% needs, 30% wants, 20% savings",
            amount=round(income * 0.2, 2),
        ))

    # Rule 5: Savings goal milestone
    if savings_goal > 0 and income > 0:
        months = round(savings_goal / max(income * 0.2, 1))
        steps.append(RoadmapStep(
            priority=5,
            action=f"Reach savings goal of ₹{savings_goal:,.0f}",
            reason=f"At 20% monthly savings, you can reach this in ~{months} months",
            amount=savings_goal,
        ))

    summary = (
        f"Based on your monthly income of ₹{income:,.0f} and total debt of ₹{total_debt:,.0f}, "
        f"here are {len(steps)} prioritized steps to improve your financial health."
    )

    return RoadmapOut(
        monthly_income=income,
        total_debt=total_debt,
        steps=steps,
        summary=summary,
    )
