// Derived from historical_sources/entanglement_backend_working_tree.cpp; see docs/provenance.md.
// The model and half-filling cut are unchanged. The task RNG is now explicit.
#include <Eigen/Dense>
#include <omp.h>
#include <atomic>
#include <cmath>
#include <complex>
#include <cstdint>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Eigen::MatrixXcd;
using Eigen::SelfAdjointEigenSolver;
using Complex = std::complex<double>;

namespace {
thread_local std::string last_error;

MatrixXcd kron(const MatrixXcd& a, const MatrixXcd& b) {
    MatrixXcd result(a.rows() * b.rows(), a.cols() * b.cols());
    for (int i = 0; i < a.rows(); ++i)
        for (int j = 0; j < a.cols(); ++j)
            result.block(i * b.rows(), j * b.cols(), b.rows(), b.cols()) = a(i, j) * b;
    return result;
}

struct Model {
    int size, sites;
    MatrixXcd clean;
    std::vector<int> keep;
    std::vector<std::mt19937> legacy_generators;
    std::uint64_t legacy_seed = 0;

    explicit Model(int l) : size(l), sites(l * l * l) {
        if (l < 2 || l % 2) throw std::invalid_argument("L must be even and at least 2");
        const double pi = std::acos(-1.0);
        const int dim = 2 * sites;
        MatrixXcd x(2, 2), y(2, 2), z(2, 2);
        x << 0, 1, 1, 0;
        y << 0, Complex(0, -1), Complex(0, 1), 0;
        z << 1, 0, 0, -1;
        MatrixXcd momentum = MatrixXcd::Zero(dim, dim);
        for (int iz = 0; iz < l; ++iz)
            for (int iy = 0; iy < l; ++iy)
                for (int ix = 0; ix < l; ++ix) {
                    double kx = 2 * pi * ix / l, ky = 2 * pi * iy / l, kz = 2 * pi * iz / l;
                    int index = 2 * (ix + l * (iy + l * iz));
                    momentum.block(index, index, 2, 2) =
                        std::sin(kx) * x + std::sin(ky) * y
                        + (-std::cos(kz) + (2 - std::cos(kx) - std::cos(ky))) * z;
                }
        MatrixXcd dft(l, l);
        for (int i = 0; i < l; ++i)
            for (int j = 0; j < l; ++j)
                dft(i, j) = std::exp(Complex(0, -2 * pi * i * j / l)) / std::sqrt(double(l));
        MatrixXcd transform = kron(kron(kron(dft, dft), dft), MatrixXcd::Identity(2, 2));
        clean = transform.adjoint() * momentum * transform;
        for (int q = 0; q < dim; ++q)
            if ((q / 2) % l < l / 2) keep.push_back(q);
    }
};
}

extern "C" {
int spectrum_backend_api() { return 1; }

const char* spectrum_last_error() { return last_error.c_str(); }

void* spectrum_create_model(int l) {
    try {
        // Only parallelize independent realizations, not each Eigen product.
        Eigen::setNbThreads(1);
        last_error.clear();
        return new Model(l);
    } catch (const std::exception& error) {
        last_error = error.what();
        return nullptr;
    }
}

void spectrum_destroy_model(void* pointer) { delete static_cast<Model*>(pointer); }

int spectrum_compute_batch(void* pointer, int first, int count,
                           const double* disorders, const double* masses, int parameters,
                           std::uint64_t seed, int legacy_rng, int threads,
                           double* entropy, double* occupations) {
    try {
        if (!pointer || first < 0 || count < 1 || parameters < 1 || threads < 1)
            throw std::invalid_argument("Invalid batch arguments");
        auto& model = *static_cast<Model*>(pointer);
        if (legacy_rng && model.legacy_generators.empty()) {
            model.legacy_seed = seed;
            for (int thread = 0; thread < threads; ++thread)
                model.legacy_generators.emplace_back(static_cast<std::uint32_t>(seed + thread));
        }
        if (legacy_rng && (int(model.legacy_generators.size()) != threads || model.legacy_seed != seed))
            throw std::invalid_argument("Legacy RNG seed and thread count must stay fixed between batches");
        std::atomic<bool> failed(false);
        const int tasks = count * parameters;
        #pragma omp parallel num_threads(threads)
        {
            std::uniform_real_distribution<double> uniform(-0.5, 0.5);
            #pragma omp for schedule(dynamic)
            for (int task = 0; task < tasks; ++task) {
                if (failed.load()) continue;
                try {
                    int realization = first + task / parameters;
                    int parameter = task % parameters;
                    std::seed_seq task_seed{
                        static_cast<std::uint32_t>(seed),
                        static_cast<std::uint32_t>(seed >> 32),
                        static_cast<std::uint32_t>(realization),
                        static_cast<std::uint32_t>(parameter)
                    };
                    std::mt19937 task_generator(task_seed);
                    auto& rng = legacy_rng ? model.legacy_generators[omp_get_thread_num()]
                                          : task_generator;
                    MatrixXcd h = model.clean;
                    for (int site = 0; site < model.sites; ++site) {
                        double disorder = disorders[parameter] * uniform(rng);
                        h(2 * site, 2 * site) += -masses[parameter] + disorder;
                        h(2 * site + 1, 2 * site + 1) += masses[parameter] + disorder;
                    }
                    SelfAdjointEigenSolver<MatrixXcd> solver(h);
                    if (solver.info() != Eigen::Success) throw std::runtime_error("Hamiltonian solver failed");
                    MatrixXcd restricted(model.sites, model.sites);
                    for (int row = 0; row < model.sites; ++row)
                        restricted.row(row) = solver.eigenvectors().row(model.keep[row]).head(model.sites);
                    MatrixXcd correlation = restricted.adjoint() * restricted;
                    SelfAdjointEigenSolver<MatrixXcd> es(correlation, Eigen::EigenvaluesOnly);
                    if (es.info() != Eigen::Success) throw std::runtime_error("Correlation solver failed");
                    double s = 0;
                    for (int mode = 0; mode < model.sites; ++mode) {
                        double p = es.eigenvalues()(mode);
                        occupations[static_cast<std::size_t>(task) * model.sites + mode] = p;
                        if (p > 1e-10 && p < 1 - 1e-10)
                            s -= p * std::log2(p) + (1 - p) * std::log2(1 - p);
                    }
                    entropy[task] = s;
                } catch (const std::exception&) {
                    failed.store(true);
                }
            }
        }
        if (failed) throw std::runtime_error("A batch task failed during diagonalization or allocation");
        last_error.clear();
        return 0;
    } catch (const std::exception& error) {
        last_error = error.what();
        return -1;
    }
}
}
