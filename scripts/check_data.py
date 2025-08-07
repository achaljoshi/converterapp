from app import create_app, db
from app.models import *

def check_data():
    app = create_app()
    with app.app_context():
        print("=== Database Data Check ===")
        
        # Check FileTypes
        filetypes = FileType.query.all()
        print(f"FileTypes: {len(filetypes)} records")
        for ft in filetypes:
            print(f"  - {ft.name}: {ft.description}")
        
        # Check Configurations
        configs = Configuration.query.all()
        print(f"Configurations: {len(configs)} records")
        for cfg in configs:
            print(f"  - {cfg.name}: {cfg.file_type}")
        
        # Check ConverterConfigs
        converters = ConverterConfig.query.all()
        print(f"ConverterConfigs: {len(converters)} records")
        for conv in converters:
            print(f"  - {conv.name}: {conv.source_type} -> {conv.target_type}")
        
        # Check Workflows
        workflows = Workflow.query.all()
        print(f"Workflows: {len(workflows)} records")
        for wf in workflows:
            print(f"  - {wf.name}: {wf.description}")
        
        # Check TestCases
        testcases = TestCase.query.all()
        print(f"TestCases: {len(testcases)} records")
        for tc in testcases:
            print(f"  - {tc.name}: {tc.description}")
        
        # Check TestFrameworks
        frameworks = TestFramework.query.all()
        print(f"TestFrameworks: {len(frameworks)} records")
        for fw in frameworks:
            print(f"  - {fw.name}: {fw.language}")
        
        # Check Labels
        labels = Label.query.all()
        print(f"Labels: {len(labels)} records")
        for label in labels:
            print(f"  - {label.name}: {label.color}")
        
        # Check Users
        users = User.query.all()
        print(f"Users: {len(users)} records")
        for user in users:
            print(f"  - {user.username}: {user.role.name if user.role else 'No role'}")
        
        print("=== End Data Check ===")

if __name__ == '__main__':
    check_data() 