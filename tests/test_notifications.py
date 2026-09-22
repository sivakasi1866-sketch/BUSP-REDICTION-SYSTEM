from app.services.notification_service import check_and_create_arrival_notifications
from app.models.trip import Trip
from app.models.route import Stop
from app.models.notification import Notification

def test_notification_thresholds_and_deduplication(db_session):
    trip = db_session.query(Trip).first()
    student_stop = db_session.query(Stop).filter(Stop.stop_name == "Student Stop").first()

    # Step 1: ETA = 12 minutes -> No notification
    notifs_12 = check_and_create_arrival_notifications(
        db=db_session,
        trip=trip,
        stop_id=student_stop.id,
        stop_name=student_stop.stop_name,
        eta_minutes=12.0
    )
    assert len(notifs_12) == 0

    # Step 2: ETA = 9 minutes -> Triggers 10_MIN notification
    notifs_9 = check_and_create_arrival_notifications(
        db=db_session,
        trip=trip,
        stop_id=student_stop.id,
        stop_name=student_stop.stop_name,
        eta_minutes=9.0
    )
    assert len(notifs_9) == 1
    assert notifs_9[0].threshold_type == "10_MIN"

    # Step 3: ETA = 7 minutes -> Deduplication: should NOT create duplicate 10_MIN notification!
    notifs_7 = check_and_create_arrival_notifications(
        db=db_session,
        trip=trip,
        stop_id=student_stop.id,
        stop_name=student_stop.stop_name,
        eta_minutes=7.0
    )
    assert len(notifs_7) == 0

    # Step 4: ETA = 4 minutes -> Triggers 5_MIN notification (and does not duplicate 10_MIN)
    notifs_4 = check_and_create_arrival_notifications(
        db=db_session,
        trip=trip,
        stop_id=student_stop.id,
        stop_name=student_stop.stop_name,
        eta_minutes=4.0
    )
    assert len(notifs_4) == 1
    assert notifs_4[0].threshold_type == "5_MIN"

    # Step 5: ETA = 1 minute -> Triggers 2_MIN notification
    notifs_1 = check_and_create_arrival_notifications(
        db=db_session,
        trip=trip,
        stop_id=student_stop.id,
        stop_name=student_stop.stop_name,
        eta_minutes=1.0
    )
    assert len(notifs_1) == 1
    assert notifs_1[0].threshold_type == "2_MIN"

    # Step 6: ETA = 0 minute -> Triggers ARRIVED notification
    notifs_0 = check_and_create_arrival_notifications(
        db=db_session,
        trip=trip,
        stop_id=student_stop.id,
        stop_name=student_stop.stop_name,
        eta_minutes=0.0
    )
    assert len(notifs_0) == 1
    assert notifs_0[0].threshold_type == "ARRIVED"

    # Total notifications recorded in DB for this trip/user/stop must be exactly 4
    all_notifs = db_session.query(Notification).filter(Notification.trip_id == trip.id).all()
    assert len(all_notifs) == 4
    types = [n.threshold_type for n in all_notifs]
    assert types == ["10_MIN", "5_MIN", "2_MIN", "ARRIVED"]
