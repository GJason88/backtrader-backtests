import pandas as pd
import matplotlib.pyplot as plt

# Plot optimization results

df = pd.read_csv('optimization.csv')

df.plot(x='BB_MA', y='End Value', kind='scatter')
plt.show()