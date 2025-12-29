import re

def extract_parameters(text):
    results = {}

    # Regex for number like 194, 161, 48, 131 etc.
    num = r'([\d.]+)'

    # Age
    age = re.search(r'Age\s*[: ]\s*(\d+)', text, re.IGNORECASE)
    if age:
        results["age"] = age.group(1)

    # Gender
    gender = re.search(r'\b(Male|Female)\b', text, re.IGNORECASE)
    if gender:
        results["gender"] = gender.group(1)

    # ---- Lipid profile ----

    # Total Cholesterol
    tc = re.search(r'Cholesterol Total\s+' + num, text, re.IGNORECASE)
    if tc:
        results["cholesterol_total"] = tc.group(1)

    # Triglycerides
    tg = re.search(r'Triglycerides\s+' + num, text, re.IGNORECASE)
    if tg:
        results["triglycerides"] = tg.group(1)

    # HDL
    hdl = re.search(r'HDL Cholesterol\s+' + num, text, re.IGNORECASE)
    if hdl:
        results["hdl"] = hdl.group(1)

    # LDL (Direct)
    ldl = re.search(r'LDL Cholesterol,?Direct\s+' + num, text, re.IGNORECASE)
    if ldl:
        results["ldl_direct"] = ldl.group(1)

    # VLDL
    vldl = re.search(r'VLDL Cholesterol\s+' + num, text, re.IGNORECASE)
    if vldl:
        results["vldl"] = vldl.group(1)

    # Non HDL
    nhdl = re.search(r'Non-HDL Cholesterol\s+' + num, text, re.IGNORECASE)
    if nhdl:
        results["non_hdl"] = nhdl.group(1)

    return results
