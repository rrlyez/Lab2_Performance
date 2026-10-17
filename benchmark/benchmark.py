import argparse
import time

import pandas as pd
import xgboost as xgb

from sklearn import preprocessing
from sklearn import tree
from sklearn import ensemble
from sklearn import model_selection
from sklearn import metrics


def load_and_prepare_data(filepath):
    df = pd.read_csv(filepath)

    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    encoder = preprocessing.LabelEncoder()
    y = encoder.fit_transform(y)

    return X, y


def run_decision_tree(X_train, y_train, X_test, y_test):
    depths = range(1, 11)
    test_accuracies = []

    for depth in depths:
        model = tree.DecisionTreeClassifier(
            max_depth=depth,
            min_samples_leaf=0.01,
            random_state=67
        )

        model_selection.cross_val_score(
            model,
            X_train,
            y_train,
            cv=5
        )

        model.fit(X_train, y_train)

        accuracy = metrics.accuracy_score(
            y_test,
            model.predict(X_test)
        )

        test_accuracies.append(accuracy)

    optimal_depth = 6

    return optimal_depth, test_accuracies[optimal_depth - 1]


def run_random_forest(
    X_train,
    y_train,
    X_test,
    y_test,
    max_depth
):
    test_accuracies = []

    for n_estimators in range(1, 16):
        model = ensemble.RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=0.01,
            random_state=67,
            n_jobs=-1
        )

        model_selection.cross_val_score(
            model,
            X_train,
            y_train,
            cv=5
        )

        model.fit(X_train, y_train)

        accuracy = metrics.accuracy_score(
            y_test,
            model.predict(X_test)
        )

        test_accuracies.append(accuracy)

    optimal_estimators = 8

    return (
        optimal_estimators,
        test_accuracies[optimal_estimators - 1]
    )


def run_xgboost(
    X_train,
    y_train,
    X_test,
    y_test,
    n_estimators,
    max_depth
):
    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=0.1
    )

    model.fit(X_train, y_train)

    accuracy = metrics.accuracy_score(
        y_test,
        model.predict(X_test)
    )

    return accuracy


def run_benchmark():
    X, y = load_and_prepare_data("dry_beans.csv")

    X_train, X_test, y_train, y_test = (
        model_selection.train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=67,
            stratify=y
        )
    )

    optimal_depth, tree_accuracy = run_decision_tree(
        X_train,
        y_train,
        X_test,
        y_test
    )

    shallow_depth = optimal_depth - 2

    optimal_estimators, forest_accuracy = run_random_forest(
        X_train,
        y_train,
        X_test,
        y_test,
        shallow_depth
    )

    num_trees = 2 * optimal_estimators

    xgb_accuracy = run_xgboost(
        X_train,
        y_train,
        X_test,
        y_test,
        num_trees,
        shallow_depth
    )

    return (
        tree_accuracy,
        forest_accuracy,
        xgb_accuracy
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of benchmark repetitions"
    )

    args = parser.parse_args()

    start = time.perf_counter()

    for _ in range(args.repeat):
        tree_accuracy, forest_accuracy, xgb_accuracy = (
            run_benchmark()
        )

    end = time.perf_counter()

    print(f"Repetitions: {args.repeat}")

    print(
        f"Decision Tree Test Accuracy: "
        f"{tree_accuracy:.2%}"
    )

    print(
        f"Random Forest Test Accuracy: "
        f"{forest_accuracy:.2%}"
    )

    print(
        f"XGBoost Test Accuracy: "
        f"{xgb_accuracy:.2%}"
    )

    print(
        f"Python wall time: "
        f"{end - start:.4f} s"
    )


if __name__ == "__main__":
    main()