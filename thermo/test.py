# %%
import schedule
import time

def next_level():
    print(next(levels))
    return levels

levels = iter([5, 4, 2, 1, 0, 3])
schedule.every(10).seconds.do(next_level)

while True:
    schedule.run_pending()
    time.sleep(1)
# %%
