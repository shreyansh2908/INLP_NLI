# -*- coding: utf-8 -*-
"""Transformers_MNLIsub.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1q6rCXpeq-f-4wCWCkBiKc_Fd05DalTZU
"""

import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from transformers import BertTokenizer, BertModel, BertForSequenceClassification, AdamW
from transformers.optimization import get_constant_schedule_with_warmup
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from tqdm import tqdm
import matplotlib.pyplot as plt
from datasets import load_dataset
from torch.utils.data import Dataset, DataLoader
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns

print("DONE!!!")

print("Datasets......\n1. SNLI \n2. MULTI-NLI\n3. SICK")
for i in range(3):
    dataset_choice = int(input("Enter choice :"))
    if dataset_choice == 1:
        dataset = load_dataset("snli")
        break
    elif dataset_choice == 2:
        dataset = load_dataset("multi_nli")
        break
    elif dataset_choice == 3:
        dataset =  load_dataset("sick")
        break
else:
    print("Invalid Choices Thrice....\nRun the program again")
    exit()

class NLIDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data.iloc[idx]
        return {
            'premise': item['premise'],
            'hypothesis': item['hypothesis'],
            'label': item['label']
        }

print("DONE!!!")

print(dataset_choice, end = "-")

if dataset_choice == 1:
    print("SNLI")
    dataset['train'] = dataset['train'].filter(lambda sen: sen['label'] != -1)
    dataset['validation'] = dataset['validation'].filter(lambda sen: sen['label'] != -1)
    dataset['test'] = dataset['test'].filter(lambda sen: sen['label'] != -1)
    train_data = dataset['train']
    test_data = dataset['test']
    validation_data = dataset['validation']

    train_dataset = pd.DataFrame({
        'sNo': range(len(train_data)),
        'premise': train_data['premise'],
        'hypothesis': train_data['hypothesis'],
        'label': train_data['label']
    })

    val_dataset = pd.DataFrame({
        'sNo': range(len(validation_data)),
        'premise': validation_data['premise'],
        'hypothesis': validation_data['hypothesis'],
        'label': validation_data['label']
    })

    test_dataset = pd.DataFrame({
        'sNo': range(len(test_data)),
        'premise': test_data['premise'],
        'hypothesis': test_data['hypothesis'],
        'label': test_data['label']
    })

elif dataset_choice == 2:
    print("MULTI-NLI")
    train_data = dataset['train']
    validation_data = dataset['validation_matched']
    test_data = dataset['validation_mismatched']

    train_dataset = pd.DataFrame({
        'sNo': range(len(train_data)),
        'premise': train_data['premise'],
        'hypothesis': train_data['hypothesis'],
        'label': train_data['label']
    })

    val_dataset = pd.DataFrame({
        'sNo': range(len(validation_data)),
        'premise': validation_data['premise'],
        'hypothesis': validation_data['hypothesis'],
        'label': validation_data['label']
    })

    test_dataset = pd.DataFrame({
        'sNo': range(len(test_data)),
        'premise': test_data['premise'],
        'hypothesis': test_data['hypothesis'],
        'label': test_data['label']
    })

elif dataset_choice == 3:
    print("SICK")
    train_data = dataset['train']
    validation_data = dataset['validation']
    test_data = dataset['test']

    train_dataset = pd.DataFrame({
        'sNo': range(len(train_data)),
        'premise': train_data['sentence_A'],
        'hypothesis': train_data['sentence_B'],
        'label': train_data['label']
    })

    val_dataset = pd.DataFrame({
        'sNo': range(len(validation_data)),
        'premise': validation_data['sentence_A'],
        'hypothesis': validation_data['sentence_B'],
        'label': validation_data['label']
    })

    test_dataset = pd.DataFrame({
        'sNo': range(len(test_data)),
        'premise': test_data['sentence_A'],
        'hypothesis': test_data['sentence_B'],
        'label': test_data['label']
    })

print("DONE!!!")

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model1 = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=3)
optimizer = AdamW(model1.parameters(), lr=1e-5)

print(dataset_choice)
# Datasets......
train_ds = NLIDataset(train_dataset[:50000])
val_ds = NLIDataset(val_dataset)
test_ds = NLIDataset(test_dataset)

# DataLoaders......
batch_size = 32
train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=batch_size)
test_loader = DataLoader(test_ds, batch_size=batch_size)
print(len(train_loader), len(val_loader), len(test_loader))
print("DONE!!!")

train_ds[1]

"""# **BERT**"""

from collections import Counter

label_counts = Counter(train_dataset['label'])

print("Count of unique labels:")
for label, count in label_counts.items():
    print(f"Label {label}: {count} samples")

print("Train Dataset Size:", len(train_dataset), len(train_ds))
print("Val Dataset Size:", len(val_dataset), len(val_ds))
print("Test Dataset Size:", len(test_dataset), len(test_ds))

print("Train DataLoader Size:", len(train_loader))
print("Val DataLoader Size:", len(val_loader))
print("Test DataLoader Size:", len(test_loader))

epochs = 3

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

model1.to(device)
all_preds1 = []

for epoch in range(epochs):
    print(epoch + 1, "Epoch.......")
    correct_predictions = 0
    total_predictions = 0
    for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}"):
        optimizer.zero_grad()
        inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt")
        inputs = {key: tensor.to(device) for key, tensor in inputs.items()}
        labels = batch['label'].to(device)

        outputs = model1(**inputs)
        logits = outputs.logits

        loss = F.cross_entropy(logits, labels)
        loss.backward()
        optimizer.step()

        predicted_labels = torch.argmax(logits, dim=1)
        correct_predictions += torch.sum(predicted_labels == labels).item()
        total_predictions += labels.size(0)

    train_accuracy = correct_predictions / total_predictions
    print("Train Accuracy:", train_accuracy)

    # Validation...
    model1.eval()
    val_labels = []
    val_preds = []
    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Validation"):
            inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt")
            inputs = {key: tensor.to(device) for key, tensor in inputs.items()}
            labels = batch['label'].to(device)
            outputs = model1(**inputs)
            val_labels.extend(labels.cpu().numpy())
            val_preds.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

    val_accuracy = accuracy_score(val_labels, val_preds)
    print("Validation Accuracy:", val_accuracy)

    test_labels = []
    test_preds2 = []
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Testing"):
            inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt")
            inputs = {key: tensor.to(device) for key, tensor in inputs.items()}
            labels = batch['label'].to(device)
            outputs = model1(**inputs)
            test_labels.extend(labels.cpu().numpy())
            test_preds2.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

    test_accuracy = accuracy_score(test_labels, test_preds2)
    all_preds1.append(test_preds2)
    print("Bert Test Accuracy:", test_accuracy)
    print()

# Testing.......
test_labels = []
test_preds1 = []
with torch.no_grad():
    for batch in tqdm(test_loader, desc="Testing"):
        inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt")
        inputs = {key: tensor.to(device) for key, tensor in inputs.items()}
        labels = batch['label'].to(device)
        outputs = model1(**inputs)
        test_labels.extend(labels.cpu().numpy())
        test_preds1.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

test_accuracy = accuracy_score(test_labels, test_preds1)
print("BERT Base Test Accuracy:", test_accuracy)

combined_preds = np.vstack(all_preds1)
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_accuracy = accuracy_score(test_labels, majority_vote)
print("BERT Avg Test Accuracy:", test_accuracy)

"""# **RoBERTa**"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import RobertaTokenizer, RobertaForSequenceClassification, AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm
from datasets import load_dataset
from sklearn.metrics import accuracy_score

tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
model2 = RobertaForSequenceClassification.from_pretrained("roberta-base", num_labels=3)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model2.to(device)

optimizer = AdamW(model2.parameters(), lr=1e-5)
all_preds2 = []

for epoch in range(epochs):
    print(epoch + 1, "Epoch.......")
    correct_predictions = 0
    total_predictions = 0
    for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}"):
        optimizer.zero_grad()
        inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt").to(device)
        labels = batch['label'].to(device)

        outputs = model2(**inputs)
        logits = outputs.logits

        loss = F.cross_entropy(logits, labels)
        loss.backward()
        optimizer.step()

        predicted_labels = torch.argmax(logits, dim=1)
        correct_predictions += torch.sum(predicted_labels == labels).item()
        total_predictions += labels.size(0)

    train_accuracy = correct_predictions / total_predictions
    print("Train Accuracy:", train_accuracy)

    # Validation
    model2.eval()
    val_labels = []
    val_preds = []
    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Validation"):
            inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt").to(device)
            labels = batch['label'].to(device)
            outputs = model2(**inputs)
            val_labels.extend(labels.cpu().numpy())
            val_preds.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

    val_accuracy = accuracy_score(val_labels, val_preds)
    print("Validation Accuracy:", val_accuracy)

    test_labels = []
    test_preds2 = []
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Testing"):
            inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt")
            inputs = {key: tensor.to(device) for key, tensor in inputs.items()}
            labels = batch['label'].to(device)
            outputs = model2(**inputs)
            test_labels.extend(labels.cpu().numpy())
            test_preds2.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

    test_accuracy = accuracy_score(test_labels, test_preds2)
    all_preds2.append(test_preds2)
    print("Roberta Test Accuracy:", test_accuracy)
    print()

# Testing.......
test_labels = []
test_preds2 = []
with torch.no_grad():
    for batch in tqdm(test_loader, desc="Testing"):
        inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt")
        inputs = {key: tensor.to(device) for key, tensor in inputs.items()}
        labels = batch['label'].to(device)
        outputs = model2(**inputs)
        test_labels.extend(labels.cpu().numpy())
        test_preds2.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

test_accuracy = accuracy_score(test_labels, test_preds2)
print("Roberta Test Accuracy:", test_accuracy)

combined_preds = np.vstack(all_preds2)
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_accuracy = accuracy_score(test_labels, majority_vote)
print("Roberta Avg Test Accuracy:", test_accuracy)

"""# **ALBERT**"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AlbertTokenizer, AlbertForSequenceClassification, AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm
from datasets import load_dataset
from sklearn.metrics import accuracy_score

tokenizer = AlbertTokenizer.from_pretrained('albert-base-v2')
model3 = AlbertForSequenceClassification.from_pretrained("albert-base-v2", num_labels=3)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model3.to(device)

optimizer = AdamW(model3.parameters(), lr=1e-5)
all_preds3 = []

for epoch in range(epochs):
    print(epoch + 1, "Epoch.......")
    correct_predictions = 0
    total_predictions = 0
    for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}"):
        optimizer.zero_grad()
        inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt").to(device)
        labels = batch['label'].to(device)

        outputs = model3(**inputs)
        logits = outputs.logits

        loss = F.cross_entropy(logits, labels)
        loss.backward()
        optimizer.step()

        predicted_labels = torch.argmax(logits, dim=1)
        correct_predictions += torch.sum(predicted_labels == labels).item()
        total_predictions += labels.size(0)

    train_accuracy = correct_predictions / total_predictions
    print("Train Accuracy:", train_accuracy)

    # Validation
    model3.eval()
    val_labels = []
    val_preds = []
    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Validation"):
            inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt").to(device)
            labels = batch['label'].to(device)
            outputs = model3(**inputs)
            val_labels.extend(labels.cpu().numpy())
            val_preds.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

    val_accuracy = accuracy_score(val_labels, val_preds)
    print("Validation Accuracy:", val_accuracy)

    test_labels = []
    test_preds2 = []
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Testing"):
            inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt")
            inputs = {key: tensor.to(device) for key, tensor in inputs.items()}
            labels = batch['label'].to(device)
            outputs = model3(**inputs)
            test_labels.extend(labels.cpu().numpy())
            test_preds2.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

    test_accuracy = accuracy_score(test_labels, test_preds2)
    all_preds3.append(test_preds2)
    print("Alberta Test Accuracy:", test_accuracy)
    print()

# Testing.......
test_labels = []
test_preds3 = []
with torch.no_grad():
    for batch in tqdm(test_loader, desc="Testing"):
        inputs = tokenizer(batch['premise'], batch['hypothesis'], padding=True, truncation=True, return_tensors="pt")
        inputs = {key: tensor.to(device) for key, tensor in inputs.items()}
        labels = batch['label'].to(device)
        outputs = model3(**inputs)
        test_labels.extend(labels.cpu().numpy())
        test_preds3.extend(outputs.logits.argmax(dim=-1).cpu().numpy())

test_accuracy = accuracy_score(test_labels, test_preds3)
print("Alberta Test Accuracy:", test_accuracy)

combined_preds = np.vstack(all_preds3)
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_accuracy = accuracy_score(test_labels, majority_vote)
print("Alberta Avg Test Accuracy:", test_accuracy)

"""# **Results**"""

print("Bert + Roberta + Alberta")
combined_preds = np.vstack([all_preds1[:-1], all_preds2[:-1], all_preds3[:-1]])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble Test Accuracy :", test_accuracy)

combined_preds = np.vstack([all_preds1, all_preds2, all_preds3])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble + Average Test Accuracy :", test_accuracy)

print("Roberta + Alberta")
combined_preds = np.vstack([all_preds2[:-1], all_preds3[:-1]])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble Test Accuracy :", test_accuracy)

combined_preds = np.vstack([all_preds2, all_preds3])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble + Average Test Accuracy :", test_accuracy)

print("Bert + Roberta")
combined_preds = np.vstack([all_preds1[:-1], all_preds2[:-1]])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble Test Accuracy :", test_accuracy)

combined_preds = np.vstack([all_preds1, all_preds2])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble + Average Test Accuracy :", test_accuracy)

print("Bert + Alberta")
combined_preds = np.vstack([all_preds1[:-1], all_preds3[:-1]])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble Test Accuracy :", test_accuracy)

combined_preds = np.vstack([all_preds1, all_preds3])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble + Average Test Accuracy :", test_accuracy)

"""# **Ensemble**"""

from sklearn.metrics import accuracy_score, f1_score, recall_score, confusion_matrix

print("Bert + Roberta + Alberta")
combined_preds = np.vstack([all_preds1[:-1], all_preds2[:-1], all_preds3[:-1]])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

# Accuracy
test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble Test Accuracy : {:.2f}%".format(test_accuracy * 100))

# F1 Score
f1 = f1_score(test_labels, test_preds, average='weighted')
print("Ensemble F1 Score : {:.2f}%".format(f1 * 100))

# Recall
recall = recall_score(test_labels, test_preds, average='weighted')
print("Ensemble Recall Score : {:.2f}%".format(recall * 100))

# Classification Report
print("Classification Report:")
print(classification_report(test_labels, test_preds))

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='YlGnBu', xticklabels=np.unique(test_labels), yticklabels=np.unique(test_labels))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

print("Roberta + Alberta")
combined_preds = np.vstack([all_preds2[:-1], all_preds3[:-1]])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

# Accuracy
test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble Test Accuracy : {:.2f}%".format(test_accuracy * 100))

# F1 Score
f1 = f1_score(test_labels, test_preds, average='weighted')
print("Ensemble F1 Score : {:.2f}%".format(f1 * 100))

# Recall
recall = recall_score(test_labels, test_preds, average='weighted')
print("Ensemble Recall Score : {:.2f}%".format(recall * 100))

# Classification Report
print("Classification Report:")
print(classification_report(test_labels, test_preds))

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='YlGnBu', xticklabels=np.unique(test_labels), yticklabels=np.unique(test_labels))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

print("Bert + Roberta")
combined_preds = np.vstack([all_preds1[:-1], all_preds2[:-1]])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

# Accuracy
test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble Test Accuracy : {:.2f}%".format(test_accuracy * 100))

# F1 Score
f1 = f1_score(test_labels, test_preds, average='weighted')
print("Ensemble F1 Score : {:.2f}%".format(f1 * 100))

# Recall
recall = recall_score(test_labels, test_preds, average='weighted')
print("Ensemble Recall Score : {:.2f}%".format(recall * 100))

# Classification Report
print("Classification Report:")
print(classification_report(test_labels, test_preds))

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='YlGnBu', xticklabels=np.unique(test_labels), yticklabels=np.unique(test_labels))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

print("Bert + Alberta")
combined_preds = np.vstack([all_preds1[:-1], all_preds3[:-1]])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

# Accuracy
test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble Test Accuracy : {:.2f}%".format(test_accuracy * 100))

# F1 Score
f1 = f1_score(test_labels, test_preds, average='weighted')
print("Ensemble F1 Score : {:.2f}%".format(f1 * 100))

# Recall
recall = recall_score(test_labels, test_preds, average='weighted')
print("Ensemble Recall Score : {:.2f}%".format(recall * 100))

# Classification Report
print("Classification Report:")
print(classification_report(test_labels, test_preds))

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='YlGnBu', xticklabels=np.unique(test_labels), yticklabels=np.unique(test_labels))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

"""# **Ensemble + Avg**"""

print("Bert + Roberta + Alberta")
combined_preds = np.vstack([all_preds1, all_preds2, all_preds3])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

# Accuracy
test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble + Average Test Accuracy : {:.2f}%".format(test_accuracy * 100))

# F1 Score
f1 = f1_score(test_labels, test_preds, average='weighted')
print("Ensemble + Average F1 Score : {:.2f}%".format(f1 * 100))

# Recall
recall = recall_score(test_labels, test_preds, average='weighted')
print("Ensemble + Average Recall Score : {:.2f}%".format(recall * 100))

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='YlGnBu', xticklabels=np.unique(test_labels), yticklabels=np.unique(test_labels))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

print("Roberta + Alberta")
combined_preds = np.vstack([all_preds2, all_preds3])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

# Accuracy
test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble + Average Test Accuracy : {:.2f}%".format(test_accuracy * 100))

# F1 Score
f1 = f1_score(test_labels, test_preds, average='weighted')
print("Ensemble + Average F1 Score : {:.2f}%".format(f1 * 100))

# Recall
recall = recall_score(test_labels, test_preds, average='weighted')
print("Ensemble + Average Recall Score : {:.2f}%".format(recall * 100))

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='YlGnBu', xticklabels=np.unique(test_labels), yticklabels=np.unique(test_labels))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

print("Bert + Roberta")
combined_preds = np.vstack([all_preds1, all_preds2])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

# Accuracy
test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble + Average Test Accuracy : {:.2f}%".format(test_accuracy * 100))

# F1 Score
f1 = f1_score(test_labels, test_preds, average='weighted')
print("Ensemble + Average F1 Score : {:.2f}%".format(f1 * 100))

# Recall
recall = recall_score(test_labels, test_preds, average='weighted')
print("Ensemble + Average Recall Score : {:.2f}%".format(recall * 100))

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='YlGnBu', xticklabels=np.unique(test_labels), yticklabels=np.unique(test_labels))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

print("Bert + Alberta")
combined_preds = np.vstack([all_preds1, all_preds3])
majority_vote = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=combined_preds)
test_preds = majority_vote.tolist()

# Accuracy
test_accuracy = accuracy_score(test_labels, test_preds)
print("Ensemble + Average Test Accuracy : {:.2f}%".format(test_accuracy * 100))

# F1 Score
f1 = f1_score(test_labels, test_preds, average='weighted')
print("Ensemble + Average F1 Score : {:.2f}%".format(f1 * 100))

# Recall
recall = recall_score(test_labels, test_preds, average='weighted')
print("Ensemble + Average Recall Score : {:.2f}%".format(recall * 100))

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_preds)
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='YlGnBu', xticklabels=np.unique(test_labels), yticklabels=np.unique(test_labels))
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

torch.save(model1, "BERT.pth")
torch.save(model2, "ROBERTA.pth")
torch.save(model3, "ALBERTA.pth")

torch.save(model1, "BERT_final.pth")
torch.save(model2, "ROBERTA_final.pth")
torch.save(model3, "ALBERTA_final.pth")

torch.save(model1.state_dict(), 'model1_state_dict.pth')