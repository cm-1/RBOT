# %%
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

def readIntoArr(fname):
    s = ''
    with open(fname, 'r') as f:
        s = f.readlines()
    return np.array([float(l.split(" ")[-1]) for l in s])

#%%
scores8 = readIntoArr("./8bg_results.txt")
scores32 = readIntoArr("./32bg_results.txt")


scores8m = np.concatenate((scores8, [scores8.mean()]))
scores32m = np.concatenate((scores32, [scores32.mean()]))
results = {"8GB": scores8m, "32GB": scores32m}

#%%
fig, ax = plt.subplots()
for i, (cat, scores) in enumerate(results.items()):
    offset = i * 0.4
    rects = ax.bar(np.arange(91) + offset, scores, 0.4, label=cat)

ax.legend()
plt.show()

#%%
fig, ax = plt.subplots()
lines = [
    ((x8, i), (x32, i)) for i, (x8, x32) in enumerate(zip(scores8m, scores32m))
]
lowlines_all = np.array([
    ((0.2, i), (min(x8, x32), i))
    for i, (x8, x32) in enumerate(zip(scores8m, scores32m))
])
worst_sel = np.array([(i % 18) == 11 for i in range(91)])
cat_sel = np.array([(i % 18) == 0 for i in range(91)])
rest_sel = ~(cat_sel & worst_sel)
ax.set_xlim(0.2, 1.0)
lc = LineCollection(lines, zorder=0, color="black")
ax.add_collection(lc)
lowlc = LineCollection(lowlines_all[rest_sel], zorder=0, linestyle="dotted", color="lightgrey")
lowlc2 = LineCollection(lowlines_all[worst_sel], zorder=0, linestyle="dashed", color="red")
lowlc3 = LineCollection(lowlines_all[cat_sel], zorder=0, linestyle="dotted", color="grey")
ax.add_collection(lowlc)
ax.add_collection(lowlc2)
ax.add_collection(lowlc3)
sizes = np.full(91, 11)
sizes[-1] *= 3
ax.scatter(scores8m, np.arange(91), label="8GB", s = sizes)
ax.scatter(scores32m, np.arange(91), label="32GB", s = sizes)
ax.legend()
smin = min(scores8.min(), scores32.min())
smax = max(scores8.max(), scores32.max())
# for i in range(1, 5):
#     x = (18 * i) - 0.5
    # ax.plot([x, x], [0.2, 1.0], linestyle='dashed', color="grey")
ax.set_yticks(18 * np.arange(6))
ax.set_yticks(np.arange(0, 90, 3), minor=True)
ax.set_yticklabels(["A", "B", "C", "D", "D*", "Avg"])
ax.set_xlabel("Success Ratio")
ax.set_ylabel("Video Sequence")
ax.set_title("Effects of Histogram Memory Usage on Tracking Success")
# plt.show()