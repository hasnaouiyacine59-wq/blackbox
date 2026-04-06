ck_1="f1kfE3Klm9VROBifvqhfI7iAy7L08NcJPLO11BnQ8Ucla4cl"
ck_2 = "YpCVNxUPiDYBMvmyFamfb3U7bbR7sc8NX4YnxajEraU9diqw"
ck_3 = "ia3ouJUA8jBsYKsk4lJBsiTto4NfZhnTbeAhyvfVS-9ImgJq"
ck_4 = "l5vQGCsyYnB2xE6Ff5rO707OCv0mb9NsGCgY32mvFMrm31U-"

_ck_map = {1: ck_1, 2: ck_2, 3: ck_3, 4: ck_4}

def get_ck(n: int) -> str:
    if n not in _ck_map:
        raise ValueError(f"n must be 1–4, got {n}")
    return _ck_map[n]
