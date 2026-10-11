import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import h5py
from itertools import product

N = 60
L = 3*[N]
N_tot = np.prod(L)
t = 1.0
t_z = -1.0
m_z = 0.0
t_0 = 1.0
w = 0.0
disorder_type = "uniform"
Ns = 100

"""X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = np.zeros((L[2]*L[1], 2*L[0], 2*L[0]), dtype=complex)

for z in range(L[2]):
    for y in range(L[1]):
        for x in range(L[0]):
            submatrix = t*np.sin(2*np.pi*x/L[0])*X + t*np.sin(2*np.pi*y/L[1])*Y + (t_z*np.cos(2*np.pi*z/L[2]) - m_z + t_0*(2-np.cos(2*np.pi*x/L[0])-np.cos(2*np.pi*y/L[1])))*Z
            H[np.array([[y+L[1]*z, y+L[1]*z], [y+L[1]*z, y+L[1]*z]]), np.array([[0, 0], [1, 1]])+2*x, np.array([[0, 1], [0, 1]])+2*x] = submatrix

def transformation_matrix(N):
    transformation_matrix = np.zeros((N, N), dtype=complex)
    for i in range(N):
        for j in range(N):
            transformation_matrix[i, j] = np.exp(-2j*np.pi*i*j/N)/np.sqrt(N)
    return transformation_matrix
print("is unitary:", np.allclose(transformation_matrix(L[2])@transformation_matrix(L[2]).conj().T, np.eye(L[2]), atol=1e-10))
# H_new = H
transform = np.kron(transformation_matrix(L[0]), np.eye(2, dtype=complex))
for z in range(L[2]):
    for y in range(L[1]):
        H[y+L[1]*z, :, :] = transform.conj().T @ H[y+L[1]*z, :, :] @ transform

E, V = np.linalg.eigh(H)
V_new = V[:, :L[0], :][:, :, :L[0]]
C = np.einsum("ijk, imk->ijm", V_new.conj(), V_new)
eigvals, eigvecs = np.linalg.eigh(C)"""

with h5py.File('entanglment_spectrum_1b.h5', 'r') as f:
    eigvals = f['eigvals'][:]


def remove_approx_duplicate_points(points, tol=1e-3):
    """
    Remove approximately duplicate points from an array of (x, y) pairs.

    Parameters
    ----------
    points : array-like, shape (N, 2)
        Array of [x, y] points.
    tol : float
        Tolerance — points within this distance (in each dimension)
        are considered duplicates. Adjust based on your data's scale.

    Returns
    -------
    np.ndarray, shape (M, 2)
        Approximately unique points, in original order.
    """
    points = np.asarray(points, dtype=float)
    rounded = np.round(points / tol) * tol
    _, idx = np.unique(rounded, axis=0, return_index=True)
    return points[np.sort(idx)]

new_eigvals = np.roll(eigvals.reshape(L[2], -1), L[2]//2, axis=0)

new_values = [remove_approx_duplicate_points(new_eigvals[i]) for i in range(L[2])]

color = '#000000'

print("eigvals:", eigvals.shape)
for i in range(L[2]):
    print(new_values[i].shape)
    plt.plot(i*np.ones_like(new_values[i]), new_values[i], ".", color=color)
plt.xlabel(r"$k_z$")
plt.ylabel("Entanglement Spectrum")
plt.yticks([0.0, 0.5, 1.0])
plt.xticks([0, L[2]//2], [r"$-\pi$", "0"])
plt.gca().tick_params(axis='both', length=0)
plt.savefig('entanglement_spectrum_1b.pdf', bbox_inches='tight')
plt.show()
# with h5py.File('entanglment_spectrum_1b.h5', 'w') as f:
#     f.create_dataset('eigvals', data=eigvals)
