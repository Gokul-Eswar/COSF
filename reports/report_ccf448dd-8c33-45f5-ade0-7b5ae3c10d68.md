# Security Assessment Report: Mock Assessment

- **Execution ID:** ccf448dd-8c33-45f5-ade0-7b5ae3c10d68
- **Status:** completed
- **Started:** 2026-02-22 10:42:26.528121
- **Ended:** 2026-02-22 10:42:26.587959

## Task Summary

| Task Name | Adapter | Status | Duration |
|-----------|---------|--------|----------|
| Mock Step 1 | mock | completed | 0.010084s |
| Mock Step 2 | mock | completed | 0.006681s |

## Detailed Results

### Mock Step 1
#### Extracted Entities
```json
[
  {
    "id": "a8206fde-8688-4585-a3ad-7664ec861db7",
    "name": "mock-10.0.0.1",
    "ip_address": "10.0.0.1",
    "os": null,
    "tags": []
  },
  {
    "id": "dc4da2e9-6a22-4713-9d45-8efe3a535086",
    "asset_id": "a8206fde-8688-4585-a3ad-7664ec861db7",
    "port": 80,
    "protocol": "tcp",
    "name": "http",
    "state": "open"
  },
  {
    "id": "ce22e930-d6b3-42eb-b8a5-8e72a01fb35c",
    "asset_id": "a8206fde-8688-4585-a3ad-7664ec861db7",
    "cve_id": null,
    "severity": "high",
    "description": "Mock vulnerability",
    "remediation": null,
    "service_id": "dc4da2e9-6a22-4713-9d45-8efe3a535086"
  }
]
```

### Mock Step 2
#### Extracted Entities
```json
[
  {
    "id": "e38ce35d-45c3-478c-a7bd-11e23674c0c2",
    "name": "mock-10.0.0.2",
    "ip_address": "10.0.0.2",
    "os": null,
    "tags": []
  },
  {
    "id": "e1daed62-a75d-408e-a0be-0d07ec7bb738",
    "asset_id": "e38ce35d-45c3-478c-a7bd-11e23674c0c2",
    "port": 80,
    "protocol": "tcp",
    "name": "http",
    "state": "open"
  },
  {
    "id": "141e37f2-39b0-410f-be09-1d8843b3e9d8",
    "asset_id": "e38ce35d-45c3-478c-a7bd-11e23674c0c2",
    "cve_id": null,
    "severity": "high",
    "description": "Mock vulnerability",
    "remediation": null,
    "service_id": "e1daed62-a75d-408e-a0be-0d07ec7bb738"
  }
]
```

