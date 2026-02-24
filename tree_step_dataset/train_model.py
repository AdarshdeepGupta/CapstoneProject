import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn.utils.rnn import pad_sequence
from model import Seq2Seq

# Load dataset
with open("dataset.json", "r") as f:
    data = json.load(f)

pairs = []
for item in data[:1000]:
    input_text = item["problem"]
    output_text = json.dumps(item["solution_tree"])
    pairs.append((input_text, output_text))

# Build vocabulary
all_text = "".join([inp + out for inp, out in pairs])
chars = sorted(list(set(all_text)))

special_tokens = ["<PAD>", "<START>", "<END>"]
stoi = {token: i for i, token in enumerate(special_tokens)}
index_offset = len(stoi)

for ch in chars:
    stoi[ch] = index_offset
    index_offset += 1

itos = {i: ch for ch, i in stoi.items()}
vocab_size = len(stoi)

def encode(text, add_special=False):
    tokens = []
    if add_special:
        tokens.append(stoi["<START>"])
    for ch in text:
        tokens.append(stoi[ch])
    if add_special:
        tokens.append(stoi["<END>"])
    return torch.tensor(tokens, dtype=torch.long)

# Encode dataset
inputs = []
targets = []

for inp, out in pairs:
    inputs.append(encode(inp))
    targets.append(encode(out, add_special=True))

inputs = pad_sequence(inputs, batch_first=True, padding_value=stoi["<PAD>"])
targets = pad_sequence(targets, batch_first=True, padding_value=stoi["<PAD>"])

model = Seq2Seq(vocab_size)
criterion = nn.CrossEntropyLoss(ignore_index=stoi["<PAD>"])
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Train longer
for epoch in range(50):
    optimizer.zero_grad()

    outputs = model(inputs, targets[:, :-1])

    loss = criterion(
        outputs.reshape(-1, vocab_size),
        targets[:, 1:].reshape(-1)
    )

    loss.backward()
    optimizer.step()

    print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

torch.save({
    "model_state": model.state_dict(),
    "stoi": stoi,
    "itos": itos
}, "tree_model.pth")

print("Model saved successfully.")