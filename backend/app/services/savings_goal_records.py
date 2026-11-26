from uuid import uuid4

from app.db.models import SavingsGoal, SavingsGoalStatus


def add_savings_goal(db, user_id, *, name, target_amount, deadline=None, description=None,
                     notify_days_before=None):
    goal = SavingsGoal(id=uuid4(), user_id=user_id, name=name, target_amount=target_amount,
                       current_amount=0, deadline=deadline, description=description,
                       status=SavingsGoalStatus.ACTIVE, notify_days_before=notify_days_before or [30, 15, 7, 3, 1])
    db.add(goal)
    return goal
