# -*- coding: utf-8 -*-
"""LogisticRegression_NLI.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/15ak-1K9VGAtDioT4b1NPPpFUga0KNQry
"""

pip install datasets

import pickle
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# Save object to a pickle file
def save_object(obj, filename):
    with open(filename, 'wb') as file:
        pickle.dump(obj, file)

# Load object from a pickle file
def load_object(filename):
    with open(filename, 'rb') as file:
        return pickle.load(file)

# Function to preprocess data
def preprocess_data(data, dataset_choice):
    if dataset_choice == "sick":
        premises = data['sentence_A']
        hypotheses = data['sentence_B']
        labels = data['label']
    else:
        premises = data['premise']
        hypotheses = data['hypothesis']
        labels = data['label']

    texts = [f"{p} {h}" for p, h in zip(premises, hypotheses)]
    return texts, labels

# Train the logistic regression model
def train_model(train_texts, train_labels):
    vectorizer = TfidfVectorizer()
    train_features = vectorizer.fit_transform(train_texts)
    model = LogisticRegression(max_iter=10000)
    model.fit(train_features, train_labels)
    return vectorizer, model

# Evaluate the model
def evaluate_model(test_texts, test_labels, vectorizer, model):
    test_features = vectorizer.transform(test_texts)
    predictions = model.predict(test_features)

    accuracy = accuracy_score(test_labels, predictions)
    print(f"Test Accuracy: {accuracy:.4f}")
    print(classification_report(test_labels, predictions, target_names=['Entailment', 'Neutral', 'Contradiction']))

    cm = confusion_matrix(test_labels, predictions)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Entailment', 'Neutral', 'Contradiction'])
    disp.plot()
    plt.show()

# Main function to load data, train, and evaluate
def main():
    dataset_choice = input("Choose a dataset (snli, mnli, sick): ").strip().lower()
    datasets = {"snli": "snli", "mnli": "multi_nli", "sick": "sick"}

    if dataset_choice not in datasets:
        print("Invalid choice. Exiting.")
        return

    dataset = load_dataset(datasets[dataset_choice])

    # Adjust validation split for MNLI
    if dataset_choice == "mnli":
        val_split = input("Choose validation split (matched, mismatched): ").strip().lower()
        val_key = f"validation_{val_split}"
        if val_key not in dataset:
            print("Invalid validation split. Exiting.")
            return
    else:
        val_key = "validation"

    train_texts, train_labels = preprocess_data(dataset['train'], dataset_choice)
    test_texts, test_labels = preprocess_data(dataset[val_key], dataset_choice)

    vectorizer, model = train_model(train_texts, train_labels)
    evaluate_model(test_texts, test_labels, vectorizer, model)

if __name__ == '__main__':
    main()