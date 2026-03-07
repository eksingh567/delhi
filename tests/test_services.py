import unittest

from app.models import EvacuationRequest, GeopoliticalSignals, StudentRegistration
from app.services import SafePassEngine


class SafePassEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SafePassEngine()

    def test_assess_risk_high(self) -> None:
        signals = GeopoliticalSignals(
            country="Ukraine",
            news_severity=90,
            military_activity=95,
            diplomatic_tension=88,
            economic_sanctions=70,
            social_sentiment=65,
            historical_pattern=80,
        )

        risk = self.engine.assess_risk(signals)
        self.assertEqual(risk.risk_level.value, "HIGH")
        self.assertGreaterEqual(risk.probability_of_escalation, 70)

    def test_register_and_filter_students(self) -> None:
        student = StudentRegistration(
            student_id="STU-001",
            full_name="Aditi Sharma",
            email="aditi@example.com",
            phone="+380991234567",
            university="Kharkiv National University",
            country="Ukraine",
            city="Kharkiv",
            passport_last4="1234",
            emergency_contact="Rahul Sharma",
            location_sharing_enabled=True,
        )

        self.engine.register_student(student)
        filtered = self.engine.list_students("Ukraine")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].student_id, "STU-001")

    def test_evacuation_plan(self) -> None:
        req = EvacuationRequest(
            country="Ukraine",
            origin_city="Kharkiv",
            target_safe_hub="Poland Border",
            student_count=120,
        )

        plan = self.engine.plan_evacuation(req)
        self.assertEqual(plan.route[0], "Kharkiv")
        self.assertEqual(plan.route[-1], "Poland Border")
        self.assertEqual(plan.transport_capacity, 120)


if __name__ == "__main__":
    unittest.main()
