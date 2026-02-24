import torch
from model import Seq2Seq

# Load saved model and vocab
checkpoint = torch.load("tree_model.pth")
stoi = checkpoint["stoi"]
itos = checkpoint["itos"]
vocab_size = len(stoi)

def encode(text):
    return torch.tensor([stoi.get(ch, 0) for ch in text], dtype=torch.long)

def decode(indices):
    return "".join([itos.get(i, "") for i in indices])

model = Seq2Seq(vocab_size)
model.load_state_dict(checkpoint["model_state"])
model.eval()

test_equation = "3x + 7 = 22"
src = encode(test_equation).unsqueeze(0)

hidden, cell = model.encoder(src)

input_token = torch.tensor([[stoi["<START>"]]])

generated = []
max_len = 400

with torch.no_grad():
    for _ in range(max_len):
        output, hidden, cell = model.decoder(input_token, hidden, cell)
        pred_token = torch.argmax(output[:, -1, :], dim=-1)

        token_id = pred_token.item()

        if token_id == stoi["<END>"]:
            break

        generated.append(token_id)
        input_token = pred_token.unsqueeze(0)

decoded_output = decode(generated)

print("Input:", test_equation)
print("\nGenerated Output:\n")
print(decoded_output)