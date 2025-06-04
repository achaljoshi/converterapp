import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import TestCase, TestRun

def seed_testruns():
    testcases = TestCase.query.all()
    statuses = ['pass', 'fail', 'error']
    now = datetime.utcnow()
    for i, tc in enumerate(testcases):
        for j in range(3):  # 3 runs per test case
            tr = TestRun(
                test_case_id=tc.id,
                executed_at=now - timedelta(days=j),
                status=statuses[(i + j) % len(statuses)],
                output=f"Demo output {j+1} for {tc.name}",
                duration=1.0 + j
            )
            db.session.add(tr)
    db.session.commit()
    print("Seeded demo test runs.")

def main():
    app = create_app()
    with app.app_context():
        seed_testruns()

if __name__ == "__main__":
    main()