from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app import create_app, db
from app.models import TestCase, TestRun, AuditLog, Workflow
import random

app = create_app()

scheduler = BackgroundScheduler()

def get_next_run_at(schedule, from_time=None):
    if not from_time:
        from_time = datetime.utcnow()
    if schedule == 'daily':
        return from_time + timedelta(days=1)
    elif schedule == 'weekly':
        return from_time + timedelta(weeks=1)
    return None

def run_due_testcases():
    with app.app_context():
        now = datetime.utcnow()
        due_cases = TestCase.query.filter(
            TestCase.schedule.in_(['daily', 'weekly']),
            (TestCase.next_run_at == None) | (TestCase.next_run_at <= now)
        ).all()
        for testcase in due_cases:
            workflow = Workflow.query.get(testcase.workflow_id)
            status = random.choice(['passed', 'failed'])
            output = f"Scheduled run for test case {testcase.name} (workflow: {workflow.name if workflow else 'N/A'})"
            run = TestRun(
                test_case_id=testcase.id,
                executed_at=now,
                status=status,
                output=output,
                duration=round(random.uniform(0.1, 2.0), 2)
            )
            db.session.add(run)
            db.session.add(AuditLog(
                user='scheduler',
                action='execute',
                filetype='testcase',
                details=f"Scheduled execution of test case: {testcase.name} (ID: {testcase.id}), status: {status}"
            ))
            testcase.next_run_at = get_next_run_at(testcase.schedule, now)
        db.session.commit()

scheduler.add_job(run_due_testcases, 'interval', minutes=1)

if __name__ == '__main__':
    scheduler.start()
    print('Scheduler started. Press Ctrl+C to exit.')
    try:
        while True:
            import time
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown() 