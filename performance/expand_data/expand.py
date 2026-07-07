import json
import os
import uuid
import copy
import random
import gc
from typing import Any, Dict, List

import numpy as np
from tqdm import tqdm


original_data_path = "db.json"

# ========= Configurable parameters =========
FACTOR = 1000                  # total scaling factor; 500 means the original plus 499x newly generated
SEED = 42
NUMERIC_NOISE_RATIO = 0.05    # numeric perturbation magnitude, 5%
CATEGORY_MUTATE_PROB = 0.03   # small probability of replacing a categorical field
OUTPUT_FILE = f"expanded_{FACTOR}.json"

# flush every this many records written, to limit buffer build-up
FLUSH_EVERY = 1000

# whether to emit more compact JSON to reduce file size
COMPACT_JSON = True

random.seed(SEED)
np.random.seed(SEED)


def load_original_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Read the original template data in one pass.
    Note: this still loads the entire original db.json into memory,
    but it no longer holds the newly generated 100 GB / 200 GB data in memory.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("The input db.json must be a top-level JSON array (list).")

    return data


def is_uuid_like(s: Any) -> bool:
    if not isinstance(s, str):
        return False
    try:
        uuid.UUID(s)
        return True
    except Exception:
        return False


def regenerate_ids(obj: Any):
    """
    Recursively rebuild every *_id field to avoid duplicate internal IDs.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("_id"):
                obj[k] = str(uuid.uuid4())
            else:
                regenerate_ids(v)
    elif isinstance(obj, list):
        for item in obj:
            regenerate_ids(item)


def collect_field_values(records: List[Dict[str, Any]], key: str) -> List[Any]:
    """
    Collect candidate categorical values for a top-level field, used for the
    low-probability category substitution. Only top-level scalar fields are
    handled here; nested structural fields are left untouched.
    """
    vals = []
    for r in records:
        if key in r and not isinstance(r[key], (dict, list)):
            vals.append(r[key])
    return vals


def build_top_level_category_pool(records: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """
    Build a candidate pool for top-level scalar categorical fields.
    """
    pool = {}
    candidate_keys = set()

    for r in records:
        for k, v in r.items():
            if not isinstance(v, (dict, list, int, float, bool)) and v is not None:
                candidate_keys.add(k)

    for k in candidate_keys:
        values = collect_field_values(records, k)
        uniq = list({v for v in values if v is not None})
        if len(uniq) > 1:
            pool[k] = uniq

    return pool


def perturb_numeric_value(key: str, value: Any) -> Any:
    """
    Apply a small perturbation to a numeric field, subject to sensible constraints.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return value

    if value is None:
        return value

    scale = max(abs(value) * NUMERIC_NOISE_RATIO, 1.0)
    new_value = value + np.random.normal(0, scale)

    key_lower = key.lower()

    if "percent" in key_lower:
        new_value = min(max(new_value, 0), 100)

    elif key_lower.startswith("days_to_") or key_lower in {"days_to_birth", "days_to_consent"}:
        if key_lower != "days_to_birth":
            new_value = max(new_value, 0)

    elif "age" in key_lower:
        new_value = max(new_value, 0)

    elif "year" in key_lower:
        new_value = round(new_value)
        new_value = min(max(new_value, 1900), 2100)

    elif value >= 0:
        new_value = max(new_value, 0)

    if isinstance(value, int) and not isinstance(value, bool):
        return int(round(new_value))
    else:
        return float(new_value)


def perturb_simple_fields(obj: Any, category_pool: Dict[str, List[Any]]):
    """
    Recursively perturb scalar fields:
    - numeric fields: small perturbation
    - top-level / local scalar string fields: low-probability substitution
    The list/dict structure itself is left unchanged.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith("_id"):
                continue

            if isinstance(v, (dict, list)):
                perturb_simple_fields(v, category_pool)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                obj[k] = perturb_numeric_value(k, v)
            elif isinstance(v, str):
                if is_uuid_like(v):
                    continue
                if "datetime" in k.lower():
                    continue
                if k in {"submitter_id"}:
                    continue

                if k in category_pool and random.random() < CATEGORY_MUTATE_PROB:
                    candidates = category_pool[k]
                    if len(candidates) > 1:
                        alt = random.choice(candidates)
                        if alt != v:
                            obj[k] = alt

    elif isinstance(obj, list):
        for item in obj:
            perturb_simple_fields(item, category_pool)


def synthetic_case_from_template(
    template: Dict[str, Any],
    category_pool: Dict[str, List[Any]]
) -> Dict[str, Any]:
    """
    Generate one new case using an original case as a template:
    1. deep-copy
    2. rebuild all *_id fields
    3. apply a small perturbation to numeric/scalar fields
    """
    new_case = copy.deepcopy(template)
    regenerate_ids(new_case)
    perturb_simple_fields(new_case, category_pool)
    return new_case


def json_dump_one_record(record: Dict[str, Any], fp):
    """
    Write a single record to the file.
    """
    if COMPACT_JSON:
        json.dump(record, fp, ensure_ascii=False, separators=(",", ":"))
    else:
        json.dump(record, fp, ensure_ascii=False)


def write_expanded_dataset_streaming(
    original_records: List[Dict[str, Any]],
    factor: int,
    output_file: str
):
    """
    Stream the full dataset to disk:
    - write the original data first
    - then generate and write the new data one record at a time
    Neither synthetic_records nor combined_data is kept in memory.
    """
    num_original = len(original_records)
    if num_original == 0:
        raise ValueError("The original data is empty; nothing to expand.")

    target_new = num_original * (factor - 1)
    total_to_write = num_original + target_new

    category_pool = build_top_level_category_pool(original_records)

    temp_output = output_file + ".tmp"

    written = 0
    first = True

    with open(temp_output, "w", encoding="utf-8") as f:
        f.write("[")

        with tqdm(total=total_to_write, desc="Writing dataset", mininterval=0.2) as pbar:
            # 1) write the original data first
            for record in original_records:
                if not first:
                    f.write(",")
                json_dump_one_record(record, f)
                first = False

                written += 1
                pbar.update(1)

                if written % FLUSH_EVERY == 0:
                    f.flush()

            # 2) then generate and write the rest as a stream
            for i in range(target_new):
                template = random.choice(original_records)
                new_case = synthetic_case_from_template(template, category_pool)

                if not first:
                    f.write(",")
                json_dump_one_record(new_case, f)
                first = False

                written += 1
                pbar.update(1)

                # periodically flush and drop the temporary object
                if written % FLUSH_EVERY == 0:
                    f.flush()

                del new_case

                # for very long runs, periodically nudge Python to collect garbage
                if i % 10000 == 0 and i > 0:
                    gc.collect()

        f.write("]")
        f.flush()
        os.fsync(f.fileno())

    os.replace(temp_output, output_file)


def main():
    print(f"Loading original data from: {original_data_path}")
    original_records = load_original_data(original_data_path)

    num_original_cases = len(original_records)
    print(f"Original number of cases: {num_original_cases}")
    print(f"Expansion factor: {FACTOR}")
    print(f"Target total cases: {num_original_cases * FACTOR}")

    write_expanded_dataset_streaming(
        original_records=original_records,
        factor=FACTOR,
        output_file=OUTPUT_FILE
    )

    print(f"Saved to {OUTPUT_FILE}")
    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"File size: {file_size / (1024 ** 3):.2f} GB")


if __name__ == "__main__":
    main()