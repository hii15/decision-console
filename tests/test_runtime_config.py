import io
import unittest

import pandas as pd

from config.runtime_config import load_runtime_config
from decision.decision_engine import run_decision_engine


class RuntimeConfigTests(unittest.TestCase):
    def test_load_runtime_config_with_overrides(self):
        payload = io.StringIO(
            '{"base_target":1.2,"channel_map":{"facebook":"Hybrid"},"multiplier_map":{"Hybrid":0.9}}'
        )
        cfg = load_runtime_config(payload)
        self.assertAlmostEqual(cfg.base_target, 1.2)
        self.assertEqual(cfg.channel_map["facebook"], "Hybrid")
        self.assertAlmostEqual(cfg.multiplier_map["Hybrid"], 0.9)

    def test_decision_engine_uses_custom_multiplier_map(self):
        df = pd.DataFrame(
            {
                "media_source": ["facebook"],
                "campaign": ["c1"],
                "d7_roas": [0.95],
            }
        )
        channel_map = {"facebook": "Hybrid"}
        out = run_decision_engine(
            df,
            channel_map=channel_map,
            base_target=1.0,
            multiplier_map={"Hybrid": 1.0},
        )
        self.assertEqual(out.loc[0, "decision"], "Test")

    def test_load_runtime_config_with_rule_overrides(self):
        payload = io.StringIO(
            '{"decision_rules":[{"op":">=","threshold":0.95,"decision":"Scale"}],"fallback_decision":"Reduce"}'
        )
        cfg = load_runtime_config(payload)
        self.assertEqual(cfg.decision_rules[0]["decision"], "Scale")
        self.assertEqual(cfg.fallback_decision, "Reduce")

    def test_load_runtime_config_with_rule_conditions(self):
        payload = io.StringIO(
            "{\"decision_rules\":[{\"op\":\">=\",\"threshold\":0.95,\"decision\":\"Scale\",\"conditions\":{\"country\":\"KR\"}}]}"
        )
        cfg = load_runtime_config(payload)
        self.assertEqual(cfg.decision_rules[0]["conditions"]["country"], "KR")

if __name__ == "__main__":
    unittest.main()
