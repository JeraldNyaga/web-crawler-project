import asyncio
from pathlib import Path
from scheduler.change_detector import ChangeDetector
from database import db

async def test_reports():
    await db.connect()
    
    detector = ChangeDetector()
    
    # Generate JSON report
    json_report = await detector.generate_change_report('json', 20)
    
    # Save it
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    with open("reports/test_report.json", "w") as f:
        f.write(json_report)
    print("✓ JSON report saved to reports/test_report.json")
    
    # Generate CSV report
    csv_report = await detector.generate_change_report('csv', 20)
    
    with open("reports/test_report.csv", "w") as f:
        f.write(csv_report)
    print("✓ CSV report saved to reports/test_report.csv")
    
    await db.disconnect()

asyncio.run(test_reports())
