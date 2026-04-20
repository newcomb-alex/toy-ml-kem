# Toy ML-KEM parameters (very small)
N = 16        # polynomial degree
Q = 97        # modulus
K = 2         # module dimension

ETA1 = 2
ETA2 = 2

DU = 4
DV = 4

# Derived sizes for toy encoding
# ByteEncode_d outputs (N * d) / 8 bytes
ENCODED_POLY_DU_BYTES = (N * DU) // 8
ENCODED_POLY_DV_BYTES = (N * DV) // 8

# Sizes for vectors/matrices
ENCODED_VEC_DU_BYTES = K * ENCODED_POLY_DU_BYTES
ENCODED_VEC_DV_BYTES = K * ENCODED_POLY_DV_BYTES