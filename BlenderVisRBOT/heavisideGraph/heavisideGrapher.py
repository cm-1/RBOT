import numpy as np
import matplotlib.pyplot as plt

DEFAULT_S_VALUE =  1.2

def heaviside(x, s = DEFAULT_S_VALUE):
    return 1.0/np.pi*(-np.arctan(x*s)) + 0.5

def diracDelta(x, s = DEFAULT_S_VALUE):
    return (1.0 / np.pi) * (s/(x*s*s*x + 1.0))

# Matplotlib version 2.0 uses a new default math style that, IMO, looks bad.
# The following reverts to the older style.
# Solution comes from GitHub user "jdhao" on Matplotlib issue #7921,
# "Text rendered with MathText looks really ugly (version 2.0 vs. 1.5)"
# https://github.com/matplotlib/matplotlib/issues/7921/
# Accessed 2024-06-21.
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['mathtext.rm'] = 'serif'


x = np.linspace(-10, 10, 1000)
y_h = heaviside(x)
y_d = diracDelta(x)

fig = plt.figure()
ax = fig.add_subplot(1,1,1)

# Knowledge of how to use "spines" to achieve this comes from answers by
# users Jblasco (2414194/jblasco) and Karl der Kaefer (5770949/karl-der-kaefer)
# to StackOverflow question "How to draw axis in the middle of the figure?"
# https://stackoverflow.com/q/31556446

# Remove unused axes.
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Make each remaining spine pass through the zero of the other's axis.
ax.spines['bottom'].set_position('zero')
ax.spines['left'].set_position('zero')

ax.set_ylim(0.0,1.0)

ax.plot(x, y_h, "-b", label=r"$H_e(\Phi(\mathbf{x}))$")
ax.plot(x, y_d, color="orange", label=r"$\delta_e(\Phi(\mathbf{x}))$")

ax.set_xlabel(r"Value of $\Phi(\mathbf{x})$", fontsize=12)
ax.set_title(r"$H_e$ and $\delta_e$ for $s=" + str(DEFAULT_S_VALUE) + r"$", fontsize=12)

# Knowledge of how to change the font size (via the prop={"size": ...} argument)
# comes from an answer by user Yann (717357/yann) to the StackOverflow question
# "How to change legend fontsize with matplotlib.pyplot"
# https://stackoverflow.com/q/7125009
# There are apparently newer ways to do this, but I don't think the backwards
# compability hurts.
ax.legend(loc="upper right", prop={"size": 12})

plt.show() 
