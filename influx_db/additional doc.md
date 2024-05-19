# Query for grafana:
```
from(bucket: "orangepi")
  |> range(start: -1h) // Adjust the time range as needed
  |> filter(fn: (r) => r._measurement == "measurement1")
  |> filter(fn: (r) => r.tagname1 == "tagvalue1")
  |> filter(fn: (r) => r._field == "field1")
  |> yield(name: "mean") // Optional: Change to suit your needs, e.g., mean, sum, etc.
```


