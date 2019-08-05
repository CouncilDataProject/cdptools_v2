**To generate the Legistar test data run the following commands:**

```python
from cdptools.legistar_utils import events
from datetime import datetime
day_of = datetime(target_year, target_month, target_day)
day_after = datetime(target_year, target_month, target_day + 1)
x = events.get_legistar_events_for_timespan("seattle", day_of, day_after, True)
```
