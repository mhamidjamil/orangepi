# Quires for grafana

## Query for test output:
```
from(bucket: "orangepi")
  |> range(start: -1h) // Adjust the time range as needed
  |> filter(fn: (r) => r._measurement == "measurement1")
  |> filter(fn: (r) => r.tagname1 == "tagvalue1")
  |> filter(fn: (r) => r._field == "field1")
  |> yield(name: "mean") // Optional: Change to suit your needs, e.g., mean, sum, etc.
```

## Query for CPU temperatures:
```
from(bucket: "orangepi")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "temperature")
  |> filter(fn: (r) => r._field == "average_temp" or r._field == "max_temp")
  |> aggregateWindow(every: 2m, fn: mean)
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "average_temp", "max_temp"])
```

## Query for room temperature and humidity:
```
from(bucket: "orangepi")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "environment")
  |> filter(fn: (r) => r._field == "temperature" or r._field == "humidity")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "temperature", "humidity"])
```
