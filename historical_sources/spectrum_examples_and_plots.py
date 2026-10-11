import numpy as np
import h5py
import matplotlib.pyplot as plt

with h5py.File('half_filling_results/half_filling_data_20260519_134201.h5', 'r') as f:
    print(f.keys())
    # print(f['mz_array'][:])
    print(f['w_array'][:])
    eigvals = f['eigvals'][:]
    data = f['eigvals'][:]
    w_array = f['w_array'][:]
    print(data.shape)

print(eigvals.shape)

special1 = eigvals[0, 0]
special2 = eigvals[0, 10]
color1 = '#000000'
color2 = '#FB1A18'
# First plot (full range)
plt.plot(special1, '.', color=color1, label=r'w=0.0')
plt.plot(special2, '.', color=color2, label=r'w=2.0')
plt.yticks([0.5])
plt.legend(loc='upper left')
plt.savefig('entanglement_spectrum_1c_full.pdf', bbox_inches='tight')
plt.show()
plt.close()

# Second plot (zoomed in)
plt.plot(special1, '.', color=color1, label=r'w=0.0')
plt.plot(special2, '.', color=color2, label=r'w=2.0')
plt.xlim(485.5, 514.5)
plt.ylim(0.2, 0.8)
plt.yticks([0.5])
plt.legend(loc='upper left')
plt.savefig('entanglement_spectrum_1c_zoomed.pdf', bbox_inches='tight')
plt.show()
plt.close()

# Save relevant data
print(np.concatenate([special1[None, :], special2[None, :]], axis=0).shape)
with h5py.File('entanglement_spectrum_1c.h5', 'w') as f:
    f.create_dataset('eigvals', data=np.concatenate([special1[None, :], special2[None, :]], axis=0))
    f.create_dataset('w_array', data=np.array([0.0, 2.0]))