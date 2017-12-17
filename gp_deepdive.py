import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from scipy.spatial.distance import cdist, pdist, squareform

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF

# np.random.seed(0)


def euclidean(Xa, Xb):
    """distance sparse matrix"""
    dist = cdist(Xa, Xb, metric='minkowski', p=2)
    return np.sqrt(np.sum(np.square(dist).diagonal()))


a = np.random.rand(3, 4)
b = np.random.normal(size=a.shape)

assert np.isclose(np.linalg.norm(a - b), euclidean(a, b))


def radial_basis_function(Xa, Xb=None, lengthscale=1):
    """Gaussian Kernel implemented using Eculidean matrix"""
    assert isinstance(Xa, np.ndarray)
    if Xb is None:
        Xb = Xa
    dist = cdist(Xa, Xb, metric='minkowski', p=2)
    return np.exp(- np.square(dist) / 2 / np.square(lengthscale))


a = np.random.rand(4, 8)
b = np.random.normal(size=(100, 8))

# assert np.allclose(radial_basis_function(a, b, lengthscale=1),
#                    rbf_kernel(a, b, gamma=.5))

assert np.allclose(cdist(a, a), squareform(pdist(a)))

# Gaussian Process Introduction

N = 100
epsilon = 1e-10
param = .5
X_test = np.linspace(-10, 10, N).reshape(-1, 1)

K_ss = radial_basis_function(X_test, lengthscale=param)
# in order to apply cholesky decomposition, K_ss must be a matrix:
# - positive definite i.e. x.H * M * x > 0 for any x in same shape in C;
# - symmetric, a especial case of Hermitian with only real values.
# add positive definite matrix to ensure positive definiteness of K_ss
K_ss += np.eye(N) * epsilon

# f ~ μ + L * N(0, I) represents functional form of Multivariate Gaussian
# where L.T * L = Σ the covariance matrix

L_ss = np.linalg.cholesky(K_ss)
# sample from multivariate Gaussian with random white gaussian.
# TODO shouldn't the gaussian be multivate with 0 mean and np.eye(N) sigma?
f_prior = 0 + np.dot(L_ss, np.random.normal(loc=0, size=(N, 3)))

# f_prior with shape (N, 3)
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, sharey=True)
ax1.plot(X_test, f_prior)
ax1.grid(True)

# new evidence
X_train = np.arange(-10, 10, 1).reshape(-1, 1)
bool_mask = np.random.choice(a=[True, False], size=len(X_train), p=[.5, .5])
X_train = X_train[bool_mask]
y_train = np.sin(X_train)


def polynomial(X, theta, p=2):
    """f(x) = ax**3 + bx**2 + cx + d"""
    m, n = X.shape
    theta = np.array(theta)
    assert theta.shape == (p + 1,)

    X_polynominal = np.zeros(shape=(m, p + 1))
    for order in range(0, p + 1):
        X_polynominal[:, order] = np.power(X, order).ravel()
    return np.dot(X_polynominal, theta)


# y_train = polynomial(X_train, theta=[1.2, 2.5], p=1)


n = X_train.shape[0]
K = radial_basis_function(X_train, lengthscale=param)
K += epsilon * np.eye(n)
L = np.linalg.cholesky(K)

# conditional probability of multivariate gaussian given f_prior
K_s = radial_basis_function(X_train, X_test, lengthscale=param)
L_s = np.linalg.solve(L, K_s)

assert np.allclose(np.dot(np.linalg.inv(L), K_s), np.linalg.solve(L, K_s))


# TODO !!! why lower triangular matrix L instead of whole kernel matrix?
# according to Ebden 2008:
# mu = K_s * inv(K) * y
# = L_s * L * inv(L * L.T) * y
# = L_s * (L * inv(L)) * inv(L.T) * y
# = L_s * I * (inv(L.T) * y)
mean = np.dot(L_s.T, np.dot(np.linalg.inv(L), y_train)).ravel()

assert np.allclose(np.dot(np.linalg.inv(L), y_train),
                   np.linalg.solve(L, y_train))

# sample from f ~ posterior given x_test, x_train, y_train points
# according to Ebden 2008:
# Σ = K_ss - K_s * inv(K) * K_s.T
# = K_ss - L_s * L * inv(L * L.T) * (L_s * L).T
# = K_ss - L_s * L * inv(L) * inv(L.T) * L_s.T * L.T
# = K_ss - L_s * I * I * L_s.T
# = K_ss - L_s * L_s.T
sigma = K_ss - np.dot(L_s.T, L_s)
L = np.linalg.cholesky(sigma)
f_posterior = mean.reshape(-1, 1) + \
              np.dot(L, np.random.normal(loc=0, size=(N, 3)))

# TODO how to find standard deviation of this posterier?
var = np.diag(K_ss) - np.sum(L_s**2, axis=0)
std = np.sqrt(var)

ax2.plot(X_train, y_train, 'bs', ms=5)
ax2.plot(X_test, f_posterior)
# 4 sigma confidence interval roughly 95%
ax2.fill_between(X_test.ravel(), mean-2*std, mean+2*std, color="#dddddd")
ax2.plot(X_test, mean, 'r--', lw=2)
ax2.grid(True)
fig.tight_layout()


gp = GaussianProcessRegressor(kernel=RBF(length_scale=param), alpha=epsilon)
gp.fit(X_train, y_train)
mu, std = gp.predict(X_test, return_std=True)

ax3.plot(X_train, y_train, 'bs', ms=5)
ax3.fill_between(X_test.ravel(), mu.ravel()-2*std, mu.ravel()+2*std)
ax3.plot(X_test, mu, 'r--', lw=2)
ax3.grid(True)
fig.tight_layout()
plt.show()
