resource "grafana_rule_group" "rule_group_8bc20abbd7d8e863" {
  org_id           = 1
  name             = "increase traafic"
  folder_uid       = "efep1yw0pkxkwd"
  interval_seconds = 300

  rule {
    name      = "Unusual Traffic Spike"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "dfeotjrrru2o0b"
      model          = "{\"dataset\":\"sentinel\",\"editorMode\":\"code\",\"format\":\"table\",\"intervalMs\":1000,\"maxDataPoints\":43200,\"rawQuery\":true,\"rawSql\":\"SELECT COUNT(*) as current_rate\\nFROM events\\nWHERE timestamp > NOW() - INTERVAL '5 minutes'\\n\\n-- Query B: Baseline from last hour\\nSELECT AVG(count) as baseline_rate\\nFROM (\\n  SELECT COUNT(*) as count\\n  FROM events\\n  WHERE timestamp > NOW() - INTERVAL '1 hour'\\n    AND timestamp < NOW() - INTERVAL '5 minutes'\\n  GROUP BY time_bucket('5 minutes', timestamp)\\n) as baseline\",\"refId\":\"A\",\"sql\":{\"columns\":[{\"parameters\":[],\"type\":\"function\"}],\"groupBy\":[{\"property\":{\"type\":\"string\"},\"type\":\"groupBy\"}],\"limit\":50}}"
    }
    data {
      ref_id = "B"

      relative_time_range {
        from = 0
        to   = 0
      }

      datasource_uid = "__expr__"
      model          = "{\"conditions\":[{\"evaluator\":{\"params\":[],\"type\":\"gt\"},\"operator\":{\"type\":\"and\"},\"query\":{\"params\":[]},\"reducer\":{\"params\":[],\"type\":\"last\"},\"type\":\"query\"}],\"datasource\":{\"type\":\"__expr__\",\"uid\":\"__expr__\"},\"expression\":\"A\",\"intervalMs\":1000,\"maxDataPoints\":43200,\"reducer\":\"last\",\"refId\":\"B\",\"type\":\"reduce\"}"
    }
    data {
      ref_id = "C"

      relative_time_range {
        from = 0
        to   = 0
      }

      datasource_uid = "__expr__"
      model          = "{\"conditions\":[{\"evaluator\":{\"params\":[0],\"type\":\"gt\"},\"operator\":{\"type\":\"and\"},\"query\":{\"params\":[]},\"reducer\":{\"params\":[],\"type\":\"last\"},\"type\":\"query\"}],\"datasource\":{\"type\":\"__expr__\",\"uid\":\"__expr__\"},\"expression\":\"B\",\"intervalMs\":1000,\"maxDataPoints\":43200,\"refId\":\"C\",\"type\":\"threshold\"}"
    }

    no_data_state   = "NoData"
    exec_err_state  = "Error"
    for             = "5m"
    keep_firing_for = "5m"
    annotations     = {}
    labels = {
      alert_type = ""
      team       = "operations"
    }
    is_paused = false

    notification_settings {
      contact_point = "Honeypot Alerts"
    }
  }
}
