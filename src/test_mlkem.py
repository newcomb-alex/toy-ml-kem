from mlkem import mlkem_keygen, mlkem_encaps, mlkem_decaps

NUM_TRIALS = 50
successes = 0

for i in range(1, NUM_TRIALS + 1):
    ek, dk = mlkem_keygen()
    c, K_enc = mlkem_encaps(ek)
    K_dec = mlkem_decaps(dk, c)

    match = (K_enc == K_dec)
    if match:
        successes += 1

    print(f"Run {i}/{NUM_TRIALS}")
    print("K_enc:", K_enc.hex())
    print("K_dec:", K_dec.hex())
    print("match:", match)
    print("-" * 40)

success_rate = successes / NUM_TRIALS
print(f"Successful decapsulations: {successes}/{NUM_TRIALS}")
print(f"Success rate: {success_rate:.4f} ({success_rate * 100:.2f}%)")