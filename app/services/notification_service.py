from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.trip import Trip
from app.models.assignment import DefaultAssignment, SpecialAssignment
from app.models.user import User

THRESHOLDS = [
    (10, "10_MIN", "Bus is ~10 mins away", "Your bus {bus_number} is approximately 10 minutes away from {stop_name}."),
    (5, "5_MIN", "Bus is ~5 mins away", "Your bus {bus_number} is approximately 5 minutes away from {stop_name}. Please be ready!"),
    (2, "2_MIN", "Bus arriving shortly (~2 mins)", "Your bus {bus_number} is approaching {stop_name}. Please head to the stop!"),
    (0.5, "ARRIVED", "Bus has arrived at your stop", "Your bus {bus_number} has arrived at {stop_name}.")
]

def check_and_create_arrival_notifications(
    db: Session,
    trip: Trip,
    stop_id: int,
    stop_name: str,
    eta_minutes: float
) -> list[Notification]:
    """
    Checks if a threshold is crossed for students/staff assigned to this stop and bus.
    Enforces strict deduplication: exactly one notification per threshold type per trip.
    """
    created_notifications = []

    # Find all users assigned to this bus and stop
    # Check default assignments
    default_assigned_users = (
        db.query(DefaultAssignment.user_id)
        .filter(
            DefaultAssignment.bus_id == trip.bus_id,
            DefaultAssignment.stop_id == stop_id,
            DefaultAssignment.is_active == True
        )
        .all()
    )
    user_ids = {u[0] for u in default_assigned_users}

    # Also check special assignments for today
    today = datetime.now(timezone.utc).date()
    special_assigned_users = (
        db.query(SpecialAssignment.user_id)
        .filter(
            SpecialAssignment.bus_id == trip.bus_id,
            SpecialAssignment.stop_id == stop_id,
            SpecialAssignment.effective_date == today,
            SpecialAssignment.is_active == True
        )
        .all()
    )
    for u in special_assigned_users:
        user_ids.add(u[0])

    if not user_ids:
        return []

    bus_number = trip.bus.bus_number if trip.bus else "Bus"

    for threshold_val, threshold_code, title_tpl, msg_tpl in THRESHOLDS:
        if eta_minutes <= threshold_val:
            for uid in user_ids:
                # Check if this threshold notification already exists for this trip + user + stop
                existing = db.query(Notification).filter(
                    Notification.trip_id == trip.id,
                    Notification.user_id == uid,
                    Notification.stop_id == stop_id,
                    Notification.threshold_type == threshold_code
                ).first()

                if not existing:
                    notif = Notification(
                        user_id=uid,
                        trip_id=trip.id,
                        stop_id=stop_id,
                        threshold_type=threshold_code,
                        title=title_tpl.format(bus_number=bus_number, stop_name=stop_name),
                        message=msg_tpl.format(bus_number=bus_number, stop_name=stop_name),
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(notif)
                    created_notifications.append(notif)

    if created_notifications:
        db.commit()

    return created_notifications
