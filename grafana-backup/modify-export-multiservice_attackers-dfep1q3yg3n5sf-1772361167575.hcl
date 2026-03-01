resource "grafana_rule_group" "rule_group_970fd60641c2fd14" {
  org_id           = 1
  name             = "multiservice_attackers"
  folder_uid       = "efep1htutc35sf"
  interval_seconds = 600

  rule {
    name      = "Attack Pattern Detection"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "dfeotjrrru2o0b"
      model          = "{\"dataset\":\"sentinel\",\"editorMode\":\"code\",\"format\":\"table\",\"intervalMs\":1000,\"maxDataPoints\":43200,\"rawQuery\":true,\"rawSql\":\"SELECT COUNT(DISTINCT source_ip) as multi_service_attackers\\nFROM events\\nWHERE \\n  timestamp > NOW() - INTERVAL '10 minutes'\\nGROUP BY source_ip\\nHAVING COUNT(DISTINCT sensor_type) > 2\",\"refId\":\"A\",\"sql\":{\"columns\":[{\"parameters\":[],\"type\":\"function\"}],\"groupBy\":[{\"property\":{\"type\":\"string\"},\"type\":\"groupBy\"}],\"limit\":50}}"
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
    for            = "10m"
    annotations    = {}
    labels = {
      alert_type = "coordinated_attack"
      team       = "security"
    }
    is_paused = false

    notification_settings {
      contact_point = "Honeypot Alerts"
    }
  }
}
