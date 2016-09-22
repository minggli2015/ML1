import statsmodels.api as sm
import numpy as np
from sklearn import linear_model

__author__ = 'Ming Li @ London, UK'


def forward_select(data, target, alpha=0.05, display=True):

    """Linear model designed by forward selection.

    Parameters:
    -----------
    data : pandas DataFrame with all possible predictors and response w

    response: string, name of response column in data

    Returns:
    --------
    model: an "optimal" fitted statsmodels linear model
           with an intercept
           selected by forward selection
           evaluated by adjusted R-squared
    """

    remaining = set([i for i in data.columns if i not in target.columns])
    selected_var = []
    current_score, best_new_score = 0.0, 0.0

    print('beginning forward stepwise variable selection...\n')
    while remaining and current_score == best_new_score:

        scores_with_candidates = []  # containing variables

        for candidate in remaining:

            X = sm.add_constant(data[selected_var + [candidate]]) # inherit variables from last step and try new ones
            reg = sm.OLS(target, X).fit()
            score, p = reg.rsquared, reg.pvalues[-1]  # r2 (changeable) and two-tailed p value of the candidate
            scores_with_candidates.append((score, p, candidate))

        scores_with_candidates.sort(reverse=False)  # order variables by score in ascending
        disqualified_candidates = [i for i in scores_with_candidates if ~(i[1] < alpha)]
        scores_with_candidates = [i for i in scores_with_candidates if i[1] < alpha]
        try:
            best_new_score, best_candidate_p, best_candidate = scores_with_candidates.pop()
        except IndexError:  # when no candidate passes significance test at critical value
            disqualified_score, disqualified_p, disqualified_candidate = disqualified_candidates.pop(0)
            remaining.remove(disqualified_candidate)  # remove the worst disqualified candidate
#            print(disqualified_score, disqualified_p, disqualified_candidate)
            continue  # continuing the while loop
        if current_score < best_new_score:
            remaining.remove(best_candidate)
            current_score = best_new_score
            selected_var.append(best_candidate)
            if display:
                print(selected_var)

    model = sm.OLS(target, sm.add_constant(data[selected_var])).fit()

    print('forward stepwise selection completed...\n')

    return model, selected_var


def backward_select(data, target, alpha=0.05, display=True):
    """Linear model designed by backward selection.

    Parameters:
    -----------
    data : pandas DataFrame with all possible predictors and response w

    response: string, name of response column in data

    Returns:
    --------
    model: an "optimal" fitted statsmodels linear model
           with an intercept
           selected by forward selection
           evaluated by adjusted R-squared
    """

    selected_var = list(set([i for i in data.columns if i not in target.columns]))

    print('beginning backward stepwise variable selection...\n')
    while selected_var:
        if display:
            print(selected_var)

        scores_with_candidates = []  # containing variables

        X = sm.add_constant(data[selected_var])  # inherit variables from last step and try new ones
        reg = sm.OLS(target, X).fit()
        score = reg.rsquared  # r2 (changeable) and two-tailed p value of the candidate
        p = reg.pvalues[1:]  # first p value belongs to constant
        for i, var in enumerate(selected_var):
            scores_with_candidates.append((p[i], score,  var))
        scores_with_candidates.sort(reverse=False)  # order variables by p value in ascending order
        disqualified_candidates = [i for i in scores_with_candidates if ~(i[0] < alpha)]
        try:
            scores_with_candidates.remove(disqualified_candidates.pop())
            selected_var = [i[2] for i in scores_with_candidates]

        except IndexError:  # when no candidate fails the significance test at critical value
            selected_var = [i[2] for i in scores_with_candidates]
            break

    model = sm.OLS(target, sm.add_constant(data[selected_var])).fit()

    print('\nbackward stepwise selection completed...\n')

    return model, selected_var


def cost_function(params, x, y, model):

    J = 0
    m = len(x)
    # for i in range(m):
    #     h = np.sum(params.T * x[i])  # hypothesis linear regression with constant 1
    #     J += (h - y[i]) ** 2
    # J /= (2 * m)
    if isinstance(model, sm.OLS) or isinstance(model, linear_model.LinearRegression):
        h = np.dot(x, params.T)
        # GLM hypothesis in linear algebra representation
        J = (h - y) ** 2
        J /= (2 * m)
        return np.sum(J)

    if isinstance(model, linear_model.LogisticRegression):
        h = 1 / (1 + np.exp(-np.dot(x, params.T)))
        # logistic (sigmoid) model hypothesis
        J = -np.dot(np.log(h).T, y) - np.dot(np.log(1 - h).T, (1 - y))
        J /= m
        return np.sum(J)


def partial_derivative_cost(params, x, y, model):

    J = 0
    m = len(x)
    # for i in range(m):
    #     h = np.sum(params.T * x[i])
    #     J += (h - y[i]) * x[i][j]
    # J /= m

    if isinstance(model, sm.OLS) or isinstance(model, linear_model.LinearRegression):
        h = np.dot(x, params.T)
        # GLM hypothesis in linear algebra representation

    if isinstance(model, linear_model.LogisticRegression):
        h = 1 / (1 + np.exp(-np.dot(x, params.T)))
        # logistic (sigmoid) model hypothesis

    J = np.dot(x.T, (h - y)) / m
    # partial_derivative terms for either linear or logistic regression
    return J.T  # J is a n-dimensioned vector


def gradient_descent(params, x, y, model, alpha=.1, max_epochs=5000, conv_thres=.0001, display=False):

    count = 0  # initiating a count number so once reaching max iterations will terminate

    params = np.array(params)
    x = np.array(x)
    y = np.array(y)

    cost = cost_function(params, x, y, model)  # initial J(theta)

    prev_cost = cost + 10
    costs = [cost]
    thetas = [params]

    # beginning gradient_descent iterations

    if display:
        print('\nbeginning gradient decent algorithm...\n')

    while (np.abs(prev_cost - cost) > conv_thres) and (count <= max_epochs):

        prev_cost = cost

        # update = np.zeros(params.shape[0])
        #
        # for j in range(len(params)):
        #     update = partial_derivative_cost(params, j, x, y)  # gradient descend
        params -= alpha * partial_derivative_cost(params, x, y, model)  # gradient descend

        thetas.append(params)  # restoring historic parameters

        cost = cost_function(params, x, y, model)  # cost at each iteration
        costs.append(cost)
        count += 1

    return params, costs


