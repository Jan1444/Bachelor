import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

X = 10*np.random.rand(5,3)

fig = plt.figure(figsize=(15,5),facecolor='w')
ax = fig.add_subplot(111)
ax.imshow(X, cmap=cm.jet)

plt.savefig("image.png",bbox_inches='tight',dpi=100)