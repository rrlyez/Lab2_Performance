"""
In this lab, you will solve a classification problem using decision tree,
random forest, and (optionally) XGBoost. Ensemble methods over trees remain
one of the most powerful tools for tabular data.
"""

import collections

import dtreeviz
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb

from matplotlib import ticker
from sklearn import preprocessing, tree, ensemble, model_selection, metrics
from sklearn.inspection import PartialDependenceDisplay

# =============================================================================
# PART 1: Decision Trees
# =============================================================================
# A Decision Tree splits the data to maximize information gain. The default
# metric for classification is Gini impurity, defined as:
# $$G = \sum_{i=1}^{C} p_i (1 - p_i)$$
# where $p_i$ is the probability of an item belonging to class $i$.
# TODO: recall the definition of entropy and information gain from the lecture.
# How does it differ from Gini impurity?
# Entropy measures the uncertainty of class distribution:
# H = -sum(p_i * log2(p_i)).
# Information gain is the decrease in entropy after a split.
# Gini impurity also measures class impurity, but it does not use log.
# =============================================================================


def load_and_prepare_data(
    filepath: str,
) -> tuple[pd.DataFrame, pd.Series, preprocessing.LabelEncoder]:
    """Loads the dataset and separates features and target.

    Args:
        filepath: Path to the CSV dataset.

    Returns:
        A tuple containing the feature matrix X and the target vector y,
        along with the fitted LabelEncoder for the target.
    """
    df = pd.read_csv(filepath)
    X, y = df.iloc[:, :-1], df.iloc[:, -1]
    # We use LabelEncoder to convert string labels to integers (0 to C-1)
    # which is required by some frameworks like XGBoost.
    le = preprocessing.LabelEncoder()
    y = pd.Series(le.fit_transform(y))
    return X, y, le


def train_decision_tree(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    max_depth: int,
    min_samples_leaf: int | float = 0.01,
    random_state: int = 67,
) -> tuple[tree.DecisionTreeClassifier, np.ndarray[float]]:
    """Trains a single decision tree of limited depth
    and evaludates its cross-validation accuracy.

    Args:
        X_train: Training features.
        y_train: Training target.
        max_depth: Maximum depth of the tree.
        min_samples_leaf: Minimum number of samples required to be at a leaf node.
        random_state: Controls randomness to make the results reproducible.

    Returns:
        A tuple containing the trained model and 5-fold cross-validation scores.
    """
    # TODO: answer the following questions in the docstring:
    # 1. What is the meaning of min_samples_leaf?
    # 2. How does random state affect the model training?

    model = tree.DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
    )
    # TODO: compute cross validation scores with sklearn.
    cv_scores = model_selection.cross_val_score(
        model,
        X_train,
        y_train,
        cv=5
    )
    model.fit(X_train, y_train)
    return model, cv_scores


def evaluate_tree_depths(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    min_depth: int = 1,
    max_depth: int = 10,
) -> tuple[int, float]:
    """Evaluates different tree depths and plots the results.

    Args:
        X_train: Training features.
        y_train: Training target.
        X_test: Testing features.
        y_test: Testing target.
        min_depth: Minimum depth to evaluate.
        max_depth: Maximum depth to evaluate.

    Returns:
        The optimal depth and the corresponding test accuracy.
    """
    depths = list(range(min_depth, max_depth + 1))
    cv_means, cv_stds = [], []
    test_accuracies = []

    for depth in depths:
        model, cv_scores = train_decision_tree(X_train, y_train, depth)
        # TODO: compute the mean and std of the cross-validation scores.
        cv_means.append(cv_scores.mean())
        cv_stds.append(cv_scores.std())

        test_acc = metrics.accuracy_score(y_test, model.predict(X_test))
        test_accuracies.append(test_acc)

    plt.figure(figsize=(10, 6))
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(1.0))

    # Plot mean CV accuracy with a variance band (+/- 1 Std Dev)
    plt.plot(depths, cv_means, label="Mean CV Accuracy", marker="o")
    plt.fill_between(
        depths,
        np.array(cv_means) - np.array(cv_stds),
        np.array(cv_means) + np.array(cv_stds),
        alpha=0.2,
        label="CV ±1 Std Dev",
    )

    plt.plot(depths, test_accuracies, label="Test Accuracy", marker="s")

    plt.xlabel("Max Depth")
    plt.ylabel("Accuracy")
    plt.ylim(0.80, 1.00)
    plt.title("Decision Tree: Accuracy vs. Max Depth")
    plt.legend()
    plt.grid(True)
    plt.show()

    # TODO: Based on the plot, select the optimal max_depth.
    # Is the model overfitting at higher depths?
    # Optimal max_depth is 6.
    # At higher depths the accuracy does not improve significantly.
    optimal_depth = int(input("Based on the plot, what is the optimal depth? "))
    return optimal_depth, test_accuracies[depths.index(optimal_depth)]


# =============================================================================
# PART 2: Random Forests
# =============================================================================
# A random forest reduces the variance of single decision trees by averaging
# multiple trees grown on bootstrap samples (Bagging).
# $Var(\bar{X}) = \rho \sigma^2 + \frac{1-\rho}{B} \sigma^2$
# As the number of trees $B$ increases, the second term goes to 0.
# =============================================================================


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators: int,
    max_depth: int = 5,
    min_samples_leaf: int | float = 0.01,
    random_state: int = 67,
) -> tuple[ensemble.RandomForestClassifier, np.ndarray[float]]:
    """Trains a Random Forest and calculates its cross-validation accuracy.

    Args:
        X_train: Training features.
        y_train: Training target.
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of each tree.
        min_samples_leaf: Minimum number of samples required to be at a leaf node.
        random_state: Controls randomness to make the results reproducible.

    Returns:
        A tuple containing the trained model and 5-fold cross-validation scores.
    """
    # TODO: check out thte interface of sklearn.ensemble.RandomForestClassifier.
    model = ensemble.RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1
    )
    # TODO: what is the meaning of njobs? How does it affect the training?
    # n_jobs specifies how many CPU cores are used for training.
    # n_jobs=-1 uses all available cores and can speed up training.
    cv_scores = model_selection.cross_val_score(model, X_train, y_train, cv=5)
    model.fit(X_train, y_train)
    return model, cv_scores


def evaluate_forest_estimators(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    max_depth: int = 5,
    min_estimators: int = 1,
    max_estimators: int = 15,
) -> tuple[int, float]:
    """Evaluates different numbers of estimators for random forest.

    Args:
        X_train: Training features.
        y_train: Training target.
        X_test: Testing features.
        y_test: Testing target.
        max_depth: Maximum depth of each tree.
        min_estimators: Minimum number of estimators to evaluate.
        max_estimators: Maximum number of estimators to evaluate.

    Returns:
        The optimal number of estimators and the corresponding test accuracy.
    """
    estimators_list = list(range(min_estimators, max_estimators + 1))
    cv_means, cv_stds = [], []
    test_accuracies = []

    for n_est in estimators_list:
        model, cv_scores = train_random_forest(
            X_train, y_train, n_estimators=n_est, max_depth=max_depth
        )
        test_acc = metrics.accuracy_score(y_test, model.predict(X_test))
        cv_means.append(cv_scores.mean())
        cv_stds.append(cv_scores.std())
        test_accuracies.append(test_acc)

    plt.figure(figsize=(10, 6))
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(1.0))

    # Plot mean CV accuracy with a variance band (+/- 1 Std Dev)
    plt.plot(estimators_list, cv_means, label="Mean CV Accuracy", marker="o")
    plt.fill_between(
        estimators_list,
        np.array(cv_means) - np.array(cv_stds),
        np.array(cv_means) + np.array(cv_stds),
        alpha=0.2,
        label="CV ±1 Std Dev",
    )

    plt.plot(estimators_list, test_accuracies, label="Test Accuracy", marker="s")

    plt.xlabel("Number of Estimators")
    plt.ylabel("Accuracy")
    plt.ylim(0.80, 1.00)
    plt.title("Random Forest: Accuracy vs. Number of Estimators")
    plt.legend()
    plt.grid(True)
    plt.show()

    # TODO: Based on the plot, select the optimal number of estimators.
    # Is the model overfitting at higher numbers of estimators?
    # The optimal number of estimators is 8.
    # Increasing the number of estimators further does not improve test accuracy.
    optimal_estimators = int(
        input("Based on the plot, what is the optimal number of estimators? ")
    )
    return (
        optimal_estimators,
        test_accuracies[estimators_list.index(optimal_estimators)],
    )


# =============================================================================
# PART 3: Gradient Boosting (Optional)
# =============================================================================
# XGBoost uses an additive strategy. At step $t$, we add a tree $f_t$ that
# minimizes the objective:
# \[ Obj^{(t)} \approx \sum_{i=1}^n [g_i f_t(x_i)
# + \frac{1}{2} h_i f_t^2(x_i)] + \Omega(f_t) \]
# where $g_i$ and $h_i$ are first and second order gradients of the loss.
# =============================================================================


def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    n_estimators: int = 10,
    max_depth: int = 5,
) -> tuple:
    """Trains an XGBoost classifier and evaluates it.

    Args:
        X_train: Training features.
        y_train: Training target.
        X_test: Testing features.
        y_test: Testing target.

    Returns:
        A tuple containing the trained model and the test set accuracy.
    """
    model = xgb.XGBClassifier(
        n_estimators=n_estimators, max_depth=max_depth, learning_rate=0.1
    )
    model.fit(X_train, y_train)
    accuracy = metrics.accuracy_score(y_test, model.predict(X_test))
    return model, accuracy


if __name__ == "__main__":
    print(
        "In this lab, you will solve a classification problem using\n"
        "decision tree, random forest, and (optionally) XGBoost.\n"
        "I've provided some starter code, but you will need to completed TODOs."
    )
    try:
        X, y, le = load_and_prepare_data("dry_beans.csv")

        # TODO: Split the dataset into train and test with your favorite random.
        X_train, X_test, y_train, y_test = model_selection.train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=67,
            stratify=y
        )

        print("\n--- Part 1: Decision Tree ---")
        optimal_depth, tree_acc = evaluate_tree_depths(X_train, y_train, X_test, y_test)
        print(f"Decision Tree Test Accuracy: {tree_acc:.2%}")

        print("\n--- Part 2: Random Forest ---")
        print(f"In part 1 you chose the depth of {optimal_depth}.")
        print("Now we will train a random forest of slightly shallower trees.")
        shallow_depth = optimal_depth - 2
        optimal_estimators, forest_acc = evaluate_forest_estimators(
            X_train, y_train, X_test, y_test, max_depth=shallow_depth
        )
        print(f"Random Forest Test Accuracy: {forest_acc:.2%}")

        print("\n--- Part 3: XGBoost (Optional) ---")
        print(f"In part 2 you chose to use {optimal_estimators} trees.")
        print("Now we will train an XGBoost model of a couple more trees.")
        num_trees = 2 * optimal_estimators
        xgb_model, xgb_acc = train_xgboost(
            X_train,
            y_train,
            X_test,
            y_test,
            n_estimators=num_trees,
            max_depth=shallow_depth,
        )
        print(f"XGBoost Test Accuracy: {xgb_acc:.2%}")
        tree_index = int(input(f"Select a tree to visualize (0 to {num_trees - 1}): "))
        viz_model = dtreeviz.model(
            xgb_model,
            tree_index=tree_index,
            X_train=X_train,
            y_train=y_train,
            feature_names=list(X_train.columns),
            target_name="Class",
            class_names=le.classes_,
        )
        viz_model.view().show()
        # TODO(optional): Explore the other trees in the XGBoost model.
        for index in [0, num_trees // 2, num_trees - 1]:
            other_viz = dtreeviz.model(
                xgb_model,
                tree_index=index,
                X_train=X_train,
                y_train=y_train,
                feature_names=list(X_train.columns),
                target_name="Class",
                class_names=le.classes_,
            )
            other_viz.view().save(f"xgb_tree_{index}.svg")

        # TODO(optional): Explore other plots in dtreeviz,
        # such as feature importance and partial dependence plots.
        importances = xgb_model.feature_importances_
        indices = np.argsort(importances)[::-1]

        plt.figure(figsize=(10, 6))
        plt.bar(
            range(len(importances)),
            importances[indices]
        )

        plt.xticks(
            range(len(importances)),
            X_train.columns[indices],
            rotation=90
        )

        plt.xlabel("Features")
        plt.ylabel("Importance")
        plt.title("XGBoost Feature Importances")
        plt.tight_layout()
        plt.show()

        top_features = list(X_train.columns[indices[:2]])
        X_train_float = X_train.astype(float)

        PartialDependenceDisplay.from_estimator(
            xgb_model,
            X_train_float,
            features=top_features,
            target=0
        )

        plt.tight_layout()
        plt.show()

        # TODO(optional): Translate Turkish bean names.
        bean_names = {
            "BARBUNYA": "Cranberry bean",
            "BOMBAY": "Bombay bean",
            "CALI": "Cali bean",
            "DERMASON": "Dermason bean",
            "HOROZ": "Rooster bean",
            "SEKER": "Sugar bean",
            "SIRA": "Sira bean",
        }

        translated_class_names = [
            bean_names.get(str(name).upper(), str(name))
            for name in le.classes_
        ]
        print("\nTranslated class names:")
        for original, translated in zip(le.classes_, translated_class_names):
            print(f"{original}: {translated}")

    except FileNotFoundError:
        print(
            "Error: 'dry_beans.csv' not found. "
            "Please download the dataset and place it in the working directory."
        )
