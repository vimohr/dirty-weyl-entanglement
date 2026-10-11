import numpy as np
import ctypes
import os
import time
import matplotlib.pyplot as plt
import h5py
from datetime import datetime

# Load the C++ shared library
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libtestvi_cpp.so')
lib = ctypes.CDLL(lib_path)

# Map the signature for compute_ent_half_filling
# void compute_ent_half_filling(int Ns, double* w_array, int num_w, double* output, bool obc_x, bool obc_y, bool obc_z)
lib.compute_ent_half_filling.argtypes = [
    ctypes.c_int,                          # Ns
    ctypes.POINTER(ctypes.c_double),       # w_array
    ctypes.c_int,                          # num_w
    ctypes.POINTER(ctypes.c_double),       # output
    ctypes.POINTER(ctypes.c_double),       # eigvals_out
    ctypes.c_bool,                         # obc_x
    ctypes.c_bool,                         # obc_y
    ctypes.c_bool                          # obc_z
]
lib.compute_ent_half_filling.restype = None

def run_half_filling(Ns=10, w_array=None, obc_x=True, obc_y=True, obc_z=True):
    if w_array is None:
        w_array = np.arange(0, 4.1, 0.2)
    
    w_array = np.ascontiguousarray(w_array, dtype=np.float64)
    num_w = len(w_array)
    
    # N is hardcoded to 10 in C++
    N = 10
    dim_half = N**3
    
    # Output arrays
    results = np.zeros((Ns, num_w), dtype=np.float64)
    eigvals = np.zeros((Ns, num_w, dim_half), dtype=np.float64)
    
    print(f"Calling C++ half-filling function (OBC: x={obc_x}, y={obc_y}, z={obc_z})...")
    
    lib.compute_ent_half_filling(
        ctypes.c_int(Ns),
        w_array.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_int(num_w),
        results.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        eigvals.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_bool(obc_x),
        ctypes.c_bool(obc_y),
        ctypes.c_bool(obc_z)
    )
    
    return results, eigvals

if __name__ == "__main__":
    Ns = 10000
    # w_vals = np.arange(0, 4.1, 0.2)
    # w_array = np.concatenate([np.array([0.0]), np.logspace(-3, 3, 37, base=2)])
    # w_array = np.arange(0, 8.2, 0.2)
    w_array = np.arange(3, 5.1, 0.1)
    # w_array = np.array([0.0])
    obc_x = False
    obc_y = False
    obc_z = False
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    start = time.time()
    # Example: OBC in x, PBC in y and z
    data, eigvals = run_half_filling(Ns=Ns, w_array=w_array, obc_x=obc_x, obc_y=obc_y, obc_z=obc_z)
    end = time.time()

    # Save results to HDF5
    filename = f"half_filling_data_{date_str}.h5"
    with h5py.File(filename, "w") as f:
        f.create_dataset("w_array", data=w_array)
        f.create_dataset("data", data=data)
        f.create_dataset("eigvals", data=eigvals)
        f.attrs["Ns"] = Ns
        f.attrs["obc_x"] = obc_x
        f.attrs["obc_y"] = obc_y
        f.attrs["obc_z"] = obc_z
        f.attrs["timestamp"] = time.ctime()
    print(f"Results saved to {filename}")
    
    print(f"Finished in {end - start:.2f} seconds.")

    shift = data[0, 0]
    shift = 0.0
    
    # Simple plot
    plt.figure(figsize=(10, 6))
    plt.plot(np.log2(w_array[1:]), data[:, 1:].T, ".", color="blue", alpha=0.1)
    plt.plot(np.log2(w_array[1:]), np.mean(data[:, 1:], axis=0), color="red", label="Mean Entropy")
    plt.xlabel("Disorder Strength (w)")
    plt.ylabel("Entropy at Half-Filling")
    plt.title(f"Entropy at Half-Filling vs Disorder (OBC-x:{obc_x}, OBC-y:{obc_y}, OBC-z:{obc_z})")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"half_filling_results_{date_str}.png")
    print(f"Plot saved to half_filling_results_{date_str}.png")
    # plt.show()
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(np.log2(w_array[1:]), np.gradient(np.log2(np.mean(data[:, 1:] - shift, axis=0)), np.log2(w_array[1:])), color="red", label="Mean Entropy")
    plt.xlabel("Disorder Strength (w)")
    plt.ylabel("Entropy at Half-Filling")
    plt.title(f"Entropy at Half-Filling vs Disorder (OBC-x:{obc_x}, OBC-y:{obc_y}, OBC-z:{obc_z})")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"half_filling_results_gradient_{date_str}.png")
    print(f"Plot saved to half_filling_results_gradient_{date_str}.png")
    # plt.show()
    plt.close()