from mlkem import mlkem_keygen, mlkem_encaps, mlkem_decaps

ek, dk = mlkem_keygen()
c, K_enc = mlkem_encaps(ek)
K_dec = mlkem_decaps(dk, c)

print("K_enc:", K_enc.hex())
print("K_dec:", K_dec.hex())
print("match:", K_enc == K_dec)