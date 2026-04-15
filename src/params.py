# Toy ML-KEM parameters (very small)
N = 256        # polynomial degree
Q = 3329        # modulus
K = 2         # module dimension

ETA1 = 3
ETA2 = 2

DU = 10
DV = 4

# Derived sizes for toy encoding
# ByteEncode_d outputs (N * d) / 8 bytes
ENCODED_POLY_DU_BYTES = (N * DU) // 8
ENCODED_POLY_DV_BYTES = (N * DV) // 8

# Sizes for vectors/matrices
ENCODED_VEC_DU_BYTES = K * ENCODED_POLY_DU_BYTES
ENCODED_VEC_DV_BYTES = K * ENCODED_POLY_DV_BYTES