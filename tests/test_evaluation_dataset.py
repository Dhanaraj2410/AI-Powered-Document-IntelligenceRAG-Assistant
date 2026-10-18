import json
from pathlib import Path

from django.test import SimpleTestCase


class EvaluationDatasetTests(SimpleTestCase):
    def test_cases_include_question_keywords_and_source_location(self):
        path = Path(__file__).resolve().parents[1] / 'evaluation' / 'evaluation_dataset.json'
        dataset = json.loads(path.read_text(encoding='utf-8'))
        self.assertTrue(dataset)
        for case in dataset:
            self.assertTrue(case.get('question'))
            self.assertTrue(case.get('expected_keywords'))
            self.assertTrue(case.get('target_doc'))
            self.assertGreater(case.get('target_page', 0), 0)
