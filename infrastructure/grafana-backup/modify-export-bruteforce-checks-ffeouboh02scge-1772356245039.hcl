resource "grafana_rule_group" "rule_group_3fdc9a0804ee47c7" {
  org_id           = 1
  name             = "bruteforce-checks"
  folder_uid       = "efeotzl6s29dsa"
  interval_seconds = 60

  rule {
    name      = "SSH Bruteforce Detected"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "dfeotjrrru2o0b"
      model          = "{\"dataset\":\"sentinel\",\"editorMode\":\"code\",\"format\":\"table\",\"intervalMs\":1000,\"maxDataPoints\":43200,\"rawQuery\":true,\"rawSql\":\"SELECT \\n  COUNT(*) as attempt_count,\\n  source_ip\\nFROM events\\nWHERE \\n  event_type = 'authentication' \\n  AND timestamp > now() - interval '5 minutes'\\nGROUP BY source_ip\\nHAVING COUNT(*) > 3\",\"refId\":\"A\",\"sql\":{\"columns\":[{\"parameters\":[],\"type\":\"function\"}],\"groupBy\":[{\"property\":{\"type\":\"string\"},\"type\":\"groupBy\"}],\"limit\":50}}"
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

    no_data_state  = "NoData"
    exec_err_state = "Error"
    for            = "1m"
    annotations    = {}
    labels = {
      severity = "critical"
      type     = "bruteforce"
    }
    is_paused = false

    notification_settings {
      contact_point = "Honeypot Alerts"
    }
  }
}
