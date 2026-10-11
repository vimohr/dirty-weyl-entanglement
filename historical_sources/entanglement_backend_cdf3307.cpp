#include <Eigen/Dense>
#include <vector>
#include <cmath>
#include <complex>
#include <random>
#include <omp.h>
#include <iostream>
#include <atomic>

using namespace Eigen;
using namespace std;

void print_progress(int current, int total) {
    int barWidth = 50;
    float progress = (float)current / total;
    std::cout << "[";
    int pos = barWidth * progress;
    for (int i = 0; i < barWidth; ++i) {
        if (i < pos) std::cout << "=";
        else if (i == pos) std::cout << ">";
        else std::cout << " ";
    }
    std::cout << "] " << int(progress * 100.0) << " % (" << current << "/" << total << ")\r";
    std::cout.flush();
}

MatrixXcd kron(const MatrixXcd& A, const MatrixXcd& B) {
    MatrixXcd C(A.rows() * B.rows(), A.cols() * B.cols());
    for (int i = 0; i < A.rows(); ++i) {
        for (int j = 0; j < A.cols(); ++j) {
            C.block(i * B.rows(), j * B.cols(), B.rows(), B.cols()) = A(i, j) * B;
        }
    }
    return C;
}

extern "C" {
    void compute_ent_diffs(int Ns, double* w_array, int num_w, double* output, double* eigvals_out, bool obc_x, bool obc_y, bool obc_z) {
        int N = 10;
        int dim = 2 * N * N * N;
        MatrixXcd H = MatrixXcd::Zero(dim, dim);
        MatrixXcd X(2, 2), Y(2, 2), Z(2, 2);
        X << 0, 1, 1, 0;
        Y << 0, complex<double>(0, -1), complex<double>(0, 1), 0;
        Z << 1, 0, 0, -1;

        double t = 1.0, t_z = -1.0, m_z = 0.0, t_0 = 1.0;

        for (int z = 0; z < N; ++z) {
            for (int y = 0; y < N; ++y) {
                for (int x = 0; x < N; ++x) {
                    MatrixXcd submatrix = t * sin(2 * M_PI * x / N) * X 
                                        + t * sin(2 * M_PI * y / N) * Y 
                                        + (t_z * cos(2 * M_PI * z / N) - m_z + t_0 * (2 - cos(2 * M_PI * x / N) - cos(2 * M_PI * y / N))) * Z;
                    int idx = x + N * (y + N * z);
                    H.block(2 * idx, 2 * idx, 2, 2) = submatrix;
                }
            }
        }

        MatrixXcd T(N, N);
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                T(i, j) = exp(complex<double>(0, -2.0 * M_PI * i * j / N)) / sqrt((double)N);
            }
        }

        MatrixXcd I_2 = MatrixXcd::Identity(2, 2);
        MatrixXcd F_kron = kron(T, T);
        F_kron = kron(F_kron, T);
        F_kron = kron(F_kron, I_2);

        MatrixXcd H_new = F_kron.adjoint() * H * F_kron;

        // Boundary Conditions
        for (int s = 0; s < 2; ++s) {
            for (int x = 0; x < N; ++x) {
                for (int y = 0; y < N; ++y) {
                    for (int z = 0; z < N; ++z) {
                        int i = s + 2 * (x + N * (y + N * z));

                        if (obc_x && x == N - 1) {
                            int j1 = (s + 1) % 2 + 2 * (0 + N * (y + N * z));
                            H_new(i, j1) -= complex<double>(0, -t / 2.0);
                            H_new(j1, i) -= complex<double>(0, t / 2.0);

                            int j2 = s + 2 * (0 + N * (y + N * z));
                            double s_sign = (s == 0) ? 1.0 : -1.0;
                            H_new(i, j2) -= -t_0 / 2.0 * s_sign;
                            H_new(j2, i) -= -t_0 / 2.0 * s_sign;
                        }

                        if (obc_y && y == N - 1) {
                            int j1 = (s + 1) % 2 + 2 * (x + N * (0 + N * z));
                            double s_sign = (s == 0) ? 1.0 : -1.0;
                            H_new(i, j1) -= -t / 2.0 * s_sign;
                            H_new(j1, i) -= -t / 2.0 * s_sign;

                            int j2 = s + 2 * (x + N * (0 + N * z));
                            H_new(i, j2) -= -t_0 / 2.0 * s_sign;
                            H_new(j2, i) -= -t_0 / 2.0 * s_sign;
                        }

                        if (obc_z && z == N - 1) {
                            int j1 = s + 2 * (x + N * (y + N * 0));
                            double s_sign = (s == 0) ? 1.0 : -1.0;
                            H_new(i, j1) -= t_z / 2.0 * s_sign;
                            H_new(j1, i) -= t_z / 2.0 * s_sign;
                        }
                    }
                }
            }
        }

        // Pre-compute disorder to allow parallelizing over both loops
//        std::vector<std::vector<double>> all_disorder(Ns, std::vector<double>(dim / 2));
//        for (int n = 0; n < Ns; ++n) {
//            std::mt19937 gen(1337 + n);
//            std::uniform_real_distribution<double> dist(-0.5, 0.5);
//            for (int i = 0; i < dim / 2; ++i) {
//                all_disorder[n][i] = dist(gen);
//            }
//        }
        int total_tasks = Ns * num_w;
        std::atomic<int> progress_counter(0);

        #pragma omp parallel for collapse(2) schedule(dynamic)
        for (int n = 0; n < Ns; ++n) {
            for (int j = 0; j < num_w; ++j) {
                // Thread-local RNG for thread safety
                static thread_local std::mt19937 thread_gen(1337 + omp_get_thread_num());
                std::uniform_real_distribution<double> dist(-0.5, 0.5);

                double w = w_array[j];

                MatrixXcd H_curr = H_new;
                for (int k = 0; k < dim / 2; ++k) {
                    double disorder_base = dist(thread_gen);
                    H_curr(2 * k, 2 * k) += w * disorder_base;
                    H_curr(2 * k + 1, 2 * k + 1) += w * disorder_base;
                }

                SelfAdjointEigenSolver<MatrixXcd> solver(H_curr);
                //std::cout << solver.eigenvalues() << "\n";
                MatrixXcd V = solver.eigenvectors();

                std::vector<int> subset;
                for (int q = 0; q < dim; ++q) {
                    int x = (q / 2) % N;
                    int y = (q / (2 * N)) % N;
                    if ((x==N/2-2 || x==N/2-1 || x==N/2 || x==N/2+1) && (y==N/2-2 || y==N/2-1 || y==N/2 || y==N/2+1)){
                        subset.push_back(q);
                    }
                }

                MatrixXcd V_new1(subset.size(), dim / 2 + 1);
                MatrixXcd V_new0(subset.size(), dim / 2);

                for (size_t r = 0; r < subset.size(); ++r) {
                    for (int c = 0; c < dim / 2 + 1; ++c) {
                        V_new1(r, c) = V(subset[r], c);
                        if (c < dim / 2) {
                            V_new0(r, c) = V(subset[r], c);
                        }
                    }
                }

                MatrixXcd rho0 = V_new0.adjoint() * V_new0;
                MatrixXcd rho1 = V_new1.adjoint() * V_new1;

                SelfAdjointEigenSolver<MatrixXcd> solver0(rho0);
                SelfAdjointEigenSolver<MatrixXcd> solver1(rho1);

                auto eigvals0 = solver0.eigenvalues();
                auto eigvals1 = solver1.eigenvalues();

                //std::cout << eigvals0 << "\n";
                //std::cout << eigvals1 << "\n";

                double S0 = 0.0;
                for (int i = 0; i < eigvals0.size(); ++i) {
                    double p = eigvals0(i);
                    if (p > 1e-10 && p < 1.0 - 1e-10) {
                        S0 -= (p * std::log2(p) + (1 - p) * std::log2(1 - p));
                    }
                }

                double S1 = 0.0;
                for (int i = 0; i < eigvals1.size(); ++i) {
                    double p = eigvals1(i);
                    if (p > 1e-10 && p < 1.0 - 1e-10) {
                        S1 -= (p * std::log2(p) + (1 - p) * std::log2(1 - p));
                    }
                }

                output[n * num_w + j] = S1 - S0;
                for (int i = 0; i < eigvals0.size(); ++i) {
                    eigvals_out[(n * num_w + j) * (dim / 2) + i] = eigvals0(i);
                }

                int current = ++progress_counter;
                if (current % std::max(1, total_tasks / 200) == 0 || current == total_tasks) {
                    #pragma omp critical
                    {
                        print_progress(current, total_tasks);
                    }
                }
            }
        }
        std::cout << std::endl;
    }

    void compute_ent_half_filling(int Ns, double* w_array, double* mz_array, int num_w, double* output, double* eigvals_out, bool obc_x, bool obc_y, bool obc_z) {
        int N = 10;
        int dim = 2 * N * N * N;
        MatrixXcd H = MatrixXcd::Zero(dim, dim);
        MatrixXcd X(2, 2), Y(2, 2), Z(2, 2);
        X << 0, 1, 1, 0;
        Y << 0, complex<double>(0, -1), complex<double>(0, 1), 0;
        Z << 1, 0, 0, -1;

        // H_new is built at m_z = 0. The per-iteration correction
        // H_new(m_z) = H_new(0) - m_z*(I⊗Z) is applied cheaply inside the loop.
        double t = 1.0, t_z = -1.0, t_0 = 1.0;

        for (int z = 0; z < N; ++z) {
            for (int y = 0; y < N; ++y) {
                for (int x = 0; x < N; ++x) {
                    MatrixXcd submatrix = t * sin(2 * M_PI * x / N) * X
                                        + t * sin(2 * M_PI * y / N) * Y
                                        + (t_z * cos(2 * M_PI * z / N) + t_0 * (2 - cos(2 * M_PI * x / N) - cos(2 * M_PI * y / N))) * Z;
                    int idx = x + N * (y + N * z);
                    H.block(2 * idx, 2 * idx, 2, 2) = submatrix;
                }
            }
        }

        MatrixXcd T(N, N);
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                T(i, j) = exp(complex<double>(0, -2.0 * M_PI * i * j / N)) / sqrt((double)N);
            }
        }

        MatrixXcd I_2 = MatrixXcd::Identity(2, 2);
        MatrixXcd F_kron = kron(T, T);
        F_kron = kron(F_kron, T);
        F_kron = kron(F_kron, I_2);

        MatrixXcd H_new = F_kron.adjoint() * H * F_kron;

        // Boundary Conditions
        for (int s = 0; s < 2; ++s) {
            for (int x = 0; x < N; ++x) {
                for (int y = 0; y < N; ++y) {
                    for (int z = 0; z < N; ++z) {
                        int i = s + 2 * (x + N * (y + N * z));

                        if (obc_x && x == N - 1) {
                            int j1 = (s + 1) % 2 + 2 * (0 + N * (y + N * z));
                            H_new(i, j1) -= complex<double>(0, -t / 2.0);
                            H_new(j1, i) -= complex<double>(0, t / 2.0);

                            int j2 = s + 2 * (0 + N * (y + N * z));
                            double s_sign = (s == 0) ? 1.0 : -1.0;
                            H_new(i, j2) -= -t_0 / 2.0 * s_sign;
                            H_new(j2, i) -= -t_0 / 2.0 * s_sign;
                        }

                        if (obc_y && y == N - 1) {
                            int j1 = (s + 1) % 2 + 2 * (x + N * (0 + N * z));
                            double s_sign = (s == 0) ? 1.0 : -1.0;
                            H_new(i, j1) -= -t / 2.0 * s_sign;
                            H_new(j1, i) -= -t / 2.0 * s_sign;

                            int j2 = s + 2 * (x + N * (0 + N * z));
                            H_new(i, j2) -= -t_0 / 2.0 * s_sign;
                            H_new(j2, i) -= -t_0 / 2.0 * s_sign;
                        }

                        if (obc_z && z == N - 1) {
                            int j1 = s + 2 * (x + N * (y + N * 0));
                            double s_sign = (s == 0) ? 1.0 : -1.0;
                            H_new(i, j1) -= t_z / 2.0 * s_sign;
                            H_new(j1, i) -= t_z / 2.0 * s_sign;
                        }
                    }
                }
            }
        }

        int total_tasks = Ns * num_w;
        std::atomic<int> progress_counter(0);

        #pragma omp parallel for collapse(2) schedule(dynamic)
        for (int n = 0; n < Ns; ++n) {
            for (int j = 0; j < num_w; ++j) {
                // Thread-local RNG for thread safety
                static thread_local std::mt19937 thread_gen(1337 + omp_get_thread_num());
                std::uniform_real_distribution<double> dist(-0.5, 0.5);

                double w  = w_array[j];
                double mz = mz_array[j];

                // H_new(m_z) = H_new(0) - m_z*(I⊗Z): diagonal correction, spin-up gets -mz, spin-down gets +mz
                MatrixXcd H_curr = H_new;
                for (int k = 0; k < dim / 2; ++k) {
                    double disorder_base = dist(thread_gen);
                    H_curr(2 * k,     2 * k)     += -mz + w * disorder_base;
                    H_curr(2 * k + 1, 2 * k + 1) +=  mz + w * disorder_base;
                }

                SelfAdjointEigenSolver<MatrixXcd> solver(H_curr);
                MatrixXcd V = solver.eigenvectors();

                std::vector<int> subset;
                for (int q = 0; q < dim; ++q) {
                    int x = (q / 2) % N;
                    int y = (q / (2 * N)) % N;
                    if (x < N/2){
                        subset.push_back(q);
                    }
                    //if ((x==N/2-2 || x==N/2-1 || x==N/2 || x==N/2+1) && (y==N/2-2 || y==N/2-1 || y==N/2 || y==N/2+1)){
                    //    subset.push_back(q);
                    //}
                }

                MatrixXcd V_new0(subset.size(), dim / 2);

                for (size_t r = 0; r < subset.size(); ++r) {
                    for (int c = 0; c < dim / 2; ++c) {
                        V_new0(r, c) = V(subset[r], c);
                    }
                }

                MatrixXcd rho0 = V_new0.adjoint() * V_new0;
                SelfAdjointEigenSolver<MatrixXcd> solver0(rho0);
                auto eigvals0 = solver0.eigenvalues();

                double S0 = 0.0;
                for (int i = 0; i < eigvals0.size(); ++i) {
                    double p = eigvals0(i);
                    if (p > 1e-10 && p < 1.0 - 1e-10) {
                        S0 -= (p * std::log2(p) + (1 - p) * std::log2(1 - p));
                    }
                }

                output[n * num_w + j] = S0;
                for (int i = 0; i < eigvals0.size(); ++i) {
                    eigvals_out[(n * num_w + j) * (dim / 2) + i] = eigvals0(i);
                }

                int current = ++progress_counter;
                if (current % std::max(1, total_tasks / 200) == 0 || current == total_tasks) {
                    #pragma omp critical
                    {
                        print_progress(current, total_tasks);
                    }
                }
            }
        }
        std::cout << std::endl;
    }
}

