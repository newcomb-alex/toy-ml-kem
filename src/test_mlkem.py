import time
from mlkem import mlkem_keygen, mlkem_encaps, mlkem_decaps

NUM_TRIALS = 1
successes = 0

start_time = time.perf_counter()

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

end_time = time.perf_counter()
elapsed = end_time - start_time

success_rate = successes / NUM_TRIALS
print(f"Successful decapsulations: {successes}/{NUM_TRIALS}")
print(f"Success rate: {success_rate:.4f} ({success_rate * 100:.2f}%)")
print(f"Total runtime: {elapsed:.6f} seconds")
print(f"Average runtime per trial: {elapsed / NUM_TRIALS:.6f} seconds")