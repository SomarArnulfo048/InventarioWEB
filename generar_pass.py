from werkzeug.security import generate_password_hash

# CAMBIA ESTO POR TU CONTRASEÑA REAL
mi_password_real = "" 

hash_seguro = generate_password_hash(mi_password_real)
print(f"\nCOPIA ESTE CÓDIGO A TU BASE DE DATOS:\n{hash_seguro}\n")